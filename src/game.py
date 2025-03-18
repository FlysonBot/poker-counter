from enum import Enum
from itertools import cycle
from time import sleep

import cv2
import numpy as np
from PIL import ImageGrab

from image_match import match_template_best_result
from logger import logger
from region import Region, State


class Landlord(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


class Game:
    def __init__(self):
        self.left_region = Region((260, 346), (700, 446))
        self.middle_region = Region((425, 500), (970, 740))
        self.right_region = Region((700, 346), (1140, 446))
        self.my_region = Region((350, 760), (1020, 820))
        self.regions = cycle([self.left_region, self.middle_region, self.right_region])

    def determine_game_start(self, screenshot):
        logger.info("正在寻找地主标记...")

        # 寻找地主标记
        max_val, _ = match_template_best_result(
            screenshot, cv2.imread("templates/Landlord.png", 0)
        )

        # 判断游戏开始
        logger.debug(f"地主标记匹配度为 {max_val}")
        return max_val >= 0.95

    def determine_landlord(self, screenshot):
        # 寻找地主标记
        logger.info("正在寻找地主标记...")
        _, max_loc = match_template_best_result(
            screenshot, cv2.imread("templates/Landlord.png", 0)
        )

        # 判断地主是谁
        logger.debug(f"地主标记x坐标为 {max_loc[0]}")
        if max_loc[0] < 600:
            return Landlord.LEFT
        elif max_loc[0] < 900:
            return Landlord.MIDDLE
        else:
            return Landlord.RIGHT

    def determine_game_end(self, screenshot):
        logger.info("正在寻找分数统计标记...")
        # 寻找分数统计标记
        max_val, max_loc = match_template_best_result(
            screenshot, cv2.imread("templates/Score.png", 0)
        )

        # 判断游戏结束
        logger.debug(f"分数统计标记匹配度为 {max_val}")
        return (
            max_val > 0.8 and (550 <= max_loc[0] <= 850) and (330 <= max_loc[1] <= 550)
        )

    def get_screenshot(self):
        return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)

    def get_my_cards(self):
        return self.my_region.recognize_cards()


def game_loop(interval, counter):
    def mark_cards(cards):
        for card, count in cards.items():
            for _ in range(count):
                counter.mark_card(card)

    logger.info("开始游戏")

    while True:
        # 初始化游戏对象
        game = Game()
        logger.info("游戏初始化完成")

        # 等待游戏开始
        while not game.determine_game_start(game.get_screenshot()):
            logger.debug("等待中...")
            sleep(1)
        logger.info("游戏开始")

        # 初始化
        counter.reset()  # 重置牌数量

        # 初始化地主
        landlord = game.determine_landlord(game.get_screenshot())
        logger.info(f"地主是{landlord.name}")
        for _ in range(landlord.value):
            next(game.regions)

        # 获取截图
        screenshot = game.get_screenshot()
        current_region = next(game.regions)
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
                sleep(interval)
                continue

            # 如果区域有牌，并且不是自己，则识别牌
            if current_region.state == State.ACTIVE and not current_region.is_me:
                mark_cards(current_region.recognize_cards())

            # 并更新截图及当前区域
            current_region = next(game.regions)
