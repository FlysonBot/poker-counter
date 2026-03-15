"""
主控窗口。显示开关和退出按钮，管理记牌器窗口和后端线程的生命周期。
"""

import tkinter as tk

from loguru import logger

from config import GUI
from tracker import Counter, Tracker
from card_types import WindowsType
from ui.counter_window import CounterWindow, _calculate_offset


class MasterWindow(tk.Tk):
    """顶级窗口：开关按钮 + 退出按钮。"""

    def __init__(self) -> None:
        super().__init__()
        self._counter = Counter()
        self._tracker = Tracker(
            self._counter,
            on_update=self._on_card_played,
            mark_potential_bombs=self._mark_potential_bombs,
        )
        self._windows: list[CounterWindow] = []

        config = GUI.get("SWITCH", {})
        font_size = config.get("FONT_SIZE", 12)

        self.title("记牌器开关")
        self.attributes("-topmost", True)  # 窗口始终置于最顶层
        self.overrideredirect(True)  # 去掉系统标题栏和边框
        self.configure(bg="white")
        self.attributes(
            "-transparentcolor", "white"
        )  # 白色背景变透明，实现异形窗口效果

        # 开关按钮：打开/关闭记牌器，text 和 command 会在开关时动态切换
        self._btn_switch = tk.Button(
            self,
            text="打开记牌器",
            command=self._switch_on,
            width=10,
            font=("TkDefaultFont", font_size),
        )
        self._btn_switch.pack()

        tk.Button(
            self,
            text="退出程序",
            command=self.destroy,
            width=10,
            font=("TkDefaultFont", font_size),
        ).pack()

        # update_idletasks 强制 tkinter 计算好窗口实际尺寸，
        # 这样 winfo_width/height 才能返回正确值（否则可能返回 1）
        self.update_idletasks()
        x, y = _calculate_offset(self.winfo_width(), self.winfo_height(), config)
        self.geometry(f"+{x}+{y}")

        logger.success("主控窗口初始化完毕")

    # ── 开关 ────────────────────────────────────────────────────────────────

    def _switch_on(self) -> None:
        # 立即禁用按钮，防止用户在后端启动期间重复点击
        self._btn_switch.config(state="disabled")

        # 创建各记牌器悬浮窗（根据 config.yaml 中的 DISPLAY 配置决定是否显示）
        self._windows.clear()
        for wtype in WindowsType:
            if GUI.get(wtype.name, {}).get("DISPLAY", True):
                win = CounterWindow(wtype, self, self._counter, self._tracker)
                self._windows.append(win)

        # 启动后端识别线程
        self._tracker.start()

        # 把按钮的文字和点击行为同时切换成"关闭"
        self._btn_switch.config(text="关闭记牌器", command=self._switch_off)

        # 延迟 100ms 再重新启用按钮，给后端线程足够时间完成启动，
        # 避免用户立刻点关闭时线程还没准备好
        self.after(100, lambda: self._btn_switch.config(state="normal"))
        logger.success("记牌器已打开")

    def _switch_off(self) -> None:
        # 立即禁用按钮，等旧线程完全退出后再重新启用（见 _wait_and_enable）
        self._btn_switch.config(state="disabled")

        # 停止后端线程并销毁所有悬浮窗
        self._tracker.stop()
        for w in self._windows:
            w.destroy()
        self._windows.clear()

        # 重置按钮文字和点击行为，然后等线程退出后再启用
        self._btn_switch.config(text="打开记牌器", command=self._switch_on)
        self._wait_and_enable()
        logger.success("记牌器已关闭")

    def _wait_and_enable(self) -> None:
        # 后端线程是异步的，stop() 只是发信号，线程不会立刻退出。
        # 这里用 after 轮询，确认线程真正结束后才重新启用按钮，
        # 防止用户在旧线程还在跑时再次点开启动新线程。
        if self._tracker.is_running:
            self.after(200, self._wait_and_enable)
        else:
            self._btn_switch.config(state="normal")

    # ── 出牌回调（更新窗口颜色）────────────────────────────────────────────

    def _mark_potential_bombs(self, not_my_cards: set) -> None:
        """识别完手牌后调用：在主窗口把我没有的牌标红，提示用户对手可能持有该牌的炸弹。
        每局开始时先重置所有颜色（清除上一局残留），再标红潜在炸弹。
        红色 = 我没有这张牌，对手可能有炸弹
        黑色 = 这张牌已被某人打出（覆盖红色，说明炸弹已不完整）
        """
        from card_types import WindowsType as WT

        # 先全部重置为默认颜色（黑色），清除上一局残留
        for win in self._windows:
            win.reset_colors()

        # 再把潜在炸弹牌在主窗口标红
        for win in self._windows:
            if win._window_type == WT.MAIN:
                for card in not_my_cards:
                    win.set_card_color(card, "red")

    def _on_card_played(self, player, cards) -> None:
        """tracker 检测到出牌时，更新各窗口的标签颜色。"""
        from card_types import Player

        for win in self._windows:
            for card, count in cards.items():
                # 主窗口：牌名标签变黑，表示这张牌已被打出过（覆盖初始的红色）
                if win._window_type == WindowsType.MAIN:
                    win.set_card_color(card, "black")
                # 左/右窗口：同一回合出了多张同种牌时变红（例如出了两张 K，大概率没有更多的 K 了）
                elif (
                    win._window_type == WindowsType.LEFT and player == Player.LEFT and count > 1
                ):
                    win.set_card_color(card, "red")
                elif (
                    win._window_type == WindowsType.RIGHT
                    and player == Player.RIGHT
                    and count > 1
                ):
                    win.set_card_color(card, "red")

    def delayed_destroy(self) -> None:
        """延迟 1 秒后销毁窗口。供后端错误处理器调用——
        直接在后端线程里调用 destroy() 会导致跨线程操作 tkinter 而卡死，
        改用 after() 把销毁操作调度回主线程执行。"""
        self.after(1000, self.destroy)
