class CardCounterLogic:
    def __init__(self):
        # 初始化牌的数量
        self.reset_cards()

    def mark_card(self, card):
        """减少指定牌的数量"""
        if self.cards[card] > 0:
            self.cards[card] -= 1
            return True
        return False

    def reset_cards(self):
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
            "小王": 1,
            "大王": 1,
        }

    def get_card_count(self, card):
        """获取指定牌的剩余数量"""
        return self.cards[card]

    def get_total_cards(self):
        """获取剩余牌的总数"""
        return sum(self.cards.values())

    def get_status(self):
        """获取当前所有牌的状态"""
        return "\n".join([f"{card}: {count}" for card, count in self.cards.items()])
