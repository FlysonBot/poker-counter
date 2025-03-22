"""
游戏状态模块，负责监控游戏状态并识别牌局中的牌。
"""

from time import sleep

import cv2
import numpy as np
from PIL import ImageGrab

from config import REGIONS, THRESHOLDS
from image_processing import (
    MARKS,
    GrayscaleImage,
    best_template_match,
)
from logger import logger
from regions import CardRegion, LandlordLocation, Region
from regions.region_state import RegionState


class GameState:
    """
    游戏状态类，负责监控游戏状态并识别牌局中的牌。
    """

    def __init__(self) -> None:
        """
        初始化游戏状态，设置游戏区域和其他标记区域。
        """

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

        self.game_end_marker = CardRegion(*REGIONS["three_displayed_cards"])
        self.my_cards_region = CardRegion(*REGIONS["my_cards"])
        self.game_end_marker.state = RegionState.ACTIVE
        self.my_cards_region.state = RegionState.ACTIVE

        self._reset_flag = False  # 通过窗口手动重置的标记

        logger.success("所有区域初始化完毕")

    def manual_reset(self) -> None:
        """
        手动重置记牌器。
        """

        self._reset_flag = True

    def get_screenshot(self) -> GrayscaleImage:
        """
        获取当前屏幕截图。

        :return: 灰度截图
        """

        try:
            return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)  # type: ignore

        except OSError:
            logger.info("截图失败，可能是屏幕超时。将在2秒后重试。")
            sleep(2)

            while True:
                try:
                    return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)  # type: ignore

                except OSError:
                    logger.trace("截图失败，将在2秒后重试。")
                    sleep(2)

    def get_my_cards(self) -> dict[str, int]:
        """
        获取当前玩家的手牌。

        :return: 手牌字典
        """

        logger.trace("正在识别当前玩家的手牌...")
        cards = self.my_cards_region.recognize_cards()
        logger.info(f"当前玩家的手牌为：{cards}")

        return cards

    def _find_landlord_mark(self, screenshot: GrayscaleImage) -> list[float]:
        """
        寻找地主标记。

        :param screenshot: 屏幕截图
        :return: 地主标记的置信度和位置
        """

        logger.trace("正在寻找地主标记...")

        # 为每个区域截图
        regions = self.landlord_marker.values()
        list(map(lambda region: region.capture(screenshot), regions))

        # 匹配并获取匹配结果置信度
        results = map(
            lambda region: best_template_match(
                region.region_screenshot, MARKS["Landlord"]
            ),
            regions,
        )

        return [result[0] for result in results]

    def is_game_started(self, screenshot: GrayscaleImage) -> bool:
        """
        判断游戏是否开始。

        :param screenshot: 屏幕截图
        :return: 游戏是否开始
        """

        confidences = self._find_landlord_mark(screenshot)

        max_confidence: float = max(confidences)
        logger.trace(f"地主标记匹配置信度为：{max_confidence}")

        return max_confidence >= THRESHOLDS["landlord"]

    def find_landlord_location(self, screenshot: GrayscaleImage) -> LandlordLocation:
        """
        确定地主的位置。

        :param screenshot: 屏幕截图
        :return: 地主位置
        """

        logger.debug("正在确定地主位置...")
        logger.debug(self._find_landlord_mark(screenshot))

        # 计算地主标记的匹配置信度
        confidences = self._find_landlord_mark(screenshot)
        max_confidence = max(confidences)
        max_index = confidences.index(max_confidence)
        logger.debug(f"地主标记匹配置信度为：{max_confidence}")

        # 根据匹配区域的位置判断地主是谁
        if max_index == 0:
            logger.info("地主是上家")
            return LandlordLocation.LEFT
        if max_index == 1:
            logger.info("地主是自己")
            return LandlordLocation.MIDDLE
        logger.info("地主是下家")
        return LandlordLocation.RIGHT

    def is_game_ended(self, screenshot: GrayscaleImage) -> bool:
        """
        判断游戏是否结束。

        :param screenshot: 屏幕截图
        :return: 游戏是否结束
        """

        if self._reset_flag:
            self._reset_flag = False
            return True

        logger.trace("正在识别底牌区域的牌...")

        self.game_end_marker.capture(screenshot)  # 从截图中提取底牌区域图片
        cards = self.game_end_marker.recognize_cards()  # 识牌
        logger.trace(f"底牌区域的牌为：{cards}")

        return len(cards) > 0
