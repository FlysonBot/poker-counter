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
    import sys
    from pathlib import Path

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
        self, window_type: WindowsType, parent: "MasterWindow", counter, tracker
    ) -> None:
        """
        counter: tracker.Counter 实例
        tracker: tracker.Tracker 实例（用于热键 reset）
        """
        super().__init__(parent)
        self._window_type = window_type
        self._parent = parent
        self._counter = counter
        self._tracker = tracker

        config = GUI.get(window_type.name, {})

        # 表格必须在获取窗口尺寸之前创建，否则 winfo_width/height 返回 1
        self._create_table(config)
        self._setup_style(config)
        self._setup_position(config)
        self._setup_bindings()

        logger.success(f"{window_type.value}窗口初始化完毕")

    # ── 样式与位置 ──────────────────────────────────────────────────────────

    def _setup_style(self, config: dict) -> None:
        self.title(f"记牌器-{self._window_type.value}")
        self.attributes("-topmost", True)  # 始终置于最顶层
        self.overrideredirect(True)  # 去掉系统标题栏和边框
        self.configure(bg="white")
        self.attributes(
            "-transparentcolor", "white"
        )  # 白色背景变透明，实现异形窗口效果
        self.attributes("-alpha", config.get("OPACITY", 1))  # 整体透明度

    def _setup_position(self, config: dict) -> None:
        # 强制 tkinter 计算好实际尺寸，再读取宽高用于定位
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x, y = _calculate_offset(w, h, config)
        self.geometry(f"+{x}+{y}")
        logger.info(f"{self._window_type.value}窗口位置: +{x}+{y}，尺寸: {w}x{h}")

    # ── 表格 ────────────────────────────────────────────────────────────────

    def _create_table(self, config: dict) -> None:
        frame = ttk.Frame(self)
        font_size = config.get("FONT_SIZE", 18)
        is_main = self._window_type == WindowsType.MAIN

        # 主窗口横向排列（牌名一行，数量一行）；左右窗口竖向排列（每张牌占一行）
        if is_main:
            frame.pack(padx=0, pady=0)
            rows, cols = 2, len(Card)
        else:
            frame.pack(padx=0, pady=0, fill="both", expand=True)
            rows, cols = len(Card), 2

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

        # 每张牌对应一个 StringVar，用于在后端出牌时动态修改标签颜色
        self._color_vars: dict[Card, tk.StringVar] = {
            card: tk.StringVar(value="black") for card in Card
        }

        self._card_labels: dict[Card, tk.Label] = {}
        self._count_labels: dict[Card, tk.Label] = {}

        # 根据窗口类型决定数量标签绑定哪个计数器变量
        # textvariable 让标签内容自动跟随 IntVar 变化，无需手动刷新
        if is_main:
            get_var = lambda card: self._counter.remaining[card]
        elif self._window_type == WindowsType.LEFT:
            get_var = lambda card: self._counter.left[card]
        else:
            get_var = lambda card: self._counter.right[card]

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
                card_lbl.grid(row=0, column=idx, sticky="nsew")
                count_lbl.grid(row=1, column=idx, sticky="nsew")
                # 主窗口：颜色变量绑定到牌名标签（变色表示该牌已被打出）
                self._color_vars[card].trace_add(
                    "write",
                    lambda *_, c=card, lbl=card_lbl: lbl.config(  # type: ignore[arg-type]
                        fg=self._color_vars[c].get()
                    ),
                )
            else:
                card_lbl.grid(row=idx, column=0, sticky="nsew")
                count_lbl.grid(row=idx, column=1, sticky="nsew")
                # 左右窗口：颜色变量绑定到数量标签（变红表示同一回合出了多张）
                self._color_vars[card].trace_add(
                    "write",
                    lambda *_, c=card, lbl=count_lbl: lbl.config(  # type: ignore[arg-type]
                        fg=self._color_vars[c].get()
                    ),
                )

            self._card_labels[card] = card_lbl
            self._count_labels[card] = count_lbl

        # 设置网格权重使各格子均匀分布
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
            "TOGGLE_OVERLAY": lambda e: self._parent._overlay.toggle(),
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
        key = self._window_type.name  # "MAIN" / "LEFT" / "RIGHT"
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
    x = (
        config.get("OFFSET_X")
        if config.get("OFFSET_X") is not None
        else (
            config.get("CENTER_X", 0) - w // 2
            if config.get("CENTER_X") is not None
            else 0
        )
    )
    y = (
        config.get("OFFSET_Y")
        if config.get("OFFSET_Y") is not None
        else (
            config.get("CENTER_Y", 0) - h // 2
            if config.get("CENTER_Y") is not None
            else 0
        )
    )
    return int(x), int(y)
