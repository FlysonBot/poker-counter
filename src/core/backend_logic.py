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
from models.labels import LabelProperties
from models.screenshot import screenshot

from .verify_count import GameEndExamination


@singleton
class BackendLogic:
    """后端逻辑类，负责监控游戏状态并更新记牌器"""

    def __init__(self) -> None:
        self._counter = CardCounter()
        self._gs = GameState()
        self.label_properties = LabelProperties()
        logger.info("后端逻辑类初始化完毕")

    def set_stop_event(self, stop_event: Event) -> None:
        self._stop_event = stop_event
        logger.info("后端终止事件设置完毕")

    @property
    def _keep_running(self) -> bool:
        return not self._stop_event.is_set()

    def _update_text_color(self, card: Card, count: int, player: Player) -> None:
        """根据条件更新标签字体颜色"""
        if count > 1:  # 同一牌如果在同一回合内出了多次就改成红色
            match player:
                case Player.LEFT:
                    self.label_properties.text_color.change_style(
                        card, WindowsType.LEFT, "red"
                    )
                    logger.debug(
                        f"{card.value}出了{count}次，更改上家记牌器标签字体颜色为红色"
                    )
                case Player.MIDDLE:  # 自己没有记牌器窗口，不需要改颜色
                    pass
                case Player.RIGHT:
                    self.label_properties.text_color.change_style(
                        card, WindowsType.RIGHT, "red"
                    )
                    logger.debug(
                        f"{card.value}出了{count}次，更改下家记牌器标签字体颜色为红色"
                    )
        # 不管如何，只要出了牌就把总记牌器标签颜色改成黑色
        self.label_properties.text_color.change_style(card, WindowsType.MAIN, "black")
        logger.debug(f"更改主窗口记牌器{card.value}的颜色为黑色")

    def _mark_cards(self, cards: CardIntDict, player: Player) -> None:
        """标记已出的牌"""
        for card, count in cards.items():
            self._update_text_color(card, count, player)
            for _ in range(count):
                self._counter.mark(card, player)

    def _pregame_init(self) -> None:
        """初始化"""
        self._counter.reset()
        self.label_properties.text_color.reset()
        self._player_cycle = cycle([Player.LEFT, Player.MIDDLE, Player.RIGHT])
        screenshot.update()
        logger.info("游戏前初始化完成")

    def _wait_for_game_start(self) -> None:
        """等待游戏开始"""
        logger.info("正在等待游戏开始...")
        while not self._gs.is_game_started and self._keep_running:
            screenshot.update()
            logger.debug("正在等待游戏开始...")
            sleep(GAME_START_INTERVAL)
        if self._keep_running:
            logger.info("游戏已开始")

    def _find_landlord(self) -> None:
        """找地主"""
        self._landlord = self._gs.landlord_location
        logger.info(f"地主是{self._landlord.value}")

    def _init_player_cycle(self) -> None:
        """调整玩家循环以使地主变为第一个玩家"""
        self._current_player = next(self._player_cycle)
        while self._current_player is not self._landlord:
            self._current_player = next(self._player_cycle)

    def _mark_my_cards(self) -> None:
        """标记自己的牌"""
        my_cards = self._gs.my_cards
        logger.info(f"识别到自己的牌为：{my_cards}")
        self._mark_cards(my_cards, Player.MIDDLE)
        self._counter.player2_count = 0  # 重置出牌计数

        # 将未标记的牌标记为红色
        not_my_cards = {card for card in Card if card not in my_cards}
        for card in not_my_cards:
            if self._keep_running:  # 避免尝试在主线程已关闭窗口后更改已关闭的窗口
                self.label_properties.text_color.change_style(
                    card, WindowsType.MAIN, "red"
                )
            else:  # 并配合主线程的关闭命令退出循环
                break

        # 检查退出事件
        if not self._keep_running:
            return

        expected_card_count = 20 if self._landlord is Player.MIDDLE else 17
        if sum(my_cards.values()) != expected_card_count:
            logger.warning(
                f"自己的牌识别出错，识别到了{sum(my_cards.values())}张牌，但应该识别到{expected_card_count}张牌。"
                f"自己{'' if self._landlord is Player.MIDDLE else '并不'}是地主。"
            )

    def _should_advance_after_marking(self) -> bool:
        """根据条件标记活跃区域内的牌，返回是否进入下一个区域"""
        cards = card_regions[self._current_player].recognize_cards()
        logger.info(f"识别到已出牌：{cards}")

        if len(cards) > 0:
            if self._current_player is not Player.MIDDLE:  # 不再次标记自己的牌
                self._mark_cards(cards, self._current_player)
            return True

        logger.debug("未识别到任何牌，继续等待。")
        return False

    def _should_advance(self) -> bool:
        """每个区域识牌记牌的逻辑，返回是否进入下一个区域"""
        match card_regions[self._current_player].state:
            case RegionState.WAIT:
                logger.debug("等待玩家出牌中...")
                sleep(SCREENSHOT_INTERVAL)
                return False

            case RegionState.PASS:
                logger.info("玩家选择不出牌")
                return True

            case RegionState.ACTIVE:
                logger.info("检测到玩家已出牌，正在识别...")
                return self._should_advance_after_marking()

    def _game_end_self_examination(self) -> None:
        """游戏结束时进行自检"""
        GameEndExamination(self._landlord, self._current_player)

    def run(self) -> None:
        """后端逻辑主函数，负责监控游戏状态并更新记牌器"""
        with logger.catch():  # 让日志记录器捕获所有错误
            while self._keep_running:
                self._pregame_init()

                self._wait_for_game_start()

                self._find_landlord()
                self._init_player_cycle()
                self._mark_my_cards()
                logger.info(f"切换到{self._current_player.value}的区域")

                while self._keep_running and not self._gs.is_game_ended:
                    screenshot.update()
                    card_regions[self._current_player].update_state()

                    if self._should_advance() and not self._gs.is_game_ended:
                        self._current_player = next(self._player_cycle)
                        logger.info(f"切换到{self._current_player.value}的区域")

            # 重置标签样式object，以避免在关闭窗口后重复使用Tkinter变量
            self.label_properties.reset()
