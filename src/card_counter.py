class CardCounter:
    def __init__(self):
        # 初始化牌的数量
        self.reset()

    def reset(self):
        """重置所有牌的数量"""
        self.cards = {
            "3": 4,
            "4": 4,
            "5": 4,
            "6": 4,
            "7": 4,
            "8": 4,
            "9": 4,
            "10": 4,
            "J": 4,
            "Q": 4,
            "K": 4,
            "A": 4,
            "2": 4,
            "王": 2,
        }

    def get_card_count(self, card):
        """获取指定牌的剩余数量"""
        return self.cards[card]

    def mark_card(self, card):
        """减少指定牌的数量"""
        if self.cards[card] > 0:
            self.cards[card] -= 1

