"""
游戏结束自检模块，负责检查游戏结束时记牌器记录的数值是否合法（是否在合法范围内）。
"""

from loguru import logger

from misc.custom_types import Card, Player
from models.counters import CardCounter


class GameEndExamination:
    """游戏结束自检类，用于检查游戏结束时记牌器记录的数值是否合法（是否在合法范围内）"""

    def __init__(self, landlord: Player, winner: Player) -> None:
        self._landlord = landlord
        self._winner = winner
        self._counter = CardCounter()

        self._check()

    def _check(self) -> None:
        """游戏结束时进行自检"""
        logger.info("游戏结束，开始自检")

        self._check_total_remaining()
        self._check_individual_remaining()
        self._calc_played_range()
        self._check_total_played()
        self._check_individual_played()

        logger.info("自检完毕")

    def _check_total_remaining(self) -> None:
        """检查总剩余牌数是否合法（是否在合法范围内）"""
        if self._counter.remaining_count >= 37:  # 游戏结束时不可能有多过 54-17=37 张牌
            logger.warning(
                f"游戏结束时总剩余牌数为{self._counter.remaining_count}，高于37张。游戏过程中可能有牌没有被识别到。"
            )
        elif self._counter.remaining_count <= 2:  # 游戏结束时至少还剩下 2 张牌
            logger.warning(
                f"游戏结束时总剩余牌数为{self._counter.remaining_count}，低于2张。游戏过程中可能有牌被意外多次识别。"
            )

    def _check_individual_remaining(self) -> None:
        """检查总记牌器中每个牌的剩余数量是否合法（是否在合法范围内）"""
        for card in Card:
            if self._counter.remaining_counter[card].get() < 0:
                logger.warning(f"剩余{card.value}张{card.value}，少于0张。")
            elif self._counter.remaining_counter[card].get() > 4:
                logger.warning(f"剩余{card.value}张{card.value}，超过4张。")

    def _calc_played_range(self) -> None:
        """计算不同玩家最小出牌数和最大出牌数"""
        min_count: dict[Player, int] = {}
        for player in Player:
            if player is self._winner:
                min_count[player] = 20 if player is self._landlord else 17
            else:
                min_count[player] = 0
        self._player_min_count = min_count

        max_count: dict[Player, int] = {}
        for player in Player:
            if player is self._winner:
                max_count[player] = min_count[player]
            else:
                max_count[player] = 19 if player is self._landlord else 16
        self._player_max_count = max_count

    def _check_total_played(self) -> None:
        """检查每个玩家的总出牌数是否合法（是否在合法范围内）"""
        player_list = [Player.LEFT, Player.MIDDLE, Player.RIGHT]
        sub_counters = [
            self._counter.player1_count,
            self._counter.player2_count,
            self._counter.player3_count,
        ]

        winner_under_count = lambda s1, s2: logger.warning(  # type: ignore  # noqa: E731
            f"{s1}获胜，但只检测到{s2}张牌。游戏过程中可能有牌没有被识别到。"
        )
        winner_over_count = lambda s1, s2: logger.warning(  # type: ignore  # noqa: E731
            f"{s1}获胜，但检测到{s2}了张牌。游戏过程中可能有牌被多次识别。"
        )
        other_under_count = lambda s1, s2, s3: logger.warning(  # type: ignore  # noqa: E731
            f"{s1}出了{s2}张牌，低于{s3}张牌。记牌器计数出错。"
        )
        other_over_count = lambda s1, s2, s3: logger.warning(  # type: ignore  # noqa: E731
            f"{s1}出了{s2}张牌，多于其所有的{s3}张牌。游戏过程中可能有牌被多次识别。"
        )

        for player, count in zip(player_list, sub_counters):
            if player is self._winner:
                if count < self._player_min_count[player]:
                    winner_under_count(player.value, count)
                elif count > self._player_max_count[player]:
                    winner_over_count(player.value, count)
            elif count < self._player_min_count[player]:
                other_under_count(
                    player.value, count, self._player_min_count[player]
                )
            elif count > self._player_max_count[player]:
                other_over_count(
                    player.value, count, self._player_max_count[player]
                )

    def _check_individual_played(self) -> None:
        """检查每个玩家的单独牌数是否合法（是否在合法范围内）"""
        players = [Player.LEFT, Player.RIGHT]
        counters = [
            self._counter.player1_counter,
            self._counter.player3_counter,
        ]
        for player, counter in zip(players, counters):
            for card in Card:
                if counter[card].get() < 0:
                    logger.warning(
                        f"{player.value}记牌器中记录了{card.value}张{card.value}，少于0张。"
                    )
                elif counter[card].get() > 4:
                    logger.warning(
                        f"{player.value}记牌器中记录了{card.value}张{card.value}，超过4张。"
                    )

    def _verity_total_sum(self) -> None:
        """检查总牌数减去各玩家的出牌数是否等于剩余牌数"""
        total = (
            self._counter.player1_count
            + self._counter.player2_count
            + self._counter.player3_count
        )
        if total != 54 - self._counter.remaining_count:
            logger.warning(
                f"54减去玩家出牌数总和{total}与剩余牌数{self._counter.remaining_count}不等。"
            )
