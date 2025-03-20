"""
通过模板匹配来识别图片中的牌
"""

from typing import Dict

import cv2
import numpy as np

from image_processing.templates import CARDS
from logger import logger


def template_match(target: np.ndarray, template: np.ndarray, threshold: float):
    """根据指定阀值识别图片中指定的模板图片并返回匹配的结果的位置"""
    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)

    return [(result[pt[1], pt[0]], pt) for pt in zip(*locations[::-1])]


def best_template_match(target: np.ndarray, template: np.ndarray):
    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    return max_val, max_loc


def identify_cards(image: np.ndarray, threshold: float) -> Dict[str, int]:
    """识别图像中的扑克牌"""
    results = {}

    for card, template in CARDS.items():
        amount = len(template_match(image, template, threshold))

        if amount > 0:
            results[card] = amount
            logger.info(f"检测到 {amount} 张 {card}")

    return results
