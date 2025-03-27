"""
记牌器悬浮窗模块，用于显示记牌器的实时信息。
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict

from functions.windows_offset import calculate_offset
from misc.custom_types import Card, ConfigDict, WindowsType
from misc.logger import logger, open_latest_log
from misc.open_file import open_config
from models.config import GUI
from models.counters import CardCounter
from models.labels import LabelProperties


class CounterWindow(tk.Toplevel):
    """
    记牌器窗口基类，可用于创建主窗口和玩家窗口。
    """

    def __init__(
        self,
        window_type: WindowsType,
        parent: tk.Tk,
    ) -> None:
        """初始化记牌器窗口。
        :param window_type: 窗口类型 (main, left, right)
        :param parent: 父窗口
        """
        super().__init__(parent) if parent else super().__init__()

        self.PARENT = parent
        self.WINDOW_TYPE = window_type

        config = GUI.get(self.WINDOW_TYPE.name, {})

        self._create_table()  # 需要先创建表格才能正确地获取窗口大小
        self._bind_label_style()
        self._setup_window_style(config)
        self._setup_window_position(config)
        self._setup_binding()

        logger.success(f"{window_type.value}窗口初始化完毕")

    def _setup_window_style(self, config: ConfigDict) -> None:
        """设置窗口样式"""
        self.title(f"记牌器-{self.WINDOW_TYPE.value}")
        self.attributes("-topmost", True)  # 置顶  # type: ignore
        self.overrideredirect(True)  # 去掉窗口边框
        self.configure(bg="white")  # 窗口背景设为白色
        self.attributes(  # type: ignore
            "-transparentcolor", "white"
        )  # 使白色背景变得透明
        self.attributes(  # type: ignore
            "-alpha", config.get("OPACITY", 1)
        )  # 设置透明度

    def _setup_window_position(self, config: ConfigDict) -> None:
        """设置窗口偏移量"""
        self.update_idletasks()  # 刷新窗口大小

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        x_offset, y_offset = calculate_offset(
            window_width,
            window_height,
            config.get("OFFSET_X", None),
            config.get("OFFSET_Y", None),
            config.get("CENTER_X", None),
            config.get("CENTER_Y", None),
        )

        window_name = self.WINDOW_TYPE.value
        self.geometry(f"+{x_offset}+{y_offset}")  # 应用偏移量
        logger.info(f"{window_name}窗口偏移量为：{x_offset}，{y_offset}")
        logger.info(f"{window_name}窗口大小为：{window_width}x{window_height}")

        logger.success(f"{window_name}窗口属性设置完毕")

    def _setup_binding(self) -> None:
        """绑定窗口拖动事件和键盘热键"""
        self.bind("<Button-1>", self._on_drag_start)  # 鼠标左键按下  # type: ignore
        self.bind("<B1-Motion>", self._on_drag_move)  # 鼠标左键拖动  # type: ignore

        self.bind(
            "<KeyPress-q>", lambda event: self.PARENT.destroy()
        )  # q键退出应用程序
        self.bind("<KeyPress-l>", lambda event: open_latest_log())  # l键打开日志文件
        self.bind("<KeyPress-c>", lambda event: open_config())  # c键打开配置文件

        logger.success(f"{self.WINDOW_TYPE.value}窗口键盘和鼠标事件绑定成功")

    def _create_table(self) -> None:
        """创建记牌器表格，显示牌型和数量"""
        self._table_frame = ttk.Frame(self)

        # 根据窗口类型决定表格方向
        if self.WINDOW_TYPE == WindowsType.MAIN:
            self._table_frame.pack(padx=0, pady=0)
            rows, cols = 2, len(Card)  # 水平布局
        else:
            self._table_frame.pack(padx=0, pady=0, fill="both", expand=True)
            rows, cols = len(Card), 2  # 垂直布局

        # 获取牌数的函数
        counter = CardCounter()  # 获取全局记牌器实例
        get_count: dict[WindowsType, Callable[[Card], tk.Variable]] = {
            WindowsType.MAIN: lambda card: counter.remaining_counter[card],
            WindowsType.LEFT: lambda card: counter.player1_counter[card],
            WindowsType.RIGHT: lambda card: counter.player3_counter[card],
        }
        get_count_text = get_count[self.WINDOW_TYPE]

        # 初始化标签
        self._card_labels: Dict[Card, tk.Label] = {}  # 牌名标签
        self._count_labels: Dict[Card, tk.Label] = {}  # 数量标签
        FONT_SIZE = GUI.get(self.WINDOW_TYPE.name, {}).get("FONT_SIZE", 25)

        # 创建标签
        def create_label(**kwargs: Any) -> tk.Label:
            return tk.Label(
                self._table_frame,
                anchor="center",
                relief="solid",
                highlightbackground="red",
                highlightthickness=1,
                width=2,
                **kwargs,
            )

        for idx, card in enumerate(Card):
            label_text = card.value if card.value != "JOKER" else "王"
            card_label = create_label(
                text=label_text, font=("Arial", FONT_SIZE), bg="lightblue", fg="black"
            )
            count_label = create_label(
                textvariable=get_count_text(card),
                font=("Arial", FONT_SIZE, "bold"),
                bg="lightyellow",
                fg="black",
            )

            # 根据窗口类型放置标签
            if self.WINDOW_TYPE == WindowsType.MAIN:
                card_label.grid(row=0, column=idx, padx=0, pady=0, sticky="nsew")
                count_label.grid(row=1, column=idx, padx=0, pady=0, sticky="nsew")
            else:
                card_label.grid(row=idx, column=0, padx=0, pady=0, sticky="nsew")
                count_label.grid(row=idx, column=1, padx=0, pady=0, sticky="nsew")

            self._card_labels[card] = card_label
            self._count_labels[card] = count_label

        # 设置网格权重，确保列宽/行高一致
        for i in range(rows):
            self._table_frame.grid_rowconfigure(i, weight=1)
        for j in range(cols):
            self._table_frame.grid_columnconfigure(j, weight=1)

        logger.success(f"{self.WINDOW_TYPE.value}窗口记牌器表格创建完毕")

    def _bind_label_style(self) -> None:
        """绑定标签样式更新函数到标签样式变量类"""
        label_properties = LabelProperties()
        for card, label in self._count_labels.items():
            label_properties.text_color.bind_callback(
                self.WINDOW_TYPE,
                card,
                lambda style, label=label: (label.config(fg=style), None)[1],
            )

    def _on_drag_start(self, event: tk.Event) -> None:  # type: ignore
        """记录拖动起始位置。
        :param event: 鼠标事件
        """
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_move(self, event: tk.Event) -> None:  # type: ignore
        """处理窗口拖动。
        :param event: 鼠标事件
        """

        x = self.winfo_x() + (event.x - self._drag_start_x)
        y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{x}+{y}")
