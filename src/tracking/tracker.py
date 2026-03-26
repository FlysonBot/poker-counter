"""
游戏追踪模块。

负责游戏主循环：等待游戏开始、识别初始手牌、逐帧对比出牌区域、检测游戏结束。
通过帧迭代器接收图像，与截图来源解耦，支持实时截图和离线录屏回放两种模式。
Tracker 类封装后端线程的启停，供 UI 层调用；run() 函数是实际的主循环逻辑。
"""

from dataclasses import dataclass
from threading import Event, Thread
from time import sleep
from typing import Callable, Iterator, Optional

import numpy as np
from loguru import logger

from card_types import Card, Mark, Player
from config import GAME_START_INTERVAL, SCREENSHOT_INTERVAL, THRESHOLDS
from recognition.calibrate import calibrate_scale
from recognition.capture import find_game_window, region_to_pixels, take_screenshot
from recognition.recognize import has_warning, identify_cards, match_mark
from tracking.counter import CardCounts, Counter

GrayImage = np.ndarray
OnUpdateFn = Callable[[Player, CardCounts], None]  # 每次检测到出牌时的回调
OnGameEndFn = Callable[
    [Player, Player], None
]  # 游戏结束时的回调，传入 (winner, landlord)


@dataclass
class GameCallbacks:
    """游戏事件回调容器，所有字段均可选。"""

    on_update: Optional[OnUpdateFn] = None  # 每次出牌时调用
    on_reset: Optional[Callable[[], None]] = None  # 每局开始前调用
    on_game_end: Optional[OnGameEndFn] = None  # 游戏结束时调用
    mark_potential_bombs: Optional[Callable[[set], None]] = None  # 识别完手牌后调用


# ---------------------------------------------------------------------------
# 帧来源
# ---------------------------------------------------------------------------


def live_frames(
    initial_window_rect: Optional[tuple[int, int, int, int]], stop_event: Event
) -> Iterator[tuple[GrayImage, tuple[int, int, int, int]]]:
    """实时截图帧迭代器，产出 (灰度图, window_rect)。
    每帧重新查询游戏窗口位置，支持用户在游戏中途移动窗口。
    若窗口找不到（已关闭），沿用上一帧的位置继续尝试。
    收到停止信号后立即退出，不再产出新帧。
    """

    window_rect = initial_window_rect
    while not stop_event.is_set():
        # 每帧都重新查询游戏窗口位置，以支持用户移动窗口
        latest = find_game_window()
        if latest is not None:
            window_rect = latest
        frame = take_screenshot(window_rect, stop_event)
        if frame is None:
            return  # 截图返回 None 说明收到了停止信号
        if has_warning(frame, 1.0):
            sleep(SCREENSHOT_INTERVAL)
            continue  # 检测到警告弹窗，跳过该帧
        yield frame, window_rect
        sleep(SCREENSHOT_INTERVAL)


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------

PLAYERS = [Player.LEFT, Player.MIDDLE, Player.RIGHT]

