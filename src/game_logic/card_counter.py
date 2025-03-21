"""
牌数统计器模块，负责跟踪剩余牌的数量。
"""

from logger import logger


class CardCounter:
    """
    牌数统计器类，跟踪剩余牌的数量。
    """

    INITIAL_COUNTS: dict[str, int] = {
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

    def __init__(self) -> None:
        """
        初始化记牌器，重置牌数为初始值。
        """

        self.reset()
        logger.success("记牌器初始化成功")

    def reset(self) -> None:
        """
        重置计数器，将牌数恢复为初始值。
        """

        self.counts: dict[str, int] = self.INITIAL_COUNTS.copy()
        logger.success("记牌器状态已还原")

    def mark(self, card: str) -> None:
        """
        标记已出的牌。

        :param card: 已出的牌
        """

        if card == "JOKER":
            card = "王"

        if self.counts.get(card, 0) > 0:
            self.counts[card] -= 1
            logger.debug(f"标记牌：{card} (剩余：{self.counts[card]})")

        else:
            logger.warning(f"尝试标记不存在的牌型或已出完的牌：{card}")

    def get_count(self, card: str) -> int:
        """
        获取指定牌的剩余数量。

        :param card: 牌名
        :return: 牌的剩余数量
        """
        return self.counts.get(card, 0)
