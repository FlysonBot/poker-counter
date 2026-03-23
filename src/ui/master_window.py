"""
主控窗口。显示开关和退出按钮，管理记牌器窗口和后端线程的生命周期。
"""

import tkinter as tk

from loguru import logger

from config import GUI, HOTKEYS
from tracker import Counter, Tracker
from card_types import Player, WindowsType
from ui.counter_window import CounterWindow, _calculate_offset
from ui.overlay_manager import OverlayManager


class MasterWindow(tk.Tk):
    """顶级窗口：开关按钮 + 退出按钮。"""

    def __init__(self) -> None:
        super().__init__()
        self._counter = Counter()
        self._tracker = Tracker(
            self._counter,
            on_update=self._on_card_played,
            mark_potential_bombs=self._mark_potential_bombs,
            on_reset=self._on_reset,
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
        self._btn_switch.pack(fill="x")

        tk.Button(
            self,
            text="退出程序",
            command=self.destroy,
            width=10,
            font=("TkDefaultFont", font_size),
        ).pack(fill="x")

        # 调整 + 帮助并排一行
        btn_row = tk.Frame(self, bg="white")
        btn_row.pack()
        tk.Button(
            btn_row,
            text="调整",
            command=lambda: self._overlay.toggle(),
            width=4,
            font=("TkDefaultFont", font_size),
        ).pack(side="left")
        tk.Button(
            btn_row,
            text="帮助",
            command=self._show_help,
            width=4,
            font=("TkDefaultFont", font_size),
        ).pack(side="left")

        # update_idletasks 强制 tkinter 计算好窗口实际尺寸，
        # 这样 winfo_width/height 才能返回正确值（否则可能返回 1）
        self.update_idletasks()
        x, y = _calculate_offset(self.winfo_width(), self.winfo_height(), config)
        self.geometry(f"+{x}+{y}")

        # 叠加层管理器：热键 c 切换显示/隐藏，首次启动自动显示
        self._overlay = OverlayManager(self)
        hotkey = HOTKEYS.get("TOGGLE_OVERLAY", "c")
        self.bind(f"<KeyPress-{hotkey}>", lambda e: self._overlay.toggle())
        self._overlay.show_if_first_launch()

        logger.success("主控窗口初始化完毕")

    # ── 开关 ────────────────────────────────────────────────────────────────

    def _switch_on(self) -> None:
        # 立即禁用按钮，防止用户在后端启动期间重复点击
        self._btn_switch.config(state="disabled")

        # 开始计数时自动隐藏叠加层（假定用户已完成区域调整）
        self._overlay._hide()

        # 创建各记牌器悬浮窗（根据 config.yaml 中的 DISPLAY 配置决定是否显示）
        self._windows.clear()
        for wtype in WindowsType:
            if GUI.get(wtype.name, {}).get("DISPLAY", True):
                win = CounterWindow(wtype, self, self._counter, self._tracker)
                self._windows.append(win)

        # 所有窗口创建完毕后统一计算尺寸并定位，避免逐个定位时的闪烁
        self.update_idletasks()
        for win in self._windows:
            win.reposition()

        # 启动后端识别线程
        self._tracker.start()

        # 把按钮的文字和点击行为同时切换成"关闭"
        self._btn_switch.config(text="关闭记牌器", command=self._switch_off)

        # 延迟 100ms 再重新启用按钮，给后端线程足够时间完成启动，
        # 避免用户立刻点关闭时线程还没准备好
        self.after(100, self._enable_switch)  # type: ignore
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

    def _enable_switch(self) -> None:
        self._btn_switch.config(state="normal")

    def _wait_and_enable(self) -> None:
        # 后端线程是异步的，stop() 只是发信号，线程不会立刻退出。
        # 这里用 after 轮询，确认线程真正结束后才重新启用按钮，
        # 防止用户在旧线程还在跑时再次点开启动新线程。
        if self._tracker.is_running:
            self.after(200, self._wait_and_enable)  # type: ignore
        else:
            self._enable_switch()

    # ── 出牌回调（更新窗口颜色）────────────────────────────────────────────

    def _on_reset(self) -> None:
        """游戏结束/重置时调用：重置所有窗口颜色，与数字重置同步。"""
        for win in self._windows:
            win.reset_colors()

    def _mark_potential_bombs(self, not_my_cards: set) -> None:
        """识别完手牌后调用：在主窗口把我没有的牌标红，提示用户对手可能持有该牌的炸弹。
        红色 = 我没有这张牌，对手可能有炸弹
        黑色 = 这张牌已被某人打出（覆盖红色，说明炸弹已不完整）
        """
        # 把潜在炸弹牌在主窗口标红
        for win in self._windows:
            if win._window_type == WindowsType.MAIN:
                for card in not_my_cards:
                    win.set_card_color(card, "red")

    def _on_card_played(self, player, cards) -> None:
        """tracker 检测到出牌时，更新左右窗口的标签颜色。"""
        for win in self._windows:
            for card, count in cards.items():
                # 左/右窗口：同一回合出了多张同种牌时变红（例如出了两张 K，大概率没有更多的 K 了）
                if (
                    win._window_type == WindowsType.LEFT
                    and player == Player.LEFT
                    and count > 1
                ):
                    win.set_card_color(card, "red")
                elif (
                    win._window_type == WindowsType.RIGHT
                    and player == Player.RIGHT
                    and count > 1
                ):
                    win.set_card_color(card, "red")

    def _show_help(self) -> None:
        """弹出帮助对话框。"""
        win = tk.Toplevel(self)
        win.title("帮助")
        win.attributes("-topmost", True)
        win.resizable(False, False)

        help_text = (
            "═══ 颜色说明 ═══\n"
            "\n"
            "【主记牌器（顶部横排）】\n"
            "  红色 = 我手里没有这张牌\n"
            "  黑色 = 其余牌\n"
            "\n"
            "【上家 / 下家记牌器（竖排）】\n"
            "  红色 = 该玩家同一回合打出了2张以上同种牌\n"
            "        → 该玩家手里可能已没有更多这张牌\n"
            "\n"
            "═══ 热键（需点击任意记牌器窗口后生效）═══\n"
            "\n"
            f"  {HOTKEYS.get('TOGGLE_OVERLAY', 'c').upper()}  调整区域叠加层\n"
            f"  {HOTKEYS.get('RESET', 'r').upper()}  重置记牌器\n"
            f"  {HOTKEYS.get('OPEN_LOG', 'l').upper()}  打开日志文件\n"
            f"  {HOTKEYS.get('OPEN_CONFIG', 'o').upper()}  打开配置文件\n"
            f"  {HOTKEYS.get('QUIT', 'q').upper()}  退出程序\n"
            "\n"
            "═══ 程序不工作？ ═══\n"
            "\n"
            "1. 确认游戏窗口标题含「斗地主」\n"
            "2. 点「调整」检查各区域是否对准游戏画面\n"
            "   粉色边框应覆盖对应区域（出牌区、手牌区等）\n"
            "3. 打开日志（按 L）查看错误信息\n"
            "4. 尝试重置（按 R）后重新打开记牌器\n"
        )

        tk.Label(
            win,
            text=help_text,
            justify="left",
            font=("TkFixedFont", 10),
            padx=16,
            pady=12,
        ).pack()
        tk.Button(win, text="关闭", command=win.destroy, width=8).pack(pady=(0, 10))

    def delayed_destroy(self) -> None:
        """延迟 1 秒后销毁窗口。供后端错误处理器调用——
        直接在后端线程里调用 destroy() 会导致跨线程操作 tkinter 而卡死，
        改用 after() 把销毁操作调度回主线程执行。"""
        self.after(1000, self._do_destroy)  # type: ignore

    def _do_destroy(self) -> None:
        self.destroy()
