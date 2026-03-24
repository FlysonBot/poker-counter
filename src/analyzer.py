"""
智能分析模块。根据出牌事件推算对手持牌，并在游戏结束时输出误差分析。
不依赖 tkinter，可独立测试。
"""

from loguru import logger

from card_types import Card, Player
from tracker import CardCounts, Counter


# 顺牌的牌面值顺序（不含2和JOKER，它们不参与顺子）
_SEQUENCE_ORDER = [
    Card.THREE, Card.FOUR, Card.FIVE, Card.SIX, Card.SEVEN,
    Card.EIGHT, Card.NINE, Card.TEN, Card.J, Card.Q, Card.K, Card.A,
]
_SEQUENCE_INDEX = {card: i for i, card in enumerate(_SEQUENCE_ORDER)}


def is_sequence(cards: CardCounts) -> bool:
    """判断出牌是否为顺子（每种牌恰好1张，牌面值连续，且至少5张）。"""
    if len(cards) < 5:
        return False
    if any(count != 1 for count in cards.values()):
        return False
    indices = sorted(_SEQUENCE_INDEX[c] for c in cards if c in _SEQUENCE_INDEX)
    if len(indices) != len(cards):
        return False  # 含有不能组成顺子的牌（2或JOKER）
    return indices == list(range(indices[0], indices[0] + len(indices)))


class Estimate:
    """单张牌对单个玩家的估算。"""
    __slots__ = ("value", "confidence")

    def __init__(self, value: int, confidence: str) -> None:
        self.value = value
        self.confidence = confidence


class Analyzer:
    """
    根据出牌事件推算对手持牌估算，并在游戏结束时输出误差分析。

    on_card_played(player, cards) -> list[(player, card, value, confidence)]
        返回需要更新的估算列表，UI 层据此调用 set_estimate()。

    on_game_end(winner) -> None
        计算并打印误差分析日志。

    reset() -> None
        清空所有估算状态。
    """

    def __init__(self, counter: Counter) -> None:
        self._counter = counter
        # 首次估算快照：{player: {card: int}}，仅记录 low confidence 的首次估算
        self._first_estimate: dict[Player, dict[Card, int]] = {
            Player.LEFT: {},
            Player.RIGHT: {},
        }

    def reset(self) -> None:
        for d in self._first_estimate.values():
            d.clear()

    def on_card_played(
        self, player: Player, cards: CardCounts
    ) -> list[tuple[Player, Card, int, str]]:
        """
        处理出牌事件，返回需要更新的估算列表。
        每项为 (target_player, card, value, confidence)。
        """
        updates: list[tuple[Player, Card, int, str]] = []
        other = Player.RIGHT if player == Player.LEFT else Player.LEFT

        for card, count in cards.items():
            remaining = self._counter.remaining[card].get()

            if remaining == 0:
                # remaining 归零：两位对手都没有了，高置信度
                for target in (Player.LEFT, Player.RIGHT):
                    updates.append((target, card, 0, "high"))
            elif player in (Player.LEFT, Player.RIGHT):
                # 出牌方打出后，另一方最多持有 remaining 张，低置信度
                updates.append((other, card, remaining, "low"))

        # 记录 low confidence 首次估算
        for target, card, value, confidence in updates:
            if confidence == "low" and card not in self._first_estimate[target]:
                self._first_estimate[target][card] = value

        return updates

    def on_game_end(self, winner: Player) -> None:
        """计算并打印误差分析。winner 为最后出完牌的玩家。"""
        if winner == Player.MIDDLE:
            logger.info("自己获胜，无法验证对手估算")
            return

        loser = Player.RIGHT if winner == Player.LEFT else Player.LEFT
        winner_played = self._counter.left if winner == Player.LEFT else self._counter.right
        loser_played = self._counter.right if winner == Player.LEFT else self._counter.left
        winner_est = self._first_estimate[winner]
        loser_est = self._first_estimate[loser]

        lines = [
            f"====== 估算误差分析（{winner.value}获胜）======",
            f"{'牌':>6}  {'胜-实':>5}  {'胜-估':>5}  {'胜-差':>5}  {'败-实':>5}  {'败-估':>5}  {'败-差':>5}",
            "-" * 52,
        ]
        w_errors, l_errors = [], []
        for card in Card:
            w_actual = winner_played[card].get()
            l_played = loser_played[card].get()
            l_actual = l_played + self._counter.remaining[card].get()

            w_est = winner_est.get(card)
            l_est = loser_est.get(card)

            w_est_str = str(w_est) if w_est is not None else "?"
            l_est_str = str(l_est) if l_est is not None else "?"
            w_err = w_actual - w_est if w_est is not None else None
            l_err = l_actual - l_est if l_est is not None else None
            w_err_str = str(w_err) if w_err is not None else "?"
            l_err_str = str(l_err) if l_err is not None else "?"

            if w_err is not None:
                w_errors.append(w_err)
            if l_err is not None:
                l_errors.append(l_err)

            lines.append(
                f"{card.value:>6}  {w_actual:>5}  {w_est_str:>5}  {w_err_str:>5}  {l_actual:>5}  {l_est_str:>5}  {l_err_str:>5}"
            )

        total = len(list(Card))
        for label, errors in [(winner.value, w_errors), (loser.value, l_errors)]:
            n = len(errors)
            coverage = f"{n}/{total}"
            if n > 0:
                mae = sum(abs(e) for e in errors) / n
                over = sum(1 for e in errors if e < 0)
                under = sum(1 for e in errors if e > 0)
                lines.append(f"{label}: 覆盖率={coverage}  MAE={mae:.2f}  高估={over}张 低估={under}张")
            else:
                lines.append(f"{label}: 覆盖率={coverage}  （无估算数据）")

        logger.info("\n" + "\n".join(lines))
