"""
模板匹配模块，通过模板匹配来识别图片中的牌和标记。
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
    """
    根据指定阀值识别图片中指定的模板图片并返回匹配的结果。

    :param target: 目标图像
    :param template: 模板图像
    :param threshold: 匹配阈值
    :return: 匹配的结果列表（包含置信度和位置）
    """
    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)

    return [(result[pt[1], pt[0]], pt) for pt in zip(*locations[::-1])]  # type: ignore


def best_template_match(target: AnyImage, template: AnyImage) -> MatchResult:
    """
    返回最佳匹配结果的位置和置信度。

    :param target: 目标图像
    :param template: 模板图像
    :return: 最佳匹配结果的置信度和位置
    """

    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    return max_val, (max_loc[0], max_loc[1])


def identify_cards(image: AnyImage, threshold: float) -> Dict[str, int]:
    """
    识别图像中的所有扑克牌。

    :param image: 输入图像
    :param threshold: 匹配阈值
    :return: 识别出的牌及其数量
    """

    results: dict[str, int] = {}

    for card, template in CARDS.items():
        amount: int = len(template_match(image, template, threshold))

        if amount > 0:
            results[card] = amount
            logger.info(f"检测到 {amount} 张 {card}")

    return results
