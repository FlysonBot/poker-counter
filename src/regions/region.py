"""
区域模块，负责截取区域截图。
"""

from typing import Tuple

from image_processing import AnyImage
from logger import logger
from misc.exceptions import ScreenshotError
from regions.region_state import RegionState

Coordinate = Tuple[int, int]


class Region:
    """
    区域类，负责截取区域截图。
    """

    def __init__(self, top_left: Coordinate, bottom_right: Coordinate) -> None:
        """
        初始化区域。

        :param top_left: 区域左上角坐标
        :param bottom_right: 区域右下角坐标
        """

        self.top_left = top_left
        self.bottom_right = bottom_right
        self.state = RegionState.WAIT

        self.is_landlord = False
        self.is_me = False

        logger.debug(f"初始化区域：{top_left} -> {bottom_right}")

    def capture(self, image: AnyImage) -> None:  # type: ignore
        """
        从图像中截取区域。

        :param image: 输入图像
        """
        x1, y1 = self.top_left
        x2, y2 = self.bottom_right
        region_screenshot: AnyImage = image[y1:y2, x1:x2]
        if region_screenshot.size == 0:
            raise ScreenshotError(
                f"无效区域截图：{self.top_left} -> {self.bottom_right}\n"
                f"提供的图像大小为：{image.size}"
            )
        self.region_screenshot: AnyImage = region_screenshot
