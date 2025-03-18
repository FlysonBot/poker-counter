class CardCounter:
    def __init__(self) -> None:
        # 初始化牌的数量
        self.reset()

    def reset(self) -> None:
        """重置所有牌的数量"""
        self.cards: dict[str, int] = {
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
        self.total_cards = 54

    def get_card_count(self, card) -> int:
        """获取指定牌的剩余数量"""
        return self.cards[card]

    def mark_card(self, card) -> None:
        """减少指定牌的数量"""
        if card == "JOKER":
            card = "王"
        if self.cards[card] > 0:
            self.cards[card] -= 1
            self.total_cards -= 1
