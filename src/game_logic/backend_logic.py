from time import sleep
from typing import NoReturn
from itertools import cycle

from classes.region import Region, State
from config import SCREENSHOT_INTERVAL, GAME_START_INTERVAL
from logger import logger
from game_logic.gs import GameState


def backend_logic(counter) -> NoReturn:
    def mark_cards(cards) -> None:
        for card, count in cards.items():
            for _ in range(count):
                counter.mark_card(card)
                logger.info(f"已标记 {card}")

    logger.info("开始游戏")

    while True:
        # 初始化游戏对象
        gs = GameState()
        logger.info("游戏初始化完成")
        counter.reset()  # 重置牌数量

        # 等待游戏开始
        while not gs.is_game_started(gs.get_screenshot()):
            logger.debug("正在等待游戏开始...")
            sleep(GAME_START_INTERVAL)
        logger.info("游戏开始")

        # 初始化地主
        landlord = gs.determine_landlord_location(gs.get_screenshot())
        logger.info(f"地主是{landlord.name}")
        region_cycle = cycle([
            gs.card_regions["left"],
            gs.card_regions["middle"],
            gs.card_regions["right"],
        ])
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
            screenshot = gs.get_screenshot()  # 更新截图
            current_region.capture(screenshot)  # 更新当前出牌区域截图
            current_region.update_region_state()  # 更新当前出牌区域状态

            # 如果区域仍处于等待状态，则等待
            if current_region.state == State.WAIT:
                sleep(SCREENSHOT_INTERVAL)
                continue

            # 如果区域有牌，并且不是自己，则识别并标记牌
            if current_region.state == State.ACTIVE and not current_region.is_me:
                mark_cards(current_region.recognize_cards())

            # 并更新截图及当前区域
            current_region = next(region_cycle)