# 地主标记所在区域（检测该区域是否出现"[ 20 张 ]"文字，只有地主初始持有 20 张牌）
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
    frames: Iterator[tuple[GrayImage, tuple[int, int, int, int]]],
    counter: Counter,
    stop_event: Event,
    callbacks: Optional[GameCallbacks] = None,
) -> None:
    """
    游戏主循环。
    - frames: 帧迭代器，每次产出 (灰度图, window_rect)；
      window_rect 每帧更新，支持用户移动窗口后仍能正确识别
    - counter: 计数状态对象（由调用方持有，以便 UI 绑定）
    - stop_event: 外部停止信号
    - callbacks: 游戏事件回调（可选，默认全为 None）

    注：MIDDLE（自己）是特殊玩家——手牌在游戏开始时整批从 remaining 预扣，
    后续出牌只更新 total_played，不再影响 remaining。
    """

    if callbacks is None:
        callbacks = GameCallbacks()

    while not stop_event.is_set():
        # ── 等待游戏开始 ──────────────────────────────────────────────────
        # 通过检测三个玩家的剩余牌数区域是否出现"[ 20 张 ]"文字来判断游戏开始和地主位置，
        # 因为只有地主初始持有 20 张牌，农民只有 17 张
        logger.info("等待游戏开始...")
        counter.reset()
        if callbacks.on_reset:
            callbacks.on_reset()
        landlord: Optional[Player] = None
        frame: GrayImage = np.zeros((1, 1), dtype=np.uint8)
        window_rect: tuple[int, int, int, int] = (0, 0, 0, 0)

        for frame, window_rect in frames:
            if stop_event.is_set():
                return

            # 同时检查三个区域，置信度最高的那个就是地主位置
            confidences = {
                p: match_mark(
                    frame,
                    region_to_pixels(LANDLORD_REGIONS[p], window_rect),
                    Mark.LANDLORD,
                    1.0,
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

        # ── 自动校准 scale ────────────────────────────────────────────────
        # 地主确定后手牌已发完，用当前帧的手牌高度估算模板缩放比例
        if landlord is None:
            return  # 帧迭代器耗尽但未找到地主，正常退出
        scale = calibrate_scale(frame, window_rect)

        # ── 识别自己的手牌 ────────────────────────────────────────────────
        # 游戏开始后立即识别自己的手牌并从剩余牌数中扣除，
        # 这样剩余数就代表"除了我自己的牌以外还有多少张在场上"
        frame, window_rect = next(frames)
        my_cards = identify_cards(
            frame, region_to_pixels("my_cards", window_rect), scale
        )
        logger.info(f"识别到自己的牌: {my_cards}")
        counter.mark_hand(my_cards, is_landlord=(landlord == Player.MIDDLE))

        # 通知 UI 哪些牌不在我手里：
        # 若我没有某种牌，主窗口用红色高亮提示，方便记忆自己的手牌构成并推算对手持牌
        if callbacks.mark_potential_bombs:
            not_my_cards = {card for card in Card if card not in my_cards}
            callbacks.mark_potential_bombs(not_my_cards)

        # ── 游戏主循环（帧间对比）────────────────────────────────────────
        # 每帧同时扫描三个出牌区域，与上一帧对比：
        # 某区域从空变为非空，或内容发生变化，则认为该玩家刚出了牌
        prev: dict[Player, CardCounts] = {p: {} for p in PLAYERS}
        # 上一帧各区域的原始像素裁剪图，用于跳过未变化区域的模板识别
        prev_crops: dict[Player, GrayImage] = {}
        prev_end_crop: Optional[GrayImage] = None
        prev_end_cards: CardCounts = {}
        # 记录最后出牌的玩家，游戏结束校验时使用；初始值为占位符，正常情况下游戏结束前必有出牌覆盖此值
        last_player = Player.LEFT

        for frame, window_rect in frames:
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
                # 底牌与最后一手牌同帧出现，需在 break 前扫描出牌区确定赢家
                for player in PLAYERS:
                    if player == Player.MIDDLE:
                        continue
                    region = region_to_pixels(PLAY_REGIONS[player], window_rect)
                    cards_this_frame = identify_cards(frame, region, scale)
                    if cards_this_frame and cards_this_frame != prev.get(player, {}):
                        logger.info(
                            f"游戏结束帧检测到 {player.value} 出牌: {cards_this_frame}"
                        )
                        for card, count in cards_this_frame.items():
                            counter.mark(card, player, count, deduct_remaining=True)
                        last_player = player
                        if callbacks.on_update:
                            callbacks.on_update(player, cards_this_frame)
                        break
                assert landlord is not None
                counter.verify(landlord, last_player)
                if callbacks.on_game_end:
                    callbacks.on_game_end(last_player, landlord)
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
                        counter.mark(
                            card,
                            player,
                            count,
                            deduct_remaining=(player != Player.MIDDLE),
                        )
                    last_player = player
                    if callbacks.on_update:
                        callbacks.on_update(player, curr[player])

            prev = curr


# ---------------------------------------------------------------------------
# 线程管理（供 UI 调用）
# ---------------------------------------------------------------------------


class Tracker:
    """封装后端线程的启动/停止，供 UI 调用。"""

    def __init__(
        self, counter: Counter, callbacks: Optional[GameCallbacks] = None
    ) -> None:
        self.counter = counter
        self.callbacks = callbacks if callbacks is not None else GameCallbacks()
        self._stop_event = Event()
        self._thread: Optional[Thread] = None

    def start(self) -> None:
        """启动后端识别线程。若线程已在运行则忽略。"""

        if self._thread and self._thread.is_alive():
            logger.warning("Tracker 已在运行中")
            return

        # 清除上次的停止信号，然后启动新线程
        # find_game_window 只调用一次，截图（live_frames）和坐标转换（run）共用同一个结果，
        # 避免两次调用之间窗口移动导致截图区域与坐标不一致
        self._stop_event.clear()
        window_rect = find_game_window()
        frames = live_frames(window_rect, self._stop_event)

        def _run_safe():
            try:
                run(frames, self.counter, self._stop_event, self.callbacks)
            except Exception as e:
                logger.exception(f"后端线程异常退出: {e}")

        self._thread = Thread(target=_run_safe, daemon=True)
        self._thread.start()
        logger.success("Tracker 已启动")

    def stop(self) -> None:
        """发出停止信号。不等待线程结束（等待由 UI 的 _wait_and_enable 轮询处理）。"""

        self._stop_event.set()
        logger.success("Tracker 已停止")

    @property
    def is_running(self) -> bool:
        """返回后端线程是否仍在运行。"""

        return self._thread is not None and self._thread.is_alive()
