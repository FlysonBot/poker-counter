"""
记牌器悬浮窗。显示剩余牌数和各玩家出牌数，支持拖动和热键。
"""

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from ui.master_window import MasterWindow
    from counter import Counter
    from tracker import Tracker

from loguru import logger

import config as _config
from config import GUI, HOTKEYS
from card_types import Card, WindowsType


# ---------------------------------------------------------------------------
# 文件工具
# ---------------------------------------------------------------------------


def _open_file(filepath: str, label: str) -> None:
    try:
        os.startfile(filepath)
    except Exception:
        logger.error(f"打开{label}失败: {filepath}")
        messagebox.showerror("错误", f"打开{label}失败，请手动查看：{filepath}")


def open_latest_log() -> None:
    # 打包后 exe 在根目录，开发时 __file__ 在 src/ui/ 下，需要往上两级才到根目录
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent
    log_dir = base / "logs"
    try:
        # 按文件名排序，最后一个就是最新的日期
        files = sorted(log_dir.glob("*.log"))
        if not files:
            raise FileNotFoundError
        _open_file(str(files[-1]), "日志文件")
    except Exception:
        logger.error("找不到日志文件")
        messagebox.showerror("错误", f"找不到日志文件，请手动查看目录：{log_dir}")


def open_config() -> None:
    if getattr(sys, "frozen", False):
        path = Path(sys.executable).parent / "config.yaml"
    else:
        path = Path(__file__).parent.parent / "config.yaml"
    _open_file(str(path), "配置文件")


# ---------------------------------------------------------------------------
# 悬浮窗
# ---------------------------------------------------------------------------


