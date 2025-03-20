from time import sleep
from typing import NoReturn

from regions.region_manager import RegionManager
from classes.region import Region, State
from config import SCREENSHOT_INTERVAL, GAME_START_INTERVAL
from logger import logger
from src.regions import region_manger


def backend_logic(counter) -> NoReturn:
    def mark_cards(cards) -> None:
        for card, count in cards.items():
            for _ in range(count):
                counter.mark_card(card)
                logger.info(f"已标记 {card}")

    logger.info("开始游戏")

    while True:
        # 初始化游戏对象
        region_manger = RegionManager()
        logger.info("游戏初始化完成")
        counter.reset()  # 重置牌数量

        # 等待游戏开始
        while not region_manger.determine_game_start(region_manger.get_screenshot()):
            logger.debug("等待中...")
            sleep(GAME_START_INTERVAL)
        logger.info("游戏开始")

        # 初始化地主
        landlord = region_manger.determine_landlord_location(region_manger.get_screenshot())
        logger.info(f"地主是{landlord.name}")
        for _ in range(landlord.value):
            next(region_manger.regions)

        # 获取截图
        screenshot = region_manger.get_screenshot()
        current_region: Region = next(region_manger.regions)
        current_region.is_landlord = True  # 标记地主区域

        # 初始化自身
        region_manger.card_regions["middle"].is_me = True
        region_manger.my_cards_region.capture(region_manger.get_screenshot())
        mark_cards(region_manger.get_my_cards())

        # 实时记录
        while not region_manger.determine_game_end(screenshot):
            screenshot = region_manger.get_screenshot()
            current_region.capture_region(screenshot)
            current_region.update_region_state()

            # 如果区域处于等待状态，则等待
            if current_region.state == State.WAIT:
                sleep(SCREENSHOT_INTERVAL)
                continue

            # 如果区域有牌，并且不是自己，则识别牌
            if current_region.state == State.ACTIVE and not current_region.is_me:
                mark_cards(current_region.recognize_cards())

            # 并更新截图及当前区域
            current_region = next(region_manger.regions)
