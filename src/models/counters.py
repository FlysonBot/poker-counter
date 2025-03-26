"""
牌数统计器模块，负责跟踪剩余牌和已出牌的数量。
"""

import tkinter as tk
from dataclasses import dataclass

from loguru import logger

from misc.custom_types import CardDict, CardVarDict
from misc.singleton import singleton

from .enum import Card, Player


def _create_cardvar_dict(initial_value: CardDict) -> CardVarDict:
    """根据提供的初始值字典创建一个Tkinter变量字典"""
    return {key: tk.IntVar(value=value) for key, value in initial_value.items()}


def _modify_cardvar_dict(intvar_dict: CardVarDict, new_values: CardDict) -> None:
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

    remaining_counter = _create_cardvar_dict(FULL_COUNT)
    player1_counter = _create_cardvar_dict(EMPTY_COUNT)
    player2_counter = _create_cardvar_dict(EMPTY_COUNT)

    def reset(self) -> None:
        """重置记牌器计数为初始值"""
        _modify_cardvar_dict(self.remaining_counter, FULL_COUNT)
        _modify_cardvar_dict(self.player1_counter, EMPTY_COUNT)
        _modify_cardvar_dict(self.player2_counter, EMPTY_COUNT)

    def mark(self, card: Card, player: Player) -> None:
        """标记一个牌型，并更新计数器"""
        self.remaining_counter[card].set(self.remaining_counter[card].get() - 1)

        match player:
            case Player.LEFT:
                self.player1_counter[card].set(self.player1_counter[card].get() + 1)
            case Player.RIGHT:
                self.player2_counter[card].set(self.player2_counter[card].get() + 1)
            case _:
                pass

        if self.remaining_counter[card].get() < 0:
            logger.warning(f"尝试标记不存在的牌型或已出完的牌：{card.value}")
        logger.info(f"为 {card.value} 标记牌：{self.remaining_counter[card].get()}")
