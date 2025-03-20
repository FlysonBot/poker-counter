from time import sleep

import cv2
import numpy as np
from PIL import ImageGrab

from config import REGIONS, THRESHOLDS
from image_processing import GrayscaleImage, MatchResult
from image_processing.color_percentage import color_percentage
from image_processing.template_match import best_template_match
from image_processing.templates import MARKS
from logger import logger
from regions.card_region import CardRegion
from regions.landlord_enum import Landlord
from regions.region import Region


class GameState:
    def __init__(self) -> None:
        self.card_regions = {
            "left": CardRegion(*REGIONS["playing_left"]),
            "middle": CardRegion(*REGIONS["playing_middle"]),
            "right": CardRegion(*REGIONS["playing_right"]),
        }

        self.landlord_marker = {
            "left": Region(*REGIONS["remaining_cards_left"]),
            "middle": Region(*REGIONS["remaining_cards_middle"]),
            "right": Region(*REGIONS["remaining_cards_right"]),
        }

        self.game_end_marker = Region(*REGIONS["3_displayed_cards"])
        self.my_cards_region = CardRegion(*REGIONS["my_cards"])

    def get_screenshot(self) -> GrayscaleImage:
        try:
            return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)  # type: ignore

        except OSError:
            logger.info(
                "Error taking screenshot (likely due to screen timeout)."
                "Starts to retry every 2 seconds."
            )

            while True:
                try:
                    return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)  # type: ignore

                except OSError:
                    logger.debug("Retrying to take screenshot...")
                    sleep(2)

    def get_my_cards(self) -> dict[str, int]:
        return self.my_cards_region.recognize_cards()

    def _find_landlord_mark(self, screenshot: GrayscaleImage) -> list[MatchResult]:
        logger.info("正在寻找地主标记...")

        # 为每个区域截图
        regions = self.landlord_marker.values()
        list(map(lambda region: region.capture(screenshot), regions))

        # 匹配并获取匹配结果置信度和位置
        return [
            best_template_match(region.region_screenshot, MARKS["Landlord"])
            for region in regions
        ]

    def is_game_started(self, screenshot: GrayscaleImage) -> bool:
        confidences, _ = zip(*self._find_landlord_mark(screenshot))

        confidence = max(confidences)
        logger.debug(f"置信度为：{confidence}")

        return any(confidence >= THRESHOLDS["landlord"])

    def find_landlord_location(self, screenshot: GrayscaleImage):
        # 找到置信度/匹配度最高地主标记的x坐标
        best_match_x: int = max(
            self._find_landlord_mark(screenshot),
            key=lambda x: x[0],  # 取置信度最高的
        )[1][1]  # 取结果中位置的x坐标

        logger.debug(f"地主标记x坐标为 {best_match_x}")

        # 判断地主是谁（通过比较各区域左上角的x坐标）
        if best_match_x < REGIONS["remaining_cards_middle"][0][0]:
            return Landlord.LEFT
        if best_match_x < REGIONS["remaining_cards_right"][0][0]:
            return Landlord.MIDDLE
        return Landlord.RIGHT

    def is_game_ended(self, screenshot: GrayscaleImage):
        logger.info("正在计算底牌区域白色占比...")

        # 从截图中提取底牌区域图片
        self.game_end_marker.capture(screenshot)

        # 计算白色在图片中的占比
        percentage = color_percentage(
            self.game_end_marker.region_screenshot, (255, 255, 255)
        )
        logger.debug(f"底牌区域白色占比为 {percentage}")

        return percentage > THRESHOLDS["end-game"]
