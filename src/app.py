from threading import Thread
import tkinter as tk

from card_counter import CardCounter
from game import game_loop


class GraphicInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("记牌器")

        # 初始化应用逻辑
        interval = 0.2
        self.counter = CardCounter()
        self.current_count = self.counter.total_cards
        game_loop(interval, self.counter)

        # 第二线程循环允许后端代码
        thread = Thread(target=game_loop, args=(interval, self.counter), daemon=True)
        thread.start()

        # 创建窗口
        self.setup_window()

        # 自动更新牌数量
        self.update_count(interval*1000)

    def setup_window(self):
        # 设置窗口透明（去掉背景）
        self.root.attributes("-transparentcolor", "white")  # 白色部分透明
        self.root.configure(bg="white")  # 窗口背景设置为白色

        # 去掉窗口边框和标题栏
        self.root.overrideredirect(True)

        # 创建表格界面
        self.create_table()

        # 绑定键盘事件
        self.root.bind("<KeyPress-q>", lambda event: self.root.destroy())  # 按 Q 键退出

        # 绑定拖动事件
        self.card_labels["3"].bind(
            "<B1-Motion>", self.move_window
        )  # 拖动第一行移动窗口

    def create_table(self):
        """创建横向表格界面"""
        self.table_frame = tk.Frame(
            self.root,
            bg="lightgray",
            bd=2,
            relief="solid",
            highlightbackground="red",
            highlightthickness=2,
        )
        self.table_frame.pack(pady=0, fill=tk.BOTH, expand=True)

        # 第一行：显示牌的名称
        self.card_labels = {}
        for i, card in enumerate(self.counter.cards):
            label = tk.Label(
                self.table_frame,
                text=card,
                font=("Arial", 12),
                width=6,
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
                font=("Arial", 12),
                width=6,
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
        self.adjust_window_size()

    def adjust_window_size(self):
        """调整窗口大小以适应表格"""
        num_columns = len(self.counter.cards)
        column_width = 61  # 每列宽度
        row_height = 28  # 每行高度
        window_width = num_columns * column_width
        window_height = 2 * row_height

        # 设置窗口大小
        self.root.geometry(f"{window_width}x{window_height}")

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
