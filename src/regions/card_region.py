"""
牌区域模块，负责管理牌区域的截图、状态更新，和牌识别。
"""

from config import THRESHOLDS
from image_processing import (
    MARKS,
    best_template_match,
    color_percentage,
    identify_cards,
)
from logger import logger

from .region import Region
from .region_state import RegionState


class CardRegion(Region):
    """
    牌区域类，负责管理牌区域的截图、状态更新，和牌识别。
    """

    def update_state(self) -> None:
        """
        更新区域状态，判断区域是否处于等待、出牌或不出牌状态。
        """

        # 先检查是否为PASS状态
        confidences, _ = best_template_match(self.region_screenshot, MARKS["PASS"])
        if confidences > THRESHOLDS["pass"]:
            self.state = RegionState.PASS
            logger.debug("更新区域状态为: PASS")
            return

        # 检查是否为WAIT状态
        wait_color_percentage: float = color_percentage(
            self.region_screenshot, (118, 40, 75)
        )
        if wait_color_percentage > THRESHOLDS["wait"]:
            self.state = RegionState.WAIT
            logger.debug("更新区域状态为: WAIT")
            return

        # 否则的话状态为ACTIVE
        self.state = RegionState.ACTIVE
        logger.debug("更新区域状态为: ACTIVE")

    def recognize_cards(self) -> dict[str, int]:
        """
        识别区域内的牌。

        :return: 识别出的牌及其数量的字典
        """

        if self.state != RegionState.ACTIVE:
            logger.warning("尝试在非活跃区域（出了牌的区域）进行识牌")
            return {}

        return identify_cards(self.region_screenshot, THRESHOLDS["card"])
