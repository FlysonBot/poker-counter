import cv2
import numpy as np


def calculate_color_percentage(image, target_color, tolerance=30):
    """
    计算图片中特定颜色的占比
    :param image: 输入图像（BGR 或灰度格式）
    :param target_color: 目标颜色（BGR 值或灰度值）
    :param tolerance: 颜色容差
    :return: 目标颜色占比（0 到 1 之间的浮点数）
    """
    # 将目标颜色转换为 NumPy 数组
    target_color = np.array(target_color, dtype=np.uint8)

    # 如果图像是灰度图，调整目标颜色的形状
    if len(image.shape) == 2:
        target_color = target_color.mean() if len(target_color) > 1 else target_color

    lower_bound = np.clip(target_color - tolerance, 0, 255)
    upper_bound = np.clip(target_color + tolerance, 0, 255)

    # 创建掩码
    mask = cv2.inRange(image, lower_bound, upper_bound)

    # 计算目标颜色的像素数量
    target_pixels = np.count_nonzero(mask)

    # 计算总像素数量
    total_pixels = image.shape[0] * image.shape[1]

    # 返回目标颜色占比
    return target_pixels / total_pixels
