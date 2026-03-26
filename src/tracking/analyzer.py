"""
智能分析模块。根据出牌事件推算对手持牌，并在游戏结束时输出误差分析。
不依赖 tkinter，可独立测试。
"""

from loguru import logger

from card_types import Card, Player
from tracking.counter import CardCounts, Counter

# 每条规则方法的 updates 参数类型：每项为 (目标玩家, 牌, 估算剩余张数, 置信度)
UpdateList = list[tuple[Player, Card, int, str]]

# 顺牌的牌面值顺序（不含2和JOKER，它们不参与顺子）
_SEQUENCE_ORDER = [
    Card.THREE,
    Card.FOUR,
    Card.FIVE,
    Card.SIX,
    Card.SEVEN,
    Card.EIGHT,
    Card.NINE,
    Card.TEN,
    Card.J,
    Card.Q,
    Card.K,
    Card.A,
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
    每条推算规则是独立的方法，自行决定更新哪些估算以及是否记录到误差分析快照。
    """

    def __init__(self, counter: Counter) -> None:
        self._counter = counter
        # 误差分析快照：每张牌对每位玩家的估算总持牌数，None 表示无法推算
        self._estimated_total: dict[Player, dict[Card, int]] = {
            Player.LEFT: {},
            Player.RIGHT: {},
        }

    def reset(self) -> None:
        for d in self._estimated_total.values():
            d.clear()

    def _record_total(self, player: Player, card: Card, value: int) -> None:
        """记录首次推算出的总持牌数，供游戏结束时误差分析使用。只记录首次。"""
        if card not in self._estimated_total[player]:
            self._estimated_total[player][card] = value

    def on_card_played(self, player: Player, cards: CardCounts) -> UpdateList:
        """处理出牌事件，返回需要更新的估算列表，每项为 (target_player, card, value, confidence)。"""
        updates: UpdateList = []

        for card in cards:
            remaining = self._counter.remaining[card].get()
            self._rule_both_have_none(card, remaining, updates)
            self._rule_other_has_all_remaining(player, card, remaining, cards, updates)
            self._rule_player_played_all_their_cards(
                player, card, remaining, cards, updates
            )

        return updates

    def _rule_both_have_none(
        self, card: Card, remaining: int, updates: UpdateList
    ) -> None:
        """remaining 归零时：两位对手都确定没有这张牌了，高置信度。"""
        if remaining != 0:
            return
        for target in (Player.LEFT, Player.RIGHT):
            updates.append((target, card, 0, "high"))

    def _rule_other_has_all_remaining(
        self,
        player: Player,
        card: Card,
        remaining: int,
        cards: CardCounts,
        updates: UpdateList,
    ) -> None:
        """某玩家出牌后，另一方持有剩余的所有牌。
        remaining==1 且本次出牌数==1（出牌前 remaining 恰好是2）时高置信度，否则低置信度。"""
        if player not in (Player.LEFT, Player.RIGHT):
            return
        if remaining == 0:
            return
        # other 在此处推导，无需从外部传入
        other = Player.RIGHT if player == Player.LEFT else Player.LEFT
        confidence = "high" if remaining == 1 and cards[card] == 1 else "low"
        updates.append((other, card, remaining, confidence))
        self._record_total(other, card, remaining)

    def _rule_player_played_all_their_cards(
        self,
        player: Player,
        card: Card,
        remaining: int,
        cards: CardCounts,
        updates: UpdateList,
    ) -> None:
        """出牌方打出某张牌且不是顺子时，推断其没有更多这张牌，低置信度。
        误差分析记录出牌数作为估算总数，用于验证"不拆牌"假设的准确率。
        remaining==0 时跳过 updates 写入——此时 _rule_both_have_none 已以高置信度
        覆盖双方，避免低置信度的重复写入把出牌方的绿色覆盖成红色。
        但 _record_total 仍需执行，否则误差分析会丢失这张牌的数据。"""
        if player not in (Player.LEFT, Player.RIGHT):
            return
        if is_sequence(cards):
            return
        self._record_total(player, card, cards[card])
        if remaining == 0:
            return
        updates.append((player, card, 0, "low"))

    def on_game_end(self, winner: Player) -> None:
        """计算并打印误差分析。winner 为最后出完牌的玩家。"""
        if winner == Player.MIDDLE:
            logger.info("自己获胜，无法验证对手估算")
            return

        loser = Player.RIGHT if winner == Player.LEFT else Player.LEFT
        winner_played = (
            self._counter.left if winner == Player.LEFT else self._counter.right
        )
        loser_played = (
            self._counter.right if winner == Player.LEFT else self._counter.left
        )
        winner_est = self._estimated_total[winner]
        loser_est = self._estimated_total[loser]

        lines = [
            f"====== 估算误差分析（{winner.value}获胜）======",
            f"{'牌':>6}  {'胜-实':>5}  {'胜-估':>5}  {'胜-差':>5}  {'败-实':>5}  {'败-估':>5}  {'败-差':>5}",
            "-" * 52,
        ]
        w_errors, l_errors = [], []
        for card in Card:
            w_actual = winner_played[card].get()
            l_played = loser_played[card].get()
            # 败方实际持牌数 = 败方已出数 + 当前剩余数
            # 注意：remaining 包含底牌（约3张），会导致败方持牌数被轻微高估，属已知近似
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

        total = len(Card)
        for label, errors in [(winner.value, w_errors), (loser.value, l_errors)]:
            n = len(errors)
            coverage = f"{n}/{total}"
            if n > 0:
                mae = sum(abs(e) for e in errors) / n
                over = sum(1 for e in errors if e < 0)
                under = sum(1 for e in errors if e > 0)
                lines.append(
                    f"{label}: 覆盖率={coverage}  MAE={mae:.2f}  高估={over}张 低估={under}张"
                )
            else:
                lines.append(f"{label}: 覆盖率={coverage}  （无估算数据）")

        logger.info("\n" + "\n".join(lines))
