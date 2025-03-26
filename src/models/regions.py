"""
区域模块，负责监控和识别图片中的区域以识别牌型。
"""

from dataclasses import dataclass

from loguru import logger

from functions.color_percentage import color_percentage
from functions.match_template import MARK_TEMPLATES, best_template_match, identify_cards
from misc.custom_types import CardDict, GrayscaleImage
from models.config import THRESHOLDS

from .enum import Mark, RegionState
from .screenshot import screenshot


@dataclass
class Region:
    """区域类，用于监控和识别图片中的区域"""

    TOP_LEFT: tuple[int, int]
    BOTTOM_RIGHT: tuple[int, int]

    def __post_init__(self) -> None:
        """初始化区域状态并提取区域坐标"""
        self.state: RegionState = RegionState.WAIT
        self._X1: int = self.TOP_LEFT[0]
        self._Y1: int = self.TOP_LEFT[1]
        self._X2: int = self.BOTTOM_RIGHT[0]
        self._Y2: int = self.BOTTOM_RIGHT[1]

    @property
    def region_screenshot(self) -> GrayscaleImage:
        """返回区域截图"""
        return screenshot.image[self._Y1 : self._Y2, self._X1 : self._X2]  # type: ignore

    def update_state(self) -> None:
        """更新区域状态"""
        if self._is_pass:
            self.state = RegionState.PASS
            return logger.debug("更新区域状态为: PASS")
        if self._is_wait:
            self.state = RegionState.WAIT
            return logger.debug("更新区域状态为: WAIT")
        self.state = RegionState.ACTIVE
        return logger.debug("更新区域状态为: ACTIVE")

    @property
    def _is_pass(self) -> bool:
        confidence = best_template_match(
            self.region_screenshot, MARK_TEMPLATES[Mark.PASS]
        )
        logger.debug(f"PASS标记置信度为: {confidence}")
        return confidence > THRESHOLDS["pass"]

    @property
    def _is_wait(self) -> bool:
        blue_percentage = color_percentage(self.region_screenshot, (118, 40, 75))
        logger.debug(f"区域背景蓝色占比为: {blue_percentage}")
        return blue_percentage > THRESHOLDS["wait"]

    def recognize_cards(self) -> CardDict:  # type: ignore
        """识别区域中的牌"""
        if self.state is not RegionState.ACTIVE:
            logger.warning("尝试在非活跃区域（出了牌的区域）进行识牌")
        return identify_cards(self.region_screenshot, THRESHOLDS["card"])
