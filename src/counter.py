"""
计数状态模块。维护一局游戏中各牌的剩余数量和各玩家出牌数，并在游戏结束时进行合法性校验。
"""

import tkinter as tk
from typing import TYPE_CHECKING

from loguru import logger

from card_types import Card, Player

CardCounts = dict[Card, int]

# 一副完整的牌：除大小王各1张外，其余每种牌4张
FULL_DECK: CardCounts = {**{card: 4 for card in Card}, Card.JOKER: 2}


class Counter:
    """维护剩余牌数和各玩家出牌数的 Tkinter 变量。
    使用 tk.IntVar 而不是普通 int，是因为 UI 标签通过 textvariable 绑定到这些变量，
    变量一旦更新，标签会自动刷新，无需手动通知 UI。
    """

    def __init__(self) -> None:
        self.remaining: dict[Card, tk.IntVar] = {
            card: tk.IntVar(value=v) for card, v in FULL_DECK.items()
        }
        self.left: dict[Card, tk.IntVar] = {card: tk.IntVar(value=0) for card in Card}
        self.right: dict[Card, tk.IntVar] = {card: tk.IntVar(value=0) for card in Card}
        # 各玩家总出牌张数（纯计数，不需要绑定 UI，用普通 int 即可）
        self.total_played = {Player.LEFT: 0, Player.MIDDLE: 0, Player.RIGHT: 0}

    def reset(self) -> None:
        for card in Card:
            self.remaining[card].set(FULL_DECK[card])
            self.left[card].set(0)
            self.right[card].set(0)
        self.total_played = {p: 0 for p in Player}

    def mark(self, card: Card, player: Player, count: int = 1, affect_remaining: bool = True) -> None:
        if affect_remaining:
            new_val = self.remaining[card].get() - count
            if new_val < 0:
                logger.warning(f"剩余 {card.value} 数量变为负数，可能有误识别")
            self.remaining[card].set(new_val)
        else:
            new_val = self.remaining[card].get()

        if player == Player.LEFT:
            self.left[card].set(self.left[card].get() + count)
        elif player == Player.RIGHT:
            self.right[card].set(self.right[card].get() + count)

        self.total_played[player] += count
        logger.info(f"{player.value} 出了 {count} 张 {card.value}，剩余 {new_val}")

    @property
    def total_remaining(self) -> int:
        return sum(v.get() for v in self.remaining.values())


def verify_counts(counter: Counter, landlord: Player, last_player: Player) -> None:
    """游戏结束时检查计数是否在合法范围内，异常情况记录 warning。"""
    logger.info("开始游戏结束自检")
    remaining = counter.total_remaining

    # 游戏结束时至少还有 2 张底牌，最多只出了地主的 17 张（54-17=37）
    if remaining > 37:
        logger.warning(f"结束时剩余 {remaining} 张，超过 37，可能有牌未被识别")
    elif remaining < 2:
        logger.warning(f"结束时剩余 {remaining} 张，少于 2，可能有牌被重复识别")

    # 检查每种牌的剩余数量是否合法
    for card in Card:
        val = counter.remaining[card].get()
        max_val = FULL_DECK[card]
        if val < 0:
            logger.warning(f"剩余 {card.value} 为 {val}，小于 0")
        elif val > max_val:
            logger.warning(f"剩余 {card.value} 为 {val}，超过 {max_val}")

    # 检查各玩家出牌总数是否符合斗地主规则
    # 获胜方必须打完所有手牌（地主 20 张，农民 17 张）
    winner = last_player
    for player in Player:
        played = counter.total_played[player]
        is_landlord = player == landlord
        max_hand = 20 if is_landlord else 17
        if player == winner:
            if played < max_hand:
                logger.warning(
                    f"{player.value} 获胜但只记录了 {played} 张（应为 {max_hand}）"
                )
            elif played > max_hand:
                logger.warning(
                    f"{player.value} 获胜但记录了 {played} 张（超过 {max_hand}）"
                )
        else:
            if played > max_hand - 1:
                logger.warning(
                    f"{player.value} 未获胜但记录了 {played} 张（超过上限 {max_hand - 1}）"
                )

    logger.info("自检完毕")
