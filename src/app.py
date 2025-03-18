import tkinter as tk
from threading import Thread

from classes.card_counter import CardCounter
from logic import backend_logic


class GraphicInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("记牌器")

        # 初始化应用逻辑
        interval = 0.2
        self.counter = CardCounter()
        self.current_count = self.counter.total_cards

        # 第二线程循环允许后端代码
        thread = Thread(
            target=backend_logic, args=(interval, self.counter), daemon=True
        )
        thread.start()

        # 创建窗口
        self.setup_window()

        # 自动更新牌数量
        self.update_count(int(interval * 1000))

    def setup_window(self):
        # 初始化窗口拖动偏移变量
        self.offset_x = 0
        self.offset_y = 0

        # 设置窗口完全透明
        self.root.configure(bg="white")  # 窗口背景设置为白色
        self.root.attributes("-transparentcolor", "white")  # 使白色部分透明
        self.root.attributes("-topmost", True)  # 置顶

        # 去掉窗口边框和标题栏
        self.root.overrideredirect(True)

        # 创建表格界面
        self.create_table()

        # 调整窗口大小和位置（在程序界面中居中，并放到屏幕下方）
        self.root.update_idletasks()
        width, height = self.root.winfo_width(), self.root.winfo_height()
        self.root.geometry(f"+{700 - width // 2}+{1050 - height}")

        # 绑定键盘事件
        self.root.bind("<KeyPress-q>", lambda event: self.root.destroy())  # 按 Q 键退出

        # 绑定拖动事件到整个表格框架
        self.table_frame.bind("<Button-1>", self.on_drag_start)
        self.table_frame.bind("<B1-Motion>", self.move_window)

    def create_table(self):
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
                font=("Arial", 25),
                width=3,
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
                font=("Arial", 25),
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

        # 调整窗口大小
        self.root.update_idletasks()

    def move_window(self, event):
        """拖动窗口"""
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    def on_drag_start(self, event):
        """记录拖动起始位置"""
        self.offset_x = event.x
        self.offset_y = event.y

    def update_count(self, interval):
        """更新牌数量显示"""
        if self.current_count != self.counter.total_cards:
            self.current_count = self.counter.total_cards

            # 更新剩余牌数量显示
            for card in self.counter.cards:
                count = self.counter.get_card_count(card)
                self.count_labels[card].config(text=str(count))

        self.root.after(interval, self.update_count, interval)
