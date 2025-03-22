"""
悬浮窗组件模块，用于显示记牌器的实时信息。
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional

from config import GUI
from game_logic import CardCounter, GameState
from logger import logger, open_latest_log
from misc.open_file import open_config
from misc.windows_offset import calculate_offset

from .windows_type import WindowsType


class CounterWindow(tk.Toplevel):
    """
    记牌器窗口基类，可用于创建主窗口和玩家窗口。
    """

    def __init__(
        self,
        counter: CardCounter,
        gs: GameState,
        window_type: WindowsType,
        parent: Optional[tk.Tk] = None,
    ) -> None:
        """
        初始化记牌器窗口。

        :param counter: 记牌器对象
        :param gs: 游戏状态对象
        :param window_type: 窗口类型 (main, left, right)
        :param parent: 父窗口（可选，如不提供则新建为父窗口）
        """
        super().__init__(parent) if parent else super().__init__()

        self.parent = parent
        self.counter = counter
        self.gs = gs
        self.window_type = window_type

        get_count: dict[str, Callable[[str], int]] = {
            "MAIN": lambda card: self.counter.get_remaining_count(card),
            "LEFT": lambda card: self.counter.get_player_count(card, "left"),
            "RIGHT": lambda card: self.counter.get_player_count(card, "right"),
        }
        self._get_count_text = get_count[self.window_type.name]

        self._create_table()  # 创建表格（先创建表格后创建窗口以动态调整窗口大小）
        self._setup_window()  # 设置窗口属性
        self._setup_binding()  # 绑定窗口拖动事件

        logger.success(f"{window_type.value}窗口初始化完毕")

    def _setup_window(self) -> None:
        """
        设置窗口属性，包括窗口大小、位置、背景等。
        """

        # 基本外观设置
        self.title(f"记牌器-{self.window_type.value}")
        self.attributes("-topmost", True)  # 置顶  # type: ignore
        self.overrideredirect(True)  # 去掉窗口边框
        self.configure(bg="white")  # 窗口背景设为白色
        self.attributes(  # type: ignore
            "-transparentcolor", "white"
        )  # 使白色背景变得透明

        # 设置窗口大小并读取窗口偏移量设置
        self.update_idletasks()  # 动态调整窗口大小以匹配内容大小

        # 根据窗口透明度设置透明度
        self.attributes("-alpha", GUI.get(self.window_type.name, {}).get("OPACITY", 1))  # type: ignore

        # 根据窗口类型获取不同的位置配置
        location_config = GUI.get(self.window_type.name, {})
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        x_offset, y_offset = calculate_offset(
            window_width,
            window_height,
            location_config.get("OFFSET_X", None),
            location_config.get("OFFSET_Y", None),
            location_config.get("CENTER_X", None),
            location_config.get("CENTER_Y", None),
        )

        self.geometry(f"+{x_offset}+{y_offset}")  # 应用偏移量
        logger.info(f"{self.window_type.value}窗口偏移量为：{x_offset}，{y_offset}")
        logger.info(
            f"{self.window_type.value}窗口大小为：{window_width}x{window_height}"
        )

        logger.success(f"{self.window_type.value}窗口属性设置完毕")

    def _setup_binding(self) -> None:
        """
        绑定窗口拖动事件和键盘热键。
        """

        # 绑定窗口拖动事件
        self.bind("<Button-1>", self._on_drag_start)  # 鼠标左键按下  # type: ignore
        self.bind("<B1-Motion>", self._on_drag_move)  # 鼠标左键拖动  # type: ignore

        # 绑定键盘热键
        self.bind("<KeyPress-q>", lambda event: self.destroy_all())  # q键退出应用程序
        self.bind("<KeyPress-l>", lambda event: open_latest_log())  # l键打开日志文件
        self.bind("<KeyPress-c>", lambda event: open_config())  # c键打开配置文件
        self.bind("<KeyPress-r>", lambda event: self.gs.manual_reset())  # r键重置记牌器

        logger.success(f"{self.window_type.value}窗口键盘和鼠标事件绑定成功")

    def destroy_all(self) -> None:
        """
        摧毁所有窗口（包括开关窗口），并退出程序。
        """

        if self.parent is not None:
            if hasattr(self.parent, "destroy_all"):
                return self.parent.destroy_all()  # type: ignore
            return self.parent.destroy()

        return self.destroy()  # 销毁当前窗口及其子窗口

    def _create_table(self) -> None:
        """
        创建记牌器表格，显示牌型和数量。
        """

        # 牌型显示表格
        self.table_frame = ttk.Frame(self)

        # 根据窗口类型决定表格方向
        if self.window_type == WindowsType.MAIN:
            self.table_frame.pack(padx=0, pady=0)
            rows, cols = 2, len(self.counter.KEYS)  # 水平布局
        else:
            self.table_frame.pack(padx=0, pady=0, fill="both", expand=True)
            rows, cols = len(self.counter.KEYS), 2  # 垂直布局

        # 初始化标签
        self.card_labels: Dict[str, tk.Label] = {}  # 牌名标签
        self.count_labels: Dict[str, tk.Label] = {}  # 数量标签
        FONT_SIZE = GUI.get(self.window_type.name, {}).get("FONT_SIZE", 25)

        for idx, card in enumerate(self.counter.KEYS):
            # 创建牌名标签
            card_label = tk.Label(
                self.table_frame,
                text=card,
                anchor="center",
                relief="solid",
                font=("Arial", FONT_SIZE),
                bg="lightblue",
                fg="black",
                highlightbackground="red",
                highlightthickness=1,
                width=2,
            )

            # 创建数量标签
            count_label = tk.Label(
                self.table_frame,
                text=self._get_count_text(card),
                anchor="center",
                relief="solid",
                font=("Arial", FONT_SIZE, "bold"),
                bg="lightyellow",
                fg="black",
                highlightbackground="red",
                highlightthickness=1,
                width=2,
            )

            # 根据窗口类型放置标签
            if self.window_type == WindowsType.MAIN:
                card_label.grid(row=0, column=idx, padx=0, pady=0, sticky="nsew")
                count_label.grid(row=1, column=idx, padx=0, pady=0, sticky="nsew")
            else:
                card_label.grid(row=idx, column=0, padx=0, pady=0, sticky="nsew")
                count_label.grid(row=idx, column=1, padx=0, pady=0, sticky="nsew")

            self.card_labels[card] = card_label
            self.count_labels[card] = count_label

        # 设置网格权重，确保列宽/行高一致
        for i in range(rows):
            self.table_frame.grid_rowconfigure(i, weight=1)
        for j in range(cols):
            self.table_frame.grid_columnconfigure(j, weight=1)

        logger.success(f"{self.window_type.value}窗口记牌器表格创建完毕")

    def _on_drag_start(self, event: tk.Event) -> None:  # type: ignore
        """
        记录拖动起始位置。

        :param event: 鼠标事件
        """

        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_move(self, event: tk.Event) -> None:  # type: ignore
        """
        处理窗口拖动。

        :param event: 鼠标事件
        """

        x = self.winfo_x() + (event.x - self._drag_start_x)
        y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{x}+{y}")

    def update_display(self) -> None:
        """
        更新窗口的显示内容。
        """

        for card, label in self.count_labels.items():
            # 仅在标签存在时更新标签，避免窗口关闭后尝试更新标签
            if label.winfo_exists():
                count = self._get_count_text(card)
                label.config(text=str(count))

                if self.window_type != WindowsType.MAIN:
                    if count > 1:
                        label.config(fg="red")
                    else:
                        label.config(fg="black")

        logger.trace(f"{self.window_type.value}窗口内容更新完毕")
