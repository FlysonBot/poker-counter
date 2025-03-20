import cv2
import numpy as np
from PIL import ImageGrab
from time import sleep

from regions.landlord_enum import Landlord
from regions.region import Region
from regions.card_region import CardRegion
from config import REGIONS, THRESHOLDS
from image_processing.color_percentage import color_percentage
from image_processing.template_match import best_template_match
from image_processing.templates import MARKS
from logger import logger


class GameState:
    def __init__(self):
        self.card_regions = {
            "left": CardRegion(REGIONS["playing_left"]),
            "middle": CardRegion(REGIONS["playing_middle"]),
            "right": CardRegion(REGIONS["playing_right"]),
        }
        self.landlord_marker = {
            "left": Region(REGIONS["remaining_cards_left"]),
            "middle": Region(REGIONS["remaining_cards_middle"]),
            "right": Region(REGIONS["remaining_cards_right"]),
        }
        self.game_end_marker = Region(REGIONS["3_displayed_cards"])
        self.my_cards_region = CardRegion(REGIONS["my_cards"])

    def get_screenshot(self):
        try:
            return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)
        
        except OSError:
            logger.info("Error taking screenshot. The screen had likely turned off. Retrying untill error resolve on its own.")

            while True:
                try:
                    return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)
                except OSError:
                    sleep(2)


    def get_my_cards(self):
        return self.my_cards_region.recognize_cards()

    def _find_landlord_mark(self, screenshot: np.ndarray):
        logger.info("正在寻找地主标记...")

        # 为每个区域截图
        list(map(lambda region: region.capture(screenshot), self.landlord_marker.values()))
        
        # 匹配并获取匹配结果置信度和位置
        results = [
            (confidence, location)
            for confidence, location in best_template_match(
            region.region_screenshot, MARKS["Landlord"]
        )]

        return results
    
    def is_game_started(self, screenshot: np.ndarray):
        confidences = zip(*self._find_landlord_mark(screenshot))[0]
        logger.debug(f"置信度为：{confidences}")

        return any(confidences >= THRESHOLDS["landlord"])

    def determine_landlord_location(self, screenshot):
        # 找到置信度/匹配度最高地主标记的x坐标
        best_match_x = max(
            self._find_landlord_mark(screenshot),
            key=lambda x: x[0]
        )[1][1]
        logger.debug(f"地主标记x坐标为 {best_match_x}")

        # 判断地主是谁
        if best_match_x < REGIONS["remaining_cards_middle"][0]:
            return Landlord.LEFT
        elif best_match_x < REGIONS["remaining_cards_right"][0]:
            return Landlord.MIDDLE
        else:
            return Landlord.RIGHT

    def is_game_ended(self, screenshot: np.ndarray):
        logger.info("正在计算底牌区域白色占比...")

        # 从截图中提取底牌区域图片
        self.game_end_marker.capture(screenshot)
        
        # 计算白色在图片中的占比
        percentage = color_percentage(
            self.game_end_marker.region_screenshot, (255, 255, 255)
        )
        logger.debug(f"底牌区域白色占比为 {percentage}")

        return percentage > THRESHOLDS["end-game"]
