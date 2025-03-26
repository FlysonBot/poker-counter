"""
截图模块，负责截取屏幕截图并更新当前截图。
"""

from dataclasses import dataclass
from time import sleep

import cv2
import numpy as np
from loguru import logger
from PIL import ImageGrab

from misc.custom_types import GrayscaleImage
from misc.singleton import singleton


def _take_screenshot() -> GrayscaleImage:
    """尝试截取屏幕截图，并将其转换为灰度图像。如果截图失败，则重试2秒后重试"""
    try:
        return cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)  # type: ignore

    except OSError:
        logger.info("截图失败，可能是屏幕超时。将在2秒后重试。")
        sleep(2)
        image = None

        while True:
            try:
                image = cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_BGR2GRAY)
                logger.info("截图成功")
                return image  # type: ignore

            except OSError:
                logger.debug("截图失败，将在2秒后重试。")
                sleep(2)


@singleton
@dataclass
class Screenshot:
    """截图类，用于截取屏幕截图并更新当前截图"""

    def __post_init__(self) -> None:
        self.update()

    def update(self) -> None:
        """更新截图"""
        self.image = _take_screenshot()


screenshot = Screenshot()
