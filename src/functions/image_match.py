from typing import Sequence

import cv2
import numpy as np


def match_template_best_result(
    target_image, template_image
) -> tuple[float, Sequence[int]]:
    """Match a single template in the target image and return location and value if found"""
    result = cv2.matchTemplate(target_image, template_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc


def match_template_by_threshold(
    target_image, template_image, threshold
) -> list[tuple[float, Sequence[int]]]:
    """Match a single template in the target image and return locations and values of matches above the threshold."""
    result = cv2.matchTemplate(target_image, template_image, cv2.TM_CCOEFF_NORMED)

    # 获取高于阈值的匹配结果的位置
    locations = np.where(result >= threshold)
    matches = []

    # 提取匹配结果并将其转换为元组
    for pt in zip(*locations[::-1]):
        value: float = result[pt[1], pt[0]]
        matches.append((value, pt))

    return matches
