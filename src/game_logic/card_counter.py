"""
牌数统计器模块，负责跟踪剩余牌的数量。
"""

from logger import logger

from .simple_counter import SimpleCounter


class CardCounter:
    """
    牌数统计器类，跟踪剩余牌的数量。
    """

    KEYS = {"3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "2", "王"}
    FULL_COUNTS = {key: 4 for key in KEYS}
    FULL_COUNTS["王"] = 2
    EMPTY_COUNTS = {key: 0 for key in KEYS}

    def __init__(self) -> None:
        """
        初始化记牌器，重置牌数为初始值。
        """

        self.remaining_counter = SimpleCounter(self.FULL_COUNTS, lambda x: x - 1)

        self.player_counters: dict[str, SimpleCounter] = {
            "left": SimpleCounter(self.FULL_COUNTS, lambda x: x - 1),
            "right": SimpleCounter(self.FULL_COUNTS, lambda x: x - 1),
        }

        logger.success("记牌器初始化成功")

    def reset(self) -> None:
        """
        重置计数器，将牌数恢复为初始值。
        """

        self.remaining_counter.reset()
        self.player_counters["left"].reset()
        self.player_counters["right"].reset()

        logger.success("记牌器状态已还原")

    def mark(self, card: str, player: str) -> None:
        """
        标记已出的牌。

        :param card: 已出的牌
        """

        if card == "JOKER":
            card = "王"

        self.remaining_counter.count(card)
        if player != "myself":
            self.player_counters[player].count(card)

        logger.debug(
            f"为 {player} 标记牌：{card} (剩余：{self.remaining_counter.get_count(card)})"
        )

    def get_remaining_count(self, card: str) -> int:
        """
        获取指定牌的剩余数量。

        :param card: 牌名
        :return: 牌的剩余数量
        """

        return self.remaining_counter.get_count(card)

    def get_player_count(self, card: str, player: str) -> int:
        """
        获取指定牌的指定玩家的计数。

        :param card: 牌名
        :param player: 玩家名
        :return: 牌的指定玩家的计数
        """

        return self.player_counters[player].get_count(card)
