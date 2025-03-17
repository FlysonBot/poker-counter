import tkinter as tk
from tkinter import messagebox

from counter import CardCounterLogic


class CardCounterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("记牌器")

        # 初始化应用逻辑
        self.logic = CardCounterLogic()

        # 创建标题
        self.title_label = tk.Label(root, text="记牌器", font=("Arial", 16))
        self.title_label.pack(pady=10)

        # 创建牌区显示
        self.card_frame = tk.Frame(root)
        self.card_frame.pack(pady=10)

        self.card_buttons = {}
        for card in self.logic.cards:
            button = tk.Button(
                self.card_frame,
                text=f"{card}\n{self.logic.get_card_count(card)}",
                width=5,
                height=2,
                command=lambda c=card: self.mark_card(c),
            )
            button.grid(
                row=(list(self.logic.cards.keys()).index(card) // 5),
                column=(list(self.logic.cards.keys()).index(card) % 5),
                padx=5,
                pady=5,
            )
            self.card_buttons[card] = button

        # 创建控制按钮
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10)

        self.reset_button = tk.Button(
            self.control_frame, text="重置", command=self.reset_cards
        )
        self.reset_button.grid(row=0, column=0, padx=5)

        self.show_status_button = tk.Button(
            self.control_frame, text="显示状态", command=self.show_status
        )
        self.show_status_button.grid(row=0, column=1, padx=5)

        # 创建状态栏
        self.status_label = tk.Label(
            root, text=f"剩余牌数: {self.logic.get_total_cards()}", font=("Arial", 12)
        )
        self.status_label.pack(pady=10)

    def mark_card(self, card):
        """处理记牌逻辑"""
        if self.logic.mark_card(card):
            self.card_buttons[card].config(
                text=f"{card}\n{self.logic.get_card_count(card)}"
            )
            self.update_status()
        else:
            messagebox.showinfo("提示", f"没有剩余的 {card} 了！")

    def reset_cards(self):
        """重置所有牌的数量"""
        self.logic.reset_cards()
        for card in self.logic.cards:
            self.card_buttons[card].config(
                text=f"{card}\n{self.logic.get_card_count(card)}"
            )
        self.update_status()
        messagebox.showinfo("提示", "牌已重置！")

    def show_status(self):
        """显示当前所有牌的状态"""
        status = self.logic.get_status()
        messagebox.showinfo("当前状态", status)

    def update_status(self):
        """更新状态栏"""
        total = self.logic.get_total_cards()
        self.status_label.config(text=f"剩余牌数: {total}")
