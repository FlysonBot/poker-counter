from enum import Enum
from itertools import cycle

import cv2
import numpy as np
from PIL import ImageGrab

from classes.region import Region
from functions.color_percentage import calculate_color_percentage
from functions.image_match import match_template_best_result
from logger import logger


class Landlord(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


class Game:
    def __init__(self):
        self.left_region = Region((260, 346), (700, 446))
        self.middle_region = Region((425, 500), (970, 710))
        self.right_region = Region((700, 346), (1140, 446))
        self.my_region = Region((350, 730), (1020, 820))
        self.regions = cycle([self.left_region, self.middle_region, self.right_region])

    def determine_game_start(self, screenshot):
        logger.info("正在寻找地主标记...")
        marker_coordinates = [
            [(20, 555), (85, 580)],
            [(765, 900), (830, 930)],
            [(1310, 555), (1380, 580)],
        ]

        for coordinates in marker_coordinates:
            marker_screenshot = screenshot[
                coordinates[0][1] : coordinates[1][1],
                coordinates[0][0] : coordinates[1][0],
            ]
            max_val, _ = match_template_best_result(
                marker_screenshot, cv2.imread("templates/Landlord.png", 0)
            )
            logger.debug(f"地主标记匹配度为 {max_val}")
            if max_val >= 0.95:
                return True

        return False

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
        logger.info("正在计算底牌区域白色占比...")
        marker_screenshot = screenshot[120:140, 540:860]
        percentage = calculate_color_percentage(marker_screenshot, (255, 255, 255))
        logger.debug(f"底牌区域白色占比为 {percentage}")
        return percentage > 0.25

    def get_screenshot(self):
        return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)

    def get_my_cards(self):
        return self.my_region.recognize_cards()
