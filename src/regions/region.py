"""
区域管理器，负责截取和更新游戏区域的状态
"""

from typing import Tuple

from exceptions import GameStateError
from logger import logger
from regions.region_state import RegionState
from image_processing import AnyImage

Coordinate = Tuple[int, int]


class Region:
    """
    管理游戏区域的截取和牌面识别
    """

    def __init__(self, top_left: Coordinate, bottom_right: Coordinate) -> None:
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.state = RegionState.WAIT

        self.is_landlord = False
        self.is_me = False

        logger.debug(f"初始化区域：{top_left} -> {bottom_right}")

    def capture(self, image: AnyImage) -> None:
        """
        从图像中截取区域
        """
        x1, y1 = self.top_left
        x2, y2 = self.bottom_right
        region_screenshot: AnyImage = image[y1:y2, x1:x2]
        if region_screenshot.size == 0:
            raise GameStateError(
                f"无效区域截图：{self.top_left} -> {self.bottom_right}"
            )
        self.region_screenshot: AnyImage = region_screenshot
