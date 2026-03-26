"""
模板缩放比例自动校准模块。

在地主确定后、记牌开始前，通过分析 my_cards 区域的手牌高度，
自动计算当前屏幕分辨率下的模板缩放比例（TEMPLATE_SCALE）。

算法：
1. 用低亮度阈值二值化，让整排手牌连成一大块白色
2. 裁剪区域：左/右/上 = my_cards 边界，下延伸到帧底（防止牌被截断）
3. 找最大连通块（整排手牌）
4. 对连通块按行做水平投影，过滤弹出牌造成的稀疏行
5. 用有效行高度 / 参考高度得出 scale
失败时 fallback 到 1.0。
"""

import cv2
import numpy as np
from loguru import logger

from recognition.capture import GrayImage, Rect, region_to_pixels

# 低阈值：确保整张牌（含渐变背景）都变白，牌间细边框可以消失
_BRIGHTNESS_THRESHOLD = 130

# 每行白色像素占连通块宽度的比例低于此值，视为弹出牌的稀疏行，忽略
_ROW_DENSITY_MIN = 0.7

# 参考分辨率下单张牌的实际高度（scale=1.0 时的基准）
_CARD_REF_HEIGHT = 126


def calibrate_scale(frame: GrayImage, window_rect: Rect) -> float:
    """根据当前帧的手牌区域自动估算模板缩放比例。失败时返回 1.0。"""

    try:
        return _calibrate(frame, window_rect)
    except Exception as e:
        logger.warning(f"scale 自动校准失败，使用默认值 1.0：{e}")
        return 1.0


def _calibrate(frame: GrayImage, window_rect: Rect) -> float:
    frame_h, frame_w = frame.shape

    # my_cards 区域在全帧中的像素坐标（只取左/右/上边界，下边界延伸到帧底）
    rx1, ry1, rx2, _ = region_to_pixels("my_cards", window_rect)

    # 裁剪手牌区域，下边界延伸到帧底以防止手牌被截断
    crop = frame[ry1:frame_h, rx1:rx2]
    crop_w = rx2 - rx1
    if crop_w <= 0 or crop.size == 0:
        logger.warning("my_cards 区域无效，校准失败")
        return 1.0

    # 低阈值二值化：亮度超过阈值的像素变白，其余变黑，让整排手牌连成一大块
    _, binary = cv2.threshold(crop, _BRIGHTNESS_THRESHOLD, 255, cv2.THRESH_BINARY)

    # 找所有连通块，取面积最大的那个（即整排手牌构成的白色区域）
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        logger.warning("二值化后未找到连通块，校准失败")
        return 1.0

    areas = [(stats[i, cv2.CC_STAT_AREA], i) for i in range(1, num_labels)]
    _, best_label = max(areas)
    s = stats[best_label]
    bx = int(s[cv2.CC_STAT_LEFT])
    by = int(s[cv2.CC_STAT_TOP])
    bw = int(s[cv2.CC_STAT_WIDTH])
    bh = int(s[cv2.CC_STAT_HEIGHT])

    # 水平投影：统计连通块每一行的白色像素密度，过滤弹出牌造成的稀疏行
    block_rows = binary[by : by + bh, bx : bx + bw]
    row_sums = np.sum(block_rows == 255, axis=1)  # 每行的白色像素数
    row_density = row_sums / bw  # 转换为占连通块宽度的比例
    dense_rows = np.where(row_density >= _ROW_DENSITY_MIN)[0]  # 保留密度足够高的行

    if len(dense_rows) == 0:
        logger.warning("水平投影过滤后无有效行，校准失败")
        return 1.0

    # 用最高和最低有效行的跨度作为实际牌高，除以参考高度得出缩放比例
    card_height = int(dense_rows[-1] - dense_rows[0] + 1)
    scale = card_height / _CARD_REF_HEIGHT
    logger.info(
        f"scale 自动校准完成：牌高={card_height}px，参考高度={_CARD_REF_HEIGHT}px，scale={scale:.3f}"
    )
    return scale
