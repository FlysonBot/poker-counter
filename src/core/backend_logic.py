"""
后端逻辑模块，负责游戏的后台逻辑处理，包括牌局状态的监控和记牌。
"""

from itertools import cycle
from threading import Event
from time import sleep

from loguru import logger

from misc.custom_types import Card, CardIntDict, Player, RegionState, WindowsType
from misc.singleton import singleton
from models.config import GAME_START_INTERVAL, SCREENSHOT_INTERVAL
from models.counters import CardCounter
from models.game_state import GameState, card_regions
from models.labels import StringLabelsProperty
from models.screenshot import screenshot


@singleton
class BackendLogic:
    """后端逻辑类，负责监控游戏状态并更新记牌器"""

    def __init__(self) -> None:
        self._counter = CardCounter()
        self._gs = GameState()
        self.text_color = StringLabelsProperty({card: "black" for card in Card})

    def set_stop_event(self, stop_event: Event) -> None:
        self._stop_event = stop_event

    @property
    def _keep_running(self) -> bool:
        return not self._stop_event.is_set()

    def _change_text_to_red(self, card: Card, player: Player) -> None:
        """更新标签字体为红色"""
        match player:
            case Player.LEFT:
                self.text_color.change_style(card, WindowsType.LEFT, "red")
            case Player.RIGHT:
                self.text_color.change_style(card, WindowsType.RIGHT, "red")
            case _:
                pass

    def _mark_cards(self, cards: CardIntDict, player: Player) -> None:
        """标记已出的牌"""
        for card, count in cards.items():
            for _ in range(count):
                self._counter.mark(card, player)
            if count > 1:
                self._change_text_to_red(card, player)

    def _pregame_init(self) -> None:
        """初始化"""
        self._counter.reset()
        self._player_cycle = cycle([Player.LEFT, Player.MIDDLE, Player.RIGHT])
        screenshot.update()

    def _wait_for_game_start(self) -> None:
        """等待游戏开始"""
        while not self._gs.is_game_started and self._keep_running:
            screenshot.update()
            logger.trace("正在等待游戏开始...")
            sleep(GAME_START_INTERVAL)
        if self._keep_running:
            logger.info("游戏开始")

    def _find_landlord(self) -> None:
        """找地主"""
        self._landlord = self._gs.landlord_location
        self._landlord.log_landlord()

    def _init_player_cycle(self) -> None:
        """调整玩家循环以使地主变为第一个玩家"""
        self._current_player = next(self._player_cycle)
        while self._current_player is not self._landlord:
            self._current_player = next(self._player_cycle)

    def _mark_my_cards(self) -> None:
        """标记自己的牌"""
        self._mark_cards(self._gs.my_cards, Player.MIDDLE)

    def _should_advance_after_marking(self) -> bool:
        """根据条件标记活跃区域内的牌，返回是否进入下一个区域"""
        if self._current_player is Player.MIDDLE:
            return True  # 不标记自己的牌（因为已经标记过了）

        cards = card_regions[self._current_player].recognize_cards()
        logger.info(f"识别到已出牌：{cards}")

        if len(cards) > 0:
            self._mark_cards(cards, self._current_player)
            return True

        logger.debug("未识别到牌，继续等待")
        return False

    def _should_advance(self) -> bool:
        """每个区域识牌记牌的逻辑，返回是否进入下一个区域"""
        match card_regions[self._current_player].state:
            case RegionState.WAIT:
                sleep(SCREENSHOT_INTERVAL)
                return False

            case RegionState.PASS:
                logger.info("玩家选择不出牌")
                return True

            case RegionState.ACTIVE:
                return self._should_advance_after_marking()

    def run(self) -> None:
        """后端逻辑主函数，负责监控游戏状态并更新记牌器"""
        with logger.catch():  # 让日志记录器捕获所有错误
            while self._keep_running:
                self._pregame_init()

                self._wait_for_game_start()

                self._find_landlord()
                self._init_player_cycle()
                self._mark_my_cards()
                self._current_player.log_region()

                while self._keep_running and not self._gs.is_game_ended:
                    screenshot.update()
                    card_regions[self._current_player].update_state()

                    if self._should_advance():
                        self._current_player = next(self._player_cycle)
                        self._current_player.log_region()
