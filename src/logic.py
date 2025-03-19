from time import sleep
from typing import NoReturn

from classes.game import Game
from classes.region import Region, State
from config import SCREENSHOT_INTERVAL, GAME_START_INTERVAL
from logger import logger


def backend_logic(counter) -> NoReturn:
    def mark_cards(cards) -> None:
        for card, count in cards.items():
            for _ in range(count):
                counter.mark_card(card)
                logger.info(f"已标记 {card}")

    logger.info("开始游戏")

    while True:
        # 初始化游戏对象
        game = Game()
        logger.info("游戏初始化完成")
        counter.reset()  # 重置牌数量

        # 等待游戏开始
        while not game.determine_game_start(game.get_screenshot()):
            logger.debug("等待中...")
            sleep(GAME_START_INTERVAL)
        logger.info("游戏开始")

        # 初始化地主
        landlord = game.determine_landlord(game.get_screenshot())
        logger.info(f"地主是{landlord.name}")
        for _ in range(landlord.value):
            next(game.regions)

        # 获取截图
        screenshot = game.get_screenshot()
        current_region: Region = next(game.regions)
        current_region.is_landlord = True  # 标记地主区域

        # 初始化自身
        game.middle_region.is_me = True
        game.my_region.capture_region(game.get_screenshot())
        mark_cards(game.get_my_cards())

        # 实时记录
        while not game.determine_game_end(screenshot):
            screenshot = game.get_screenshot()
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
            current_region = next(game.regions)
