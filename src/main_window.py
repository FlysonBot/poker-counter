"""
悬浮窗组件模块，用于显示记牌器的实时信息。
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict

from config import FONT_SIZE, GUI_LOCATION
from game_logic import CardCounter, GameState
from logger import logger, open_latest_log
from misc import open_config


class MainWindow(tk.Tk):
    """
    主界面组件类，显示记牌器的实时信息。
    """

    def __init__(self, counter: CardCounter, gs: GameState) -> None:
        """
        初始化主界面组件。

        :param counter: 记牌器对象
        :param gs: 游戏状态对象
        """
        super().__init__()
        self.counter = counter
        self.gs = gs
        self._create_table()
        self._setup_window()
        self._setup_binding()
        logger.success("主界面初始化完毕")

    def _setup_window(self) -> None:
        """
        设置窗口属性，包括窗口大小、位置、背景等。
        """
        # 基本外观设置
        self.title("记牌器")
        self.attributes("-topmost", True)  # 置顶  # type: ignore
        self.overrideredirect(True)  # 去掉窗口边框
        self.configure(bg="white")  # 窗口背景设为白色
        self.attributes(  # type: ignore
            "-transparentcolor", "white"
        )  # 使白色背景变得透明

        # 设置窗口大小并读取窗口偏移量设置
        self.update_idletasks()  # 动态调整窗口大小以匹配内容大小
        initial_x_offset = GUI_LOCATION.get("OFFSET_X", None)  # 初始X偏移量
        initial_y_offset = GUI_LOCATION.get("OFFSET_Y", None)  # 初始Y偏移量
        center_x_offset = GUI_LOCATION.get("CENTER_X", None)  # 中心X偏移量
        center_y_offset = GUI_LOCATION.get("CENTER_Y", None)  # 中心Y偏移量
        window_width = self.winfo_width()  # 窗口宽度
        window_height = self.winfo_height()  # 窗口高度

        # 计算并应用窗口偏移量
        x_offset, y_offset = 0, 0  # 设置初始偏移量为0

        if initial_x_offset:
            x_offset += initial_x_offset
        elif center_x_offset:
            x_offset += center_x_offset - window_width // 2

        if initial_y_offset:
            y_offset += initial_y_offset
        elif center_y_offset:
            y_offset += center_y_offset - window_height // 2

        self.geometry(f"+{x_offset}+{y_offset}")  # 应用偏移量
        logger.info(f"窗口偏移量为：{x_offset}，{y_offset}")
        logger.info(f"窗口大小为：{window_width}，{window_height}")

        logger.success("窗口属性设置完毕")

    def _setup_binding(self) -> None:
        """
        绑定窗口拖动事件和键盘热键。
        """
        # 绑定窗口拖动事件
        self.bind("<Button-1>", self._on_drag_start)  # 鼠标左键按下  # type: ignore
        self.bind("<B1-Motion>", self._on_drag_move)  # 鼠标左键拖动  # type: ignore

        # 绑定键盘热键
        self.bind("<KeyPress-q>", lambda event: self.destroy())  # q键退出应用程序
        self.bind("<KeyPress-l>", lambda event: open_latest_log())  # l键打开日志文件
        self.bind("<KeyPress-c>", lambda event: open_config())  # c键打开配置文件
        self.bind("<KeyPress-r>", lambda event: self.gs.manual_reset())  # r键重置记牌器

        logger.success("窗口键盘和鼠标事件绑定成功")

    def _create_table(self) -> None:
        """
        创建记牌器表格，显示牌型和数量。
        """
        # 牌型显示表格
        self.table_frame = ttk.Frame(self)
        self.table_frame.pack(padx=0, pady=0)

        # 牌名标签
        self.card_labels: Dict[str, tk.Label] = {}
        for idx, card in enumerate(self.counter.INITIAL_COUNTS.keys()):
            label = tk.Label(
                self.table_frame,
                text=card,
                anchor="center",
                relief="solid",
                font=("Arial", FONT_SIZE, "bold"),
                bg="lightblue",
                fg="black",
                highlightbackground="red",
                highlightthickness=1,
                width=2,
            )
            label.grid(row=0, column=idx, padx=0, pady=0, sticky="nsew")
            self.card_labels[card] = label

        # 数量标签
        self.count_labels: Dict[str, tk.Label] = {}
        for idx, card in enumerate(self.counter.INITIAL_COUNTS.keys()):
            label = tk.Label(
                self.table_frame,
                text=str(self.counter.get_count(card)),
                anchor="center",
                relief="solid",
                font=("Arial", FONT_SIZE),
                bg="lightyellow",
                fg="black",
                highlightbackground="red",
                highlightthickness=1,
                width=2,
            )
            label.grid(row=1, column=idx, padx=0, pady=0, sticky="nsew")
            self.count_labels[card] = label

        # 设置每一列的权重，确保列宽一致
        for col in range(len(self.counter.INITIAL_COUNTS)):
            self.table_frame.grid_columnconfigure(col, weight=1)

        logger.success("窗口记牌器表格创建完毕")

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
            label.config(text=str(self.counter.get_count(card)))
        logger.trace("窗口内容更新完毕")
