"""
主控窗口模块。

提供"打开/关闭记牌器"和"退出程序"按钮，是整个程序的顶层入口。
负责管理 Counter、Analyzer、Tracker 和所有 CounterWindow 的生命周期，
并通过 GameCallbacks 接收后端出牌事件，将结果分发到各悬浮窗。
"""

import tkinter as tk

from loguru import logger

import config as _config
from card_types import Player, WindowsType
from config import GUI, HOTKEYS, config_dir
from tracking.analyzer import Analyzer
from tracking.counter import CardCounts, Counter
from tracking.tracker import GameCallbacks, Tracker
from ui.counter_window import CounterWindow, _calculate_offset
from ui.overlay_manager import OverlayManager, load_yaml, save_yaml


class MasterWindow(tk.Tk):
    """顶级控制窗口，持有所有核心对象的生命周期。

    创建并管理 Counter、Analyzer、Tracker 和 CounterWindow 实例。
    通过 GameCallbacks 将后端事件（出牌、重置、游戏结束）桥接到 UI 更新。
    """

    def __init__(self) -> None:
        super().__init__()
        # 创建核心对象：计数器、分析器、追踪器
        # Tracker 持有 Counter 的引用，游戏事件通过 callbacks 回调到 MasterWindow
        self._counter = Counter()
        self._analyzer = Analyzer(self._counter)
        self._tracker = Tracker(
            self._counter,
            GameCallbacks(
                on_update=self._on_card_played,
                mark_potential_bombs=self._mark_potential_bombs,
                on_reset=self._on_reset,
                on_game_end=self._on_game_end,
            ),
        )
        self._windows: list[CounterWindow] = []

        # 读取开关按钮的配置
        config = GUI.get("SWITCH", {})
        font_size = config.get("FONT_SIZE", 12)

        # 配置窗口外观：置顶、去边框、白色背景透明化实现异形窗口
        self.title("记牌器开关")
        self.attributes("-topmost", True)  # 窗口始终置于最顶层
        self.overrideredirect(True)  # 去掉系统标题栏和边框
        self.configure(bg="white")
        self.attributes(
            "-transparentcolor", "white"
        )  # 白色背景变透明，实现异形窗口效果

        # 叠加层管理器：热键 c 切换显示/隐藏，首次启动自动显示
        # 必须在按钮创建前初始化，因为"调整"按钮的 command 通过 toggle_overlay() 引用它
        self._overlay = OverlayManager(self)
        hotkey = HOTKEYS.get("TOGGLE_OVERLAY", "c")
        self.bind(f"<KeyPress-{hotkey}>", lambda _e: self._overlay.toggle())

        # 开关按钮：打开/关闭记牌器，text 和 command 会在开关时动态切换
        self._btn_switch = tk.Button(
            self,
            text="打开记牌器",
            command=self._switch_on,
            width=10,
            font=("TkDefaultFont", font_size),
        )
        self._btn_switch.pack(fill="x")

        # 创建退出按钮
        tk.Button(
            self,
            text="退出程序",
            command=self.destroy,
            width=10,
            font=("TkDefaultFont", font_size),
        ).pack(fill="x")

        # 调整 + 帮助 按钮并排一行，撑满与上方按钮等宽
        btn_row = tk.Frame(self, bg="white")
        btn_row.pack(fill="x")
        tk.Button(
            btn_row,
            text="调整",
            command=self.toggle_overlay,
            font=("TkDefaultFont", font_size),
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            btn_row,
            text="帮助",
            command=self._show_help,
            font=("TkDefaultFont", font_size),
        ).pack(side="left", fill="x", expand=True)

        # update_idletasks 强制 tkinter 计算好窗口实际尺寸，
        # 这样 winfo_width/height 才能返回正确值（否则可能返回 1）
        self.update_idletasks()
        x, y = _calculate_offset(self.winfo_width(), self.winfo_height(), config)
        self.geometry(f"+{x}+{y}")

        # 首次启动时自动弹出区域校准覆盖层，引导用户完成初始设置
        self._overlay.show_if_first_launch()

        # 拖动支持：记录拖动起点和状态，绑定鼠标事件
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._dragging = False
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_move)
        self.bind("<ButtonRelease-1>", self._on_drag_end)

        logger.success("主控窗口初始化完毕")

    # ── 开关 ────────────────────────────────────────────────────────────────

    def _switch_on(self) -> None:
        # 立即禁用按钮，防止用户在后端启动期间重复点击
        self._btn_switch.config(state="disabled")

        # 开始计数时自动隐藏叠加层（假定用户已完成区域调整）
        self._overlay.hide()

        # 创建各记牌器悬浮窗（根据 config.yaml 中的 DISPLAY 配置决定是否显示）
        self._windows.clear()
        for wtype in WindowsType:
            if GUI.get(wtype.name, {}).get("DISPLAY", True):
                window = CounterWindow(wtype, self, self._counter, self._tracker)
                self._windows.append(window)

        # 所有窗口创建完毕后统一计算尺寸并定位，避免逐个定位时的闪烁
        self.update_idletasks()
        for window in self._windows:
            window.reposition()

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
        for window in self._windows:
            window.destroy()
        self._windows.clear()

        # 重置按钮文字和点击行为，然后等线程退出后再启用
        self._btn_switch.config(text="打开记牌器", command=self._switch_on)
        self._wait_and_enable()
        logger.success("记牌器已关闭")

    def _enable_switch(self) -> None:
        """重新启用开关按钮。"""
        self._btn_switch.config(state="normal")

    def _wait_and_enable(self) -> None:
        # 后端线程是异步的，stop() 只是发信号，线程不会立刻退出。
        # 这里用 after 轮询，确认线程真正结束后才重新启用按钮，
        # 防止用户在旧线程还在跑时再次点开启动新线程。
        if self._tracker.is_running:
            self.after(200, self._wait_and_enable)  # type: ignore
        else:
            self._enable_switch()

    def toggle_overlay(self) -> None:
        """切换区域调整叠加层的显示/隐藏。"""
        self._overlay.toggle()

    # ── 游戏事件回调 ─────────────────────────────────────────────────────────

    def _on_reset(self) -> None:
        """游戏结束/重置时调用：重置所有窗口颜色，与数字重置同步。"""
        self._analyzer.reset()
        for window in self._windows:
            window.reset_colors()

    def _mark_potential_bombs(self, not_my_cards: set) -> None:
        """识别完手牌后调用：在主窗口把我没有的牌标红，提醒自己手里没有该牌，方便推算对手持牌。
        红色 = 我没有这张牌
        黑色 = 这张牌已被某人打出
        """
        for window in self._windows:
            if window.window_type == WindowsType.MAIN:
                for card in not_my_cards:
                    window.set_card_color(card, "red")

    def _on_card_played(self, player: Player, cards: "CardCounts") -> None:
        """tracker 检测到出牌时，更新窗口颜色和估算。"""
        # 将出牌玩家映射到对应的悬浮窗，用于颜色更新和估算显示
        player_wintype = {
            Player.LEFT: WindowsType.LEFT,
            Player.RIGHT: WindowsType.RIGHT,
        }
        target_windows = {window.window_type: window for window in self._windows}

        # 左/右窗口：同一回合出了多张同种牌时标红，提示该玩家可能手里没有更多这张牌
        if player in player_wintype:
            window = target_windows.get(player_wintype[player])
            if window:
                for card, count in cards.items():
                    if count > 1:
                        window.set_card_color(card, "red")

        # 委托 analyzer 推算对手持牌，再把结果写入对应悬浮窗的估算列
        updates = self._analyzer.on_card_played(player, cards)
        for target, card, value, confidence in updates:
            wintype = player_wintype.get(target)
            window = target_windows.get(wintype) if wintype is not None else None
            if window:
                window.set_estimate(card, value, confidence)

    def _on_game_end(self, winner: Player, _landlord: Player) -> None:
        """游戏结束时输出误差分析。"""
        self._analyzer.on_game_end(winner)

    # ── 拖动 ────────────────────────────────────────────────────────────────

    _DRAG_THRESHOLD = 10  # 超过此像素距离才视为拖动，否则视为点击

    def _on_drag_start(self, event: tk.Event) -> None:
        # 记录鼠标按下时的起始坐标，重置拖动状态
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._dragging = False

    def _on_drag_move(self, event: tk.Event) -> None:
        # 计算鼠标相对于起点的偏移量
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        # 移动超过阈值才开始拖动，避免误触
        if not self._dragging and (
            abs(dx) > self._DRAG_THRESHOLD or abs(dy) > self._DRAG_THRESHOLD
        ):
            self._dragging = True
        # 实时跟随鼠标移动窗口位置
        if self._dragging:
            x = self.winfo_x() + dx
            y = self.winfo_y() + dy
            self.geometry(f"+{x}+{y}")

    def _on_drag_end(self, _event: tk.Event) -> None:
        # 如果没有真正拖动（只是点击），直接返回
        if not self._dragging:
            return
        self._dragging = False
        x = self.winfo_x()
        y = self.winfo_y()

        # 拖动结束时把新位置写回 config.yaml，下次启动时自动恢复
        try:
            path = config_dir() / "config.yaml"
            yaml, data = load_yaml(path)
            data["GUI"]["SWITCH"]["OFFSET_X"] = x
            data["GUI"]["SWITCH"]["OFFSET_Y"] = y

            # 清除 CENTER_X/Y，避免与 OFFSET 冲突（两者只能取其一）
            for k in ("CENTER_X", "CENTER_Y"):
                data["GUI"]["SWITCH"].pop(k, None)
            save_yaml(path, yaml, data)

            # 同步更新内存，使下次读取时也是最新坐标
            _config.GUI["SWITCH"]["OFFSET_X"] = x
            _config.GUI["SWITCH"]["OFFSET_Y"] = y
            for k in ("CENTER_X", "CENTER_Y"):
                _config.GUI["SWITCH"].pop(k, None)
            logger.debug(f"主控窗口位置已保存: +{x}+{y}")

        except Exception as e:
            logger.warning(f"保存主控窗口位置失败: {e}")

    # ── 其他 ─────────────────────────────────────────────────────────────────

    def _show_help(self) -> None:
        """弹出帮助对话框。"""

        # 创建置顶的帮助弹窗，禁止调整大小
        dialog = tk.Toplevel(self)
        dialog.title("帮助")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)

        # 帮助文本：颜色说明、热键列表、排查步骤
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
            dialog,
            text=help_text,
            justify="left",
            font=("TkFixedFont", 10),
            padx=16,
            pady=12,
        ).pack()
        tk.Button(dialog, text="关闭", command=dialog.destroy, width=8).pack(
            pady=(0, 10)
        )

    def delayed_destroy(self) -> None:
        """延迟 1 秒后销毁窗口。供后端错误处理器调用——
        直接在后端线程里调用 destroy() 会导致跨线程操作 tkinter 而卡死，
        改用 after() 把销毁操作调度回主线程执行。"""

        self.after(1000, self.destroy)  # type: ignore
