"""
区域调整叠加窗口。
每个游戏区域对应一个半透明粉色边框窗口，叠加在游戏画面上方，
用户可以拖动移动、拖动边缘调整大小，调整后保存到 config.yaml。
"""

import tkinter as tk
from loguru import logger

# 边框宽度（像素），用于边缘拖拽检测和视觉显示
BORDER = 8
# 边框颜色
BORDER_COLOR = "pink"
# 标签字体
LABEL_FONT = ("Arial", 9)


class OverlayWindow(tk.Toplevel):
    """单个区域的叠加调整窗口。
    外观：纯粉色边框 + 透明内部 + 区域名称标签。
    交互：内部拖动移动，边缘拖动缩放（类似系统窗口调整大小）。
    """

    def __init__(self, parent: tk.Tk, region_name: str, x1: int, y1: int, x2: int, y2: int) -> None:
        """
        region_name: 区域名称，显示在窗口上作为标识
        x1, y1, x2, y2: 初始像素坐标（相对于屏幕）
        """
        super().__init__(parent)

        self._region_name = region_name
        self._on_change_callback = None  # 坐标变化时的回调，由 overlay_manager 注册

        # ── 窗口属性 ──────────────────────────────────────────────────────
        self.overrideredirect(True)       # 去掉系统标题栏
        self.attributes("-topmost", True) # 始终置顶
        self.attributes("-transparentcolor", "white")  # 内部白色区域透明
        self.configure(bg=BORDER_COLOR)
        self.wm_attributes("-alpha", 0.6) # 整体半透明

        # 不抢夺输入焦点，避免遮挡游戏操作
        self.wm_attributes("-disabled", False)

        # ── 内部透明区域（白色 = 透明）───────────────────────────────────
        # 用一个白色 frame 填充内部，配合 transparentcolor 实现"只显示边框"的效果
        self._inner = tk.Frame(self, bg="white")
        self._inner.place(
            x=BORDER, y=BORDER,
            relwidth=1.0, relheight=1.0,
            width=-2 * BORDER, height=-2 * BORDER,
        )

        # 区域名称标签，显示在左上角便于识别
        self._label = tk.Label(
            self,
            text=region_name,
            bg=BORDER_COLOR,
            fg="black",
            font=LABEL_FONT,
            anchor="w",
        )
        self._label.place(x=BORDER, y=0)

        # ── 设置初始位置和大小 ────────────────────────────────────────────
        w = max(x2 - x1, 40)
        h = max(y2 - y1, 40)
        self.geometry(f"{w}x{h}+{x1}+{y1}")

        # ── 拖拽状态 ──────────────────────────────────────────────────────
        self._drag_data = {}   # 记录拖拽起始信息

        # ── 绑定事件 ──────────────────────────────────────────────────────
        # 内部区域：移动窗口
        self._inner.bind("<Button-1>",   self._move_start)
        self._inner.bind("<B1-Motion>",  self._move_do)
        self._inner.bind("<ButtonRelease-1>", self._on_release)

        # 外层边框（self）：调整大小
        self.bind("<Button-1>",          self._resize_start)
        self.bind("<B1-Motion>",         self._resize_do)
        self.bind("<ButtonRelease-1>",   self._on_release)

        # 鼠标进入边框区域时改变光标形状，提示可调整大小
        self.bind("<Motion>", self._update_cursor)

        logger.debug(f"叠加窗口 [{region_name}] 创建完毕，位置 {x1},{y1} 大小 {w}x{h}")

    def register_on_change(self, callback) -> None:
        """注册坐标变化回调，在用户释放鼠标后触发。"""
        self._on_change_callback = callback

    # ── 移动逻辑 ──────────────────────────────────────────────────────────

    def _move_start(self, event: tk.Event) -> None:
        # 记录鼠标按下时相对于窗口左上角的偏移
        self._drag_data = {"mode": "move", "x": event.x, "y": event.y}

    def _move_do(self, event: tk.Event) -> None:
        x = self.winfo_x() + (event.x - self._drag_data["x"])
        y = self.winfo_y() + (event.y - self._drag_data["y"])
        self.geometry(f"+{x}+{y}")

    # ── 缩放逻辑 ──────────────────────────────────────────────────────────

    def _get_edge(self, x: int, y: int) -> str:
        """根据鼠标在窗口内的位置，判断拖拽的是哪条边/角。
        返回方向字符串，例如 'nw'、'n'、'e'、'se' 等，空字符串表示内部。
        """
        w = self.winfo_width()
        h = self.winfo_height()
        on_left   = x < BORDER
        on_right  = x > w - BORDER
        on_top    = y < BORDER
        on_bottom = y > h - BORDER

        if on_top and on_left:     return "nw"
        if on_top and on_right:    return "ne"
        if on_bottom and on_left:  return "sw"
        if on_bottom and on_right: return "se"
        if on_top:                 return "n"
        if on_bottom:              return "s"
        if on_left:                return "w"
        if on_right:               return "e"
        return ""

    def _update_cursor(self, event: tk.Event) -> None:
        """鼠标移动时根据位置更新光标形状，提示用户可以拖拽的方向。"""
        edge = self._get_edge(event.x, event.y)
        cursor_map = {
            "nw": "top_left_corner",  "se": "bottom_right_corner",
            "ne": "top_right_corner", "sw": "bottom_left_corner",
            "n":  "top_side",         "s":  "bottom_side",
            "w":  "left_side",        "e":  "right_side",
            "":   "fleur",
        }
        self.config(cursor=cursor_map.get(edge, "arrow"))

    def _resize_start(self, event: tk.Event) -> None:
        edge = self._get_edge(event.x, event.y)
        if not edge:
            return
        # 记录拖拽起始时的窗口几何信息和鼠标屏幕坐标
        self._drag_data = {
            "mode": "resize",
            "edge": edge,
            "start_x": event.x_root,
            "start_y": event.y_root,
            "orig_x":  self.winfo_x(),
            "orig_y":  self.winfo_y(),
            "orig_w":  self.winfo_width(),
            "orig_h":  self.winfo_height(),
        }

    def _resize_do(self, event: tk.Event) -> None:
        if self._drag_data.get("mode") != "resize":
            return

        d = self._drag_data
        dx = event.x_root - d["start_x"]
        dy = event.y_root - d["start_y"]
        edge = d["edge"]

        x, y = d["orig_x"], d["orig_y"]
        w, h = d["orig_w"], d["orig_h"]
        MIN = BORDER * 4  # 最小窗口尺寸，防止缩得太小无法操作

        # 根据拖拽的边/角方向计算新的位置和尺寸
        if "e" in edge: w = max(w + dx, MIN)
        if "s" in edge: h = max(h + dy, MIN)
        if "w" in edge:
            new_w = max(w - dx, MIN)
            x = x + (w - new_w)
            w = new_w
        if "n" in edge:
            new_h = max(h - dy, MIN)
            y = y + (h - new_h)
            h = new_h

        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_release(self, event: tk.Event) -> None:
        """鼠标释放时触发保存回调。"""
        if self._on_change_callback and self._drag_data:
            self._on_change_callback(self._region_name, self.get_rect())
        self._drag_data = {}

    # ── 坐标读取 ──────────────────────────────────────────────────────────

    def get_rect(self) -> tuple[int, int, int, int]:
        """返回当前窗口的屏幕坐标 (x1, y1, x2, y2)。"""
        x = self.winfo_x()
        y = self.winfo_y()
        return x, y, x + self.winfo_width(), y + self.winfo_height()
