"""
后端逻辑模块，负责游戏的后台逻辑处理，包括牌局状态的监控和记牌。
"""

from itertools import cycle
from time import sleep
from typing import NoReturn

from config import GAME_START_INTERVAL, SCREENSHOT_INTERVAL
from image_processing import GrayscaleImage
from logger import logger
from regions import LandlordLocation, Region, RegionState

from .card_counter import CardCounter
from .game_state import GameState


def backend_logic(counter: CardCounter) -> NoReturn:
    """
    后端逻辑主函数，负责监控游戏状态并更新记牌器。

    :param counter: 记牌器对象
    """

    def mark_cards(cards: dict[str, int]) -> None:
        """
        标记已出的牌。

        :param cards: 已出的牌
        """
        for card, count in cards.items():
            for _ in range(count):
                counter.mark(card)
                logger.info(f"已标记 {card}")

    logger.trace("开始后端循环代码")

    while True:
        # 初始化游戏对象
        gs = GameState()
        logger.success("游戏初始化完成")
        counter.reset()  # 重置牌数量

        # 等待游戏开始
        while not gs.is_game_started(gs.get_screenshot()):
            logger.trace("正在等待游戏开始...")
            sleep(GAME_START_INTERVAL)
        logger.info("游戏开始")

        # 初始化地主
        landlord: LandlordLocation = gs.find_landlord_location(gs.get_screenshot())
        logger.info(f"地主是{landlord.name}")
        region_cycle = cycle(
            [
                gs.card_regions["left"],
                gs.card_regions["middle"],
                gs.card_regions["right"],
            ]
        )
        for _ in range(landlord.value):
            next(region_cycle)

        # 获取截图
        screenshot = gs.get_screenshot()
        current_region: Region = next(region_cycle)
        current_region.is_landlord = True  # 标记地主区域

        # 初始化自身
        gs.card_regions["middle"].is_me = True
        gs.my_cards_region.capture(gs.get_screenshot())
        mark_cards(gs.get_my_cards())

        # 实时记录
        while not gs.is_game_ended(screenshot):
            screenshot: GrayscaleImage = gs.get_screenshot()  # 更新截图
            current_region.capture(screenshot)  # 更新当前出牌区域截图
            current_region.update_state()  # 更新当前出牌区域状态

            # 如果区域仍处于等待状态，则等待
            if current_region.state == RegionState.WAIT:
                sleep(SCREENSHOT_INTERVAL)
                continue

            # 如果区域有牌，并且不是自己，则识别并标记牌
            if current_region.state == RegionState.ACTIVE and not current_region.is_me:
                cards = current_region.recognize_cards()
                logger.info(f"识别到已出牌：{cards}")
                mark_cards(cards)

            elif current_region.state == RegionState.PASS:
                logger.info("玩家选择不出牌")

            # 并更新截图及当前区域
            current_region = next(region_cycle)
            logger.trace("跳到下一个区域")