class CounterWindow(tk.Toplevel):
    """记牌器悬浮窗，显示剩余牌数（主窗口）或玩家出牌数（左/右窗口）。"""

    def __init__(
        self,
        window_type: WindowsType,
        parent: "MasterWindow",
        counter: "Counter",
        tracker: "Tracker",
    ) -> None:
        super().__init__(parent)
        self.window_type = window_type
        self._parent = parent
        self._counter = counter
        self._tracker = tracker

        config = GUI.get(window_type.name, {})

        # 表格必须在获取窗口尺寸之前创建，否则 winfo_width/height 返回 1
        self._drag_x = 0
        self._drag_y = 0
        self._create_table(config)
        self._setup_style(config)
        self._setup_position(config)
        self._setup_bindings()

        logger.success(f"{window_type.value}窗口初始化完毕")

    # ── 样式与位置 ──────────────────────────────────────────────────────────

    def _setup_style(self, config: dict) -> None:
        self.title(f"记牌器-{self.window_type.value}")
        self.attributes("-topmost", True)  # 始终置于最顶层
        self.overrideredirect(True)  # 去掉系统标题栏和边框
        self.configure(bg="white")
        self.attributes(
            "-transparentcolor", "white"
        )  # 白色背景变透明，实现异形窗口效果
        self.attributes("-alpha", config.get("OPACITY", 1))  # 整体透明度

    def _setup_position(self, config: dict) -> None:
        # 先移到屏幕外，等所有窗口创建完毕后由 master_window 统一调用 reposition()
        self.geometry("+99999+99999")
        self._pending_config = config

    def reposition(self) -> None:
        """所有窗口创建完毕、update_idletasks 之后调用，将窗口移到正确位置。"""
        config = self._pending_config
        w = self.winfo_width()
        h = self.winfo_height()
        x, y = _calculate_offset(w, h, config)
        self.geometry(f"+{x}+{y}")
        logger.info(f"{self.window_type.value}窗口位置: +{x}+{y}，尺寸: {w}x{h}")

    # ── 表格 ────────────────────────────────────────────────────────────────

    def _create_table(self, config: dict) -> None:
        font_size = config.get("FONT_SIZE", 18)

        # 步骤1：创建容器 frame，按窗口类型设置布局方向（水平或垂直）
        frame = self._setup_frame()

        # 步骤2：初始化颜色变量，供后续出牌时动态修改标签颜色
        self._init_color_vars()

        # 步骤3：左右窗口专属——初始化估算列变量，并在第0行创建列标题
        if self.window_type != WindowsType.MAIN:
            self._init_estimate_vars()
            self._build_header_row(frame, font_size)

        # 步骤4：为每张牌创建牌名标签和数量标签，绑定颜色变量和计数器变量
        self._build_card_rows(frame, font_size)

        # 步骤5：设置网格权重，使各格子均匀撑满 frame
        self._configure_grid(frame)

    def _setup_frame(self) -> ttk.Frame:
        """创建容器 frame。主窗口横向排列，左右窗口纵向排列并撑满空间。"""
        frame = ttk.Frame(self)
        if self.window_type == WindowsType.MAIN:
            frame.pack(padx=0, pady=0)
        else:
            frame.pack(padx=0, pady=0, fill="both", expand=True)
        return frame

    def _init_color_vars(self) -> None:
        """为每张牌创建颜色 StringVar。
        通过 trace 绑定到标签的 fg，出牌时只需更新变量，标签自动变色。
        """
        self._color_vars: dict[Card, tk.StringVar] = {
            card: tk.StringVar(value="black") for card in Card
        }

    def _init_estimate_vars(self) -> None:
        """左右窗口专属：初始化估算列的显示值和颜色变量。
        estimate_vars 存估算张数（初始显示"?"），estimate_color_vars 存置信度颜色。
        """
        self._estimate_vars: dict[Card, tk.StringVar] = {
            card: tk.StringVar(value="?") for card in Card
        }
        self._estimate_color_vars: dict[Card, tk.StringVar] = {
            card: tk.StringVar(value="black") for card in Card
        }
        self._estimate_labels: dict[Card, tk.Label] = {}

    def _build_header_row(self, frame: ttk.Frame, font_size: int) -> None:
        """左右窗口专属：在第0行创建"牌 / 出 / 剩"列标题。"""
        header_font = ("Arial", font_size - 2)
        for col_idx, header_text in enumerate(["牌", "出", "剩"]):
            tk.Label(
                frame,
                text=header_text,
                anchor="center",
                relief="solid",
                highlightbackground="red",
                highlightthickness=1,
                width=2,
                font=header_font,
                bg="lightgray",
                fg="black",
            ).grid(row=0, column=col_idx, sticky="nsew")

    def _build_card_rows(self, frame: ttk.Frame, font_size: int) -> None:
        """为每张牌创建一行标签，并把颜色变量和计数器变量绑定上去。

        绑定机制说明：
        - 数量标签用 textvariable 绑定 Counter.IntVar，计数变化时自动刷新显示
        - 颜色标签用 trace 监听 StringVar，出牌事件只需 set() 变量即可触发重绘
        """
        is_main = self.window_type == WindowsType.MAIN
        self._card_labels: dict[Card, tk.Label] = {}
        self._count_labels: dict[Card, tk.Label] = {}

        # make_label：统一样式的标签工厂，所有格子共用相同的边框和对齐设置
        def make_label(**kw: Any) -> tk.Label:
            return tk.Label(
                frame,
                anchor="center",
                relief="solid",
                highlightbackground="red",
                highlightthickness=1,
                width=2,
                **kw,
            )

        # get_var：根据窗口类型选择对应的计数器变量
        # 主窗口显示剩余数，左/右窗口分别显示左家/右家的出牌数
        def get_var(card: Card) -> tk.IntVar:
            if is_main:
                return self._counter.remaining[card]
            elif self.window_type == WindowsType.LEFT:
                return self._counter.left[card]
            else:
                return self._counter.right[card]

        # 逐张牌创建标签行，放入网格
        for idx, card in enumerate(Card):
            name_text = card.value if card != Card.JOKER else "王"
            card_lbl = make_label(
                text=name_text, font=("Arial", font_size), bg="lightblue", fg="black"
            )
            count_lbl = make_label(
                textvariable=get_var(card),
                font=("Arial", font_size, "bold"),
                bg="lightyellow",
                fg="black",
            )

            if is_main:
                # 主窗口：横向排列，牌名在第0行，数量在第1行
                # 颜色变量绑定到牌名标签——变色表示该牌已从剩余中扣除
                card_lbl.grid(row=0, column=idx, sticky="nsew")
                count_lbl.grid(row=1, column=idx, sticky="nsew")
                self._color_vars[card].trace_add(
                    "write",
                    lambda *_, c=card, lbl=card_lbl: lbl.config(  # type: ignore[arg-type]
                        fg=self._color_vars[c].get()
                    ),
                )
            else:
                # 左右窗口：纵向排列，第0行是标题，数据行从第1行开始
                # 颜色变量绑定到数量标签——变红表示同一回合出了多张同种牌
                row = idx + 1
                card_lbl.grid(row=row, column=0, sticky="nsew")
                count_lbl.grid(row=row, column=1, sticky="nsew")
                self._color_vars[card].trace_add(
                    "write",
                    lambda *_, c=card, lbl=count_lbl: lbl.config(  # type: ignore[arg-type]
                        fg=self._color_vars[c].get()
                    ),
                )
                # 估算列：显示 Analyzer 推算的对手持牌数，颜色表示置信度
                est_lbl = make_label(
                    textvariable=self._estimate_vars[card],
                    font=("Arial", font_size, "bold"),
                    bg="lightyellow",
                    fg="black",
                )
                est_lbl.grid(row=row, column=2, sticky="nsew")
                self._estimate_color_vars[card].trace_add(
                    "write",
                    lambda *_, c=card, lbl=est_lbl: lbl.config(  # type: ignore[arg-type]
                        fg=self._estimate_color_vars[c].get()
                    ),
                )
                self._estimate_labels[card] = est_lbl

            self._card_labels[card] = card_lbl
            self._count_labels[card] = count_lbl

    def _configure_grid(self, frame: ttk.Frame) -> None:
        """设置网格行列权重，使所有格子均匀撑满 frame。"""
        is_main = self.window_type == WindowsType.MAIN
        rows = 2 if is_main else len(Card) + 1
        cols = len(Card) if is_main else 3
        for i in range(rows):
            frame.grid_rowconfigure(i, weight=1)
        for j in range(cols):
            frame.grid_columnconfigure(j, weight=1)

    # ── 颜色更新（供 tracker 回调调用）────────────────────────────────────

    def set_card_color(self, card: Card, color: str) -> None:
        self._color_vars[card].set(color)

    def reset_colors(self) -> None:
        for var in self._color_vars.values():
            var.set("black")
        if self.window_type != WindowsType.MAIN:
            for card in Card:
                self._estimate_vars[card].set("?")
                self._estimate_color_vars[card].set("black")

    def set_estimate(self, card: Card, value: int, confidence: str) -> None:
        """更新估算列。confidence: 'low'=红色, 'high'=绿色, 其他=黑色。"""
        color_map = {"low": "red", "high": "green"}
        self._estimate_vars[card].set(str(value))
        self._estimate_color_vars[card].set(color_map.get(confidence, "black"))

    # ── 绑定 ────────────────────────────────────────────────────────────────

    def _setup_bindings(self) -> None:
        # 鼠标拖动：记录起始位置，随鼠标移动更新窗口坐标，释放时保存位置
        self.bind("<Button-1>", self._drag_start)
        self.bind("<B1-Motion>", self._drag_move)
        self.bind("<ButtonRelease-1>", self._drag_end)

        # 热键：从 config.yaml 读取按键映射，绑定到对应操作
        hotkey_map = {
            "QUIT": lambda e: self._parent.destroy(),
            "OPEN_LOG": lambda e: open_latest_log(),
            "OPEN_CONFIG": lambda e: open_config(),
            "RESET": lambda e: self._reset(),
            "TOGGLE_OVERLAY": lambda e: self._parent.toggle_overlay(),
        }
        for key, callback in hotkey_map.items():
            if key in HOTKEYS:
                try:
                    self.bind(f"<KeyPress-{HOTKEYS[key]}>", callback)
                except Exception:
                    logger.error(f"热键 {key}={HOTKEYS[key]} 绑定失败")

    def _drag_start(self, event: tk.Event) -> None:
        # 记录鼠标按下时相对于窗口左上角的偏移，用于后续拖动计算
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event: tk.Event) -> None:
        # 用鼠标当前位置减去起始偏移，得到窗口新的左上角坐标
        x = self.winfo_x() + (event.x - self._drag_x)
        y = self.winfo_y() + (event.y - self._drag_y)
        self.geometry(f"+{x}+{y}")

    def _drag_end(self, event: tk.Event) -> None:
        """拖动结束时把新位置写回 config.yaml，下次启动时自动恢复。"""
        x = self.winfo_x()
        y = self.winfo_y()
        key = self.window_type.name  # "MAIN" / "LEFT" / "RIGHT"
        try:
            if getattr(sys, "frozen", False):
                path = Path(sys.executable).parent / "config.yaml"
            else:
                path = Path(__file__).parent.parent / "config.yaml"
            yaml = YAML()
            yaml.preserve_quotes = True
            with open(path, encoding="utf-8") as f:
                data = yaml.load(f)
            data["GUI"][key]["OFFSET_X"] = x
            data["GUI"][key]["OFFSET_Y"] = y
            # 清除 CENTER_X/Y，避免与 OFFSET 冲突
            for k in ("CENTER_X", "CENTER_Y"):
                data["GUI"][key].pop(k, None)
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f)
            # 同步更新内存，使关闭/重新打开记牌器时也读到新坐标
            _config.GUI[key]["OFFSET_X"] = x
            _config.GUI[key]["OFFSET_Y"] = y
            for k in ("CENTER_X", "CENTER_Y"):
                _config.GUI[key].pop(k, None)
            logger.debug(f"{key} 窗口位置已保存: +{x}+{y}")
        except Exception as e:
            logger.warning(f"保存窗口位置失败: {e}")

    def _reset(self) -> None:
        # 重启后端线程：stop 发出停止信号，start 重新开始等待游戏
        self._tracker.stop()
        self._tracker.start()


# ---------------------------------------------------------------------------
# 窗口位置计算
# ---------------------------------------------------------------------------


def _calculate_offset(w: int, h: int, config: dict) -> tuple[int, int]:
    # config 里 OFFSET 和 CENTER 二选一：
    # OFFSET 直接指定窗口左上角坐标；CENTER 指定窗口中心坐标（需要减去半个窗口尺寸换算）
    if config.get("OFFSET_X") is not None:
        x = config["OFFSET_X"]
    elif config.get("CENTER_X") is not None:
        x = config["CENTER_X"] - w // 2
    else:
        x = 0

    if config.get("OFFSET_Y") is not None:
        y = config["OFFSET_Y"]
    elif config.get("CENTER_Y") is not None:
        y = config["CENTER_Y"] - h // 2
    else:
        y = 0

    return int(x), int(y)
