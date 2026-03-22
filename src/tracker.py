"""
游戏追踪模块。负责游戏主循环、帧间对比计牌、游戏开始/结束检测、计数校验。
通过帧迭代器接收图像，与截图来源解耦（支持实时截图和录屏回放）。
"""

import tkinter as tk
from threading import Event, Thread
from time import sleep
from typing import Callable, Iterator, Optional

import numpy as np
from loguru import logger

from capture import find_game_window, region_to_pixels, take_screenshot
from config import GAME_START_INTERVAL, SCREENSHOT_INTERVAL, TEMPLATE_SCALE, THRESHOLDS
from recognize import has_warning, identify_cards, match_mark
from card_types import Card, Mark, Player

GrayImage = np.ndarray
CardCounts = dict[Card, int]
OnUpdateFn = Callable[[Player, CardCounts], None]  # 每次检测到出牌时的回调


# ---------------------------------------------------------------------------
# 计数状态
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 游戏结束校验
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# 帧来源
# ---------------------------------------------------------------------------


def live_frames(
    initial_window_rect: Optional[tuple[int, int, int, int]], stop_event: Event
) -> Iterator[tuple[GrayImage, float, tuple[int, int, int, int]]]:
    """实时截图帧迭代器，产出 (灰度图, 模板缩放比例, window_rect)。
    每帧重新查询游戏窗口位置，支持用户在游戏中途移动窗口。
    若窗口找不到（已关闭），沿用上一帧的位置继续尝试。
    收到停止信号后立即退出，不再产出新帧。
    """
    window_rect = initial_window_rect
    while not stop_event.is_set():
        latest = find_game_window()
        if latest is not None:
            window_rect = latest
        frame = take_screenshot(window_rect, stop_event)
        if frame is None:
            return  # 截图返回 None 说明收到了停止信号
        if has_warning(frame, TEMPLATE_SCALE):
            sleep(SCREENSHOT_INTERVAL)
            continue  # 检测到警告弹窗，跳过该帧
        yield frame, TEMPLATE_SCALE, window_rect
        sleep(SCREENSHOT_INTERVAL)


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------

PLAYERS = [Player.LEFT, Player.MIDDLE, Player.RIGHT]

# 地主标记所在区域（剩余牌数显示区域旁边有皇冠图标）
LANDLORD_REGIONS = {
    Player.LEFT: "remaining_cards_left",
    Player.MIDDLE: "remaining_cards_middle",
    Player.RIGHT: "remaining_cards_right",
}

# 各玩家出牌显示区域
PLAY_REGIONS = {
    Player.LEFT: "playing_left",
    Player.MIDDLE: "playing_middle",
    Player.RIGHT: "playing_right",
}


