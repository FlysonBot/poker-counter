"""
区域管理器，负责截取和更新游戏区域的状态
"""

from typing import Tuple

import numpy as np

from exceptions import GameStateError
from logger import logger
from regions.region_state import RegionState

Coordinate = Tuple[int, int]


class Region:
    """
    管理游戏区域的截取和牌面识别
    """

    def __init__(self, top_left: Coordinate, bottom_right: Coordinate):
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.state = RegionState.WAIT

        self.is_landlord = False
        self.is_me = False

        logger.debug(f"初始化区域：{top_left} -> {bottom_right}")

    def capture(self, image: np.ndarray) -> None:
        """
        从图像中截取区域
        """
        x1, y1 = self.top_left
        x2, y2 = self.bottom_right
        region_screenshot = image[y1:y2, x1:x2]
        if region_screenshot.size == 0:
            raise GameStateError(
                f"无效区域截图：{self.top_left} -> {self.bottom_right}"
            )
        self.region_screenshot = region_screenshot
