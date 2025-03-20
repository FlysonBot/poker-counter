from typing import Union

import cv2
import numpy as np

from .image_types import AnyImage, RGB

def color_percentage(
    image: AnyImage, target_color: Union[RGB, int], tolerance: int = 30
) -> float:
    """
    计算图片中特定颜色的占比
    :param image: 输入图像（BGR 或灰度格式）
    :param target_color: 目标颜色（BGR 值或灰度值）
    :param tolerance: 颜色容差
    :return: 目标颜色占比（0 到 1 之间的浮点数）
    """
    # 将目标颜色转换为 NumPy 数组以方便操作
    np_color = np.array(target_color, dtype=np.uint8)

    # 如果图像是灰度图（只有两个维度），调整目标颜色为灰度值
    if len(image.shape) == 2:
        # 如果目标颜色是彩色（维度大于1），取BGR平均值作为灰度值
        np_color = np_color.mean() if len(np_color) > 1 else np_color

    # 根据颜色容差计算颜色匹配范围
    lower_bound = np.clip(np_color - tolerance, 0, 255)
    upper_bound = np.clip(np_color + tolerance, 0, 255)

    # 根据范围创建掩码（输出为一个数组，0代表超出范围，255代表在范围内）
    mask = cv2.inRange(image, lower_bound, upper_bound)

    # 计算目标颜色的像素数量（通过统计掩码中非0的数值）
    target_pixels = np.count_nonzero(mask)

    # 计算总像素数量
    total_pixels = image.shape[0] * image.shape[1]

    # 返回目标颜色占比
    return target_pixels / total_pixels
