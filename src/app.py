import tkinter as tk
from threading import Thread

from classes.card_counter import CardCounter
from config import SCREENSHOT_INTERVAL, GUI_UPDATE_INTERVAL, GUI_LOCATION, FONT_SIZE
from logic import backend_logic

GUI_UPDATE_INTERVAL = int(GUI_UPDATE_INTERVAL * 1000)  # 转换为整数毫秒


class GraphicInterface:
    def __init__(self, root) -> None:
        self.root = root
        self.root.title("记牌器")

        # 初始化应用逻辑
        self.counter = CardCounter()
        self.current_count = self.counter.total_cards

        # 第二线程循环允许后端代码
        thread = Thread(
            target=backend_logic, args=(self.counter), daemon=True
        )
        thread.start()

        # 创建窗口
        self.setup_window()

        # 自动更新牌数量
        self.update_count()

    def setup_window(self) -> None:
        # 初始化窗口拖动偏移变量
        self.offset_x = GUI_LOCATION.get("OFFSET_X", 0)
        self.offset_y = GUI_LOCATION.get("OFFSET_Y", 0)

        # 设置窗口完全透明
        self.root.configure(bg="white")  # 窗口背景设置为白色
        self.root.attributes("-transparentcolor", "white")  # 使白色部分透明
        self.root.attributes("-topmost", True)  # 置顶

        # 去掉窗口边框和标题栏
        self.root.overrideredirect(True)

        # 创建表格界面
        self.create_table()

        # 调整窗口大小和位置（在程序界面中居中，并放到屏幕下方）
        self.root.update_idletasks()  # 动态调整窗口大小以匹配内容大小
        x_offset: int = self.root.winfo_width() // 2  # 获取窗口宽度的一半
        y_offset: int = self.root.winfo_height() // 2  # 获取窗口高度的一半
        x_offset += GUI_LOCATION.get("CENTER_X", -x_offset)  # 加上置中坐标或设为0
        y_offset += GUI_LOCATION.get("CENTER_Y", -y_offset)  # 加上置中坐标或设为0
        self.root.geometry(f"+{x_offset}+{y_offset}")

        # 绑定键盘事件
        self.root.bind("<KeyPress-q>", lambda event: self.root.destroy())  # 按 Q 键退出

        # 绑定拖动事件到整个表格框架
        self.table_frame.bind("<Button-1>", self.on_drag_start)
        self.table_frame.bind("<B1-Motion>", self.move_window)

    def create_table(self) -> None:
        """创建横向表格界面"""
        self.table_frame = tk.Frame(
            self.root,
            bg="lightgray",
            bd=2,
            relief="solid",
            highlightbackground="red",
            highlightthickness=0,
        )
        self.table_frame.pack(pady=0, fill=tk.BOTH, expand=True)

        # 第一行：显示牌的名称
        self.card_labels = {}
        for i, card in enumerate(self.counter.cards):
            label = tk.Label(
                self.table_frame,
                text=card,
                font=("Arial", FONT_SIZE),
                width=2,
                relief="solid",
                borderwidth=1,
                bg="lightblue",
                fg="black",
                highlightbackground="red",
                highlightthickness=1,
            )
            label.grid(row=0, column=i, padx=0, pady=0, sticky="nsew")
            self.card_labels[card] = label

        # 第二行：显示剩余数量，并支持单击
        self.count_labels = {}
        for i, card in enumerate(self.counter.cards):
            label = tk.Label(
                self.table_frame,
                text=self.counter.get_card_count(card),
                font=("Arial", FONT_SIZE),
                width=2,
                relief="solid",
                borderwidth=1,
                bg="lightyellow",
                fg="black",
                highlightbackground="red",
                highlightthickness=1,
            )
            label.grid(row=1, column=i, padx=0, pady=0, sticky="nsew")
            self.count_labels[card] = label

        # 动态调整窗口大小
        self.root.update_idletasks()

    def move_window(self, event) -> None:
        """拖动窗口"""
        x: int = self.root.winfo_pointerx() - self.offset_x
        y: int = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    def on_drag_start(self, event) -> None:
        """记录拖动起始位置"""
        self.offset_x: int = event.x
        self.offset_y: int = event.y

    def update_count(self) -> None:
        """更新牌数量显示"""
        if self.current_count != self.counter.total_cards:
            self.current_count: int = self.counter.total_cards

            # 更新剩余牌数量显示
            for card in self.counter.cards:
                count: int = self.counter.get_card_count(card)
                self.count_labels[card].config(text=str(count))

        self.root.after(GUI_UPDATE_INTERVAL, self.update_count)
