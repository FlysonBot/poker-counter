"""
通过模板匹配来识别图片中的牌
"""

from typing import Dict

import cv2
import numpy as np

from logger import logger

from .image_types import AnyImage, MatchResult
from .templates import CARDS


def template_match(
    target: AnyImage, template: AnyImage, threshold: float
) -> list[MatchResult]:
    """根据指定阀值识别图片中指定的模板图片并返回匹配的结果的位置"""
    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)

    return [(result[pt[1], pt[0]], pt) for pt in zip(*locations[::-1])]  # type: ignore


def best_template_match(target: AnyImage, template: AnyImage) -> MatchResult:
    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    return max_val, (max_loc[0], max_loc[1])


def identify_cards(image: AnyImage, threshold: float) -> Dict[str, int]:
    """识别图像中的扑克牌"""
    results: dict[str, int] = {}

    for card, template in CARDS.items():
        amount = len(template_match(image, template, threshold))

        if amount > 0:
            results[card] = amount
            logger.info(f"检测到 {amount} 张 {card}")

    return results