def run(
    frames: Iterator[tuple[GrayImage, float, tuple[int, int, int, int]]],
    counter: Counter,
    stop_event: Event,
    on_update: Optional[OnUpdateFn] = None,
    mark_potential_bombs: Optional[Callable[[set], None]] = None,
    on_reset: Optional[Callable[[], None]] = None,
) -> None:
    """
    游戏主循环。
    - frames: 帧迭代器，每次产出 (灰度图, scale, window_rect)；
      window_rect 每帧更新，支持用户移动窗口后仍能正确识别
    - counter: 计数状态对象（由调用方持有，以便 UI 绑定）
    - stop_event: 外部停止信号
    - on_update: 每次出牌后的回调（可选，供 UI 或调试工具使用）
    - mark_potential_bombs: 识别完手牌后调用，传入我没有的牌的集合（可选）；
      没有某种牌意味着对手可能持有该牌的全部 4 张（炸弹），UI 用红色高亮提示用户
    """

    while not stop_event.is_set():
        # ── 等待游戏开始 ──────────────────────────────────────────────────
        # 通过检测三个玩家的剩余牌数区域是否出现地主皇冠标记来判断游戏开始
        logger.info("等待游戏开始...")
        counter.reset()
        if on_reset:
            on_reset()
        landlord: Optional[Player] = None

        for frame, scale, window_rect in frames:  # type: GrayImage, float, tuple[int,int,int,int]
            if stop_event.is_set():
                return

            # 同时检查三个区域，置信度最高的那个就是地主位置
            confidences = {
                p: match_mark(
                    frame,
                    region_to_pixels(LANDLORD_REGIONS[p], window_rect),
                    Mark.LANDLORD,
                    scale,
                )
                for p in PLAYERS
            }
            best = max(confidences, key=lambda p: confidences[p])
            if confidences[best] >= THRESHOLDS["landlord"]:
                landlord = best
                logger.info(
                    f"游戏开始，地主是{landlord.value}（置信度 {confidences[best]:.3f}）"
                )
                break

            sleep(GAME_START_INTERVAL)

        if stop_event.is_set():
            return

        # ── 识别自己的手牌 ────────────────────────────────────────────────
        # 游戏开始后立即识别自己的手牌并从剩余牌数中扣除，
        # 这样剩余数就代表"除了我自己的牌以外还有多少张在场上"
        frame, scale, window_rect = next(frames)  # type: GrayImage, float, tuple[int,int,int,int]
        my_cards = identify_cards(
            frame, region_to_pixels("my_cards", window_rect), scale
        )
        logger.info(f"识别到自己的牌: {my_cards}")
        for card, count in my_cards.items():
            counter.mark(card, Player.MIDDLE, count)
        counter.total_played[Player.MIDDLE] = 0  # 手牌标记不算出牌，重置为 0

        expected = 20 if landlord == Player.MIDDLE else 17
        if sum(my_cards.values()) != expected:
            logger.warning(
                f"自己的牌识别到 {sum(my_cards.values())} 张，期望 {expected} 张"
            )

        # 通知 UI 哪些牌不在我手里：
        # 若我没有某种牌，对手可能持有该牌的全部 4 张（炸弹），主窗口用红色高亮提示
        if mark_potential_bombs:
            not_my_cards = {card for card in Card if card not in my_cards}
            mark_potential_bombs(not_my_cards)

        # ── 游戏主循环（帧间对比）────────────────────────────────────────
        # 每帧同时扫描三个出牌区域，与上一帧对比：
        # 某区域从空变为非空，或内容发生变化，则认为该玩家刚出了牌
        prev: dict[Player, CardCounts] = {p: {} for p in PLAYERS}
        # 上一帧各区域的原始像素裁剪图，用于跳过未变化区域的模板识别
        prev_crops: dict[Player, GrayImage] = {}
        prev_end_crop: Optional[GrayImage] = None
        prev_end_cards: CardCounts = {}
        last_player = Player.LEFT  # 记录最后出牌的玩家，游戏结束校验时使用

        for frame, scale, window_rect in frames:  # type: GrayImage, float, tuple[int,int,int,int]
            if stop_event.is_set():
                return

            # 检测游戏是否结束：底牌区域（三张翻开的牌）出现时说明有人出完牌了
            end_region = region_to_pixels("three_displayed_cards", window_rect)
            x1, y1, x2, y2 = end_region
            end_crop: GrayImage = frame[y1:y2, x1:x2]
            if prev_end_crop is not None and np.array_equal(end_crop, prev_end_crop):
                end_cards = prev_end_cards
                logger.debug("底牌区域像素未变，跳过识别")
            else:
                end_cards = identify_cards(frame, end_region, scale)
                prev_end_crop = end_crop
                prev_end_cards = end_cards
            if end_cards:
                logger.info(f"游戏结束，底牌区域识别到: {end_cards}")
                assert landlord is not None
                verify_counts(counter, landlord, last_player)
                break

            # 同时扫描三个出牌区域
            # 像素级变化检测：若裁剪图与上一帧完全相同，直接复用上次识别结果，跳过模板匹配
            curr: dict[Player, CardCounts] = {}
            for player in PLAYERS:
                region = region_to_pixels(PLAY_REGIONS[player], window_rect)
                x1, y1, x2, y2 = region
                crop: GrayImage = frame[y1:y2, x1:x2]
                if player in prev_crops and np.array_equal(crop, prev_crops[player]):
                    curr[player] = prev[player]  # 像素未变，复用上次结果
                    logger.debug(f"{player.value} 出牌区像素未变，跳过识别")
                else:
                    curr[player] = identify_cards(frame, region, scale)
                    prev_crops[player] = crop

            # 对比变化，记录出牌
            for player in PLAYERS:
                # curr 非空且与上一帧不同，说明该玩家刚打出了新的一手牌
                # 直接记录 curr 里的全部张数（curr != prev 已保证不会对同一手牌重复计数）
                # 自己（MIDDLE）的牌已在初始化时从 remaining 整体扣除，出牌不再影响 remaining
                if curr[player] and curr[player] != prev[player]:
                    logger.info(f"{player.value} 出牌: {curr[player]}")
                    for card, count in curr[player].items():
                        counter.mark(card, player, count, affect_remaining=(player != Player.MIDDLE))
                    last_player = player
                    if on_update:
                        on_update(player, curr[player])

            prev = curr


# ---------------------------------------------------------------------------
# 线程管理（供 UI 调用）
# ---------------------------------------------------------------------------


class Tracker:
    """封装后端线程的启动/停止，供 UI 调用。"""

    def __init__(
        self,
        counter: Counter,
        on_update: Optional[OnUpdateFn] = None,
        mark_potential_bombs: Optional[Callable[[set], None]] = None,
        on_reset: Optional[Callable[[], None]] = None,
    ) -> None:
        self.counter = counter
        self.on_update = on_update
        self.mark_potential_bombs = mark_potential_bombs
        self.on_reset = on_reset
        self._stop_event = Event()
        self._thread: Optional[Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.warning("Tracker 已在运行中")
            return

        # 清除上次的停止信号，然后启动新线程
        # find_game_window 只调用一次，截图（live_frames）和坐标转换（run）共用同一个结果，
        # 避免两次调用之间窗口移动导致截图区域与坐标不一致
        self._stop_event.clear()
        window_rect = find_game_window()
        frames = live_frames(window_rect, self._stop_event)
        def _run_safe(*args, **kwargs):
            try:
                run(*args, **kwargs)
            except Exception as e:
                logger.exception(f"后端线程异常退出: {e}")

        self._thread = Thread(
            target=_run_safe,
            args=(
                frames,
                self.counter,
                self._stop_event,
                self.on_update,
                self.mark_potential_bombs,
                self.on_reset,
            ),
            daemon=True,  # 主线程退出时后端线程自动结束，不会阻止程序退出
        )
        self._thread.start()
        logger.success("Tracker 已启动")

    def stop(self) -> None:
        # 只发停止信号，不等待线程结束（等待由 UI 的 _wait_and_enable 轮询处理）
        self._stop_event.set()
        logger.success("Tracker 已停止")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
