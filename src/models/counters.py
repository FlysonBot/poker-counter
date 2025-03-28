"""
牌数统计器模块，负责跟踪剩余牌和已出牌的数量。
"""

import tkinter as tk
from dataclasses import dataclass

from loguru import logger

from misc.custom_types import Card, CardIntDict, CardIntVarDict, Player
from misc.singleton import singleton


def _create_cardintvar_dict(initial_value: CardIntDict) -> CardIntVarDict:
    """根据提供的初始值字典创建一个Tkinter变量字典"""
    return {key: tk.IntVar(value=value) for key, value in initial_value.items()}


def _modify_cardvar_dict(intvar_dict: CardIntVarDict, new_values: CardIntDict) -> None:
    """根据提供的新值字典修改Tkinter变量字典"""
    for key, value in new_values.items():
        intvar_dict[key].set(value)


FULL_COUNT = {card: 4 for card in Card}
FULL_COUNT[Card.JOKER] = 2
EMPTY_COUNT = {card: 0 for card in Card}


@singleton
@dataclass
class CardCounter:
    """牌数统计器类，负责跟踪剩余牌和已出牌的数量"""

    def __post_init__(self) -> None:
        self.remaining_counter = _create_cardintvar_dict(FULL_COUNT)
        self.player1_counter = _create_cardintvar_dict(EMPTY_COUNT)
        self.player3_counter = _create_cardintvar_dict(EMPTY_COUNT)
        self.remaining_count = 54
        self.player1_count = 0
        self.player2_count = 0
        self.player3_count = 0
        logger.info("已创建记牌器计数器")

    def reset(self) -> None:
        """重置记牌器计数为初始值"""
        _modify_cardvar_dict(self.remaining_counter, FULL_COUNT)
        _modify_cardvar_dict(self.player1_counter, EMPTY_COUNT)
        _modify_cardvar_dict(self.player3_counter, EMPTY_COUNT)
        self.remaining_count = 54
        self.player1_count = 0
        self.player2_count = 0
        self.player3_count = 0
        logger.info("已重置记牌器计数")

    def mark(self, card: Card, player: Player) -> None:
        """标记一个牌型，并更新计数器"""
        self.remaining_counter[card].set(self.remaining_counter[card].get() - 1)

        match player:
            case Player.LEFT:
                self.player1_counter[card].set(self.player1_counter[card].get() + 1)
                self.player1_count += 1
            case Player.MIDDLE:
                self.player2_count += 1
            case Player.RIGHT:
                self.player3_counter[card].set(self.player3_counter[card].get() + 1)
                self.player2_count += 1

        if self.remaining_counter[card].get() < 0:
            logger.warning(
                f"尝试标记不存在的牌型或已出完的牌：{card.value}。如果是游戏马上要结束前标记的，可能是误识别，可以忽略。"
            )

        self.remaining_count -= 1
        logger.info(
            f"为{player.value}标记牌{card.value}，剩余{self.remaining_counter[card].get()}张"
        )
