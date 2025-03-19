from itertools import cycle

import cv2
import numpy as np
from PIL import ImageGrab

from classes.landlord_enum import Landlord
from classes.region import Region
from config import REGIONS, THRESHOLDS, DIVIDER_LEFT, DIVIDER_RIGHT
from image_processing.color_percentage import color_percentage
from image_processing.template_match import best_template_match
from logger import logger


class Game:
    def __init__(self):
        self.left_region = Region(REGIONS["playing_left"])
        self.middle_region = Region(REGIONS["playing_middle"])
        self.right_region = Region(REGIONS["playing_right"])
        self.my_region = Region(REGIONS["my_cards"])
        self.regions = cycle([self.left_region, self.middle_region, self.right_region])

    def determine_game_start(self, screenshot):
        logger.info("正在寻找地主标记...")
        marker_coordinates = (
            REGIONS["20cards_left"],
            REGIONS["20cards_middle"],
            REGIONS["20cards_right"],
        )

        for coordinates in marker_coordinates:
            marker_screenshot = screenshot[
                coordinates[0][1] : coordinates[1][1],
                coordinates[0][0] : coordinates[1][0],
            ]  # 第一个slicing返回第一/二个坐标，第二个slicing返回x/y坐标
            
            max_val, _ = best_template_match(
                marker_screenshot, cv2.imread("templates/Landlord.png", 0)
            )
            logger.debug(f"地主标记匹配度为 {max_val}")
            
            if max_val >= THRESHOLDS["landlord"]:
                return True

        return False

    def determine_landlord(self, screenshot):
        logger.info("正在寻找地主标记...")
        
        # 寻找地主标记
        _, max_loc = best_template_match(
            screenshot, cv2.imread("templates/Landlord.png", 0)
        )
        logger.debug(f"地主标记x坐标为 {max_loc[0]}")

        # 判断地主是谁
        if max_loc[0] < DIVIDER_LEFT:
            return Landlord.LEFT
        elif max_loc[0] < DIVIDER_RIGHT:
            return Landlord.MIDDLE
        else:
            return Landlord.RIGHT

    def determine_game_end(self, screenshot):
        logger.info("正在计算底牌区域白色占比...")

        # 从截图中提取底牌区域图片
        coord = REGIONS["3_shown_cards"]
        marker_screenshot = screenshot[coord[0][1]:coord[1][1], coord[0][0]:coord[1][0]]
        
        # 计算白色在图片中的占比
        percentage = color_percentage(marker_screenshot, (255, 255, 255))
        logger.debug(f"底牌区域白色占比为 {percentage}")

        return percentage > THRESHOLDS["end-game"]

    def get_screenshot(self):
        return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)

    def get_my_cards(self):
        return self.my_region.recognize_cards()
