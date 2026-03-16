"""
截图与窗口定位模块。负责定位游戏窗口、截图并将比例坐标转换为像素坐标。
Windows-only（pygetwindow / PIL.ImageGrab）。
"""

from time import sleep
from typing import Optional

import numpy as np
from loguru import logger
from PIL import Image, ImageGrab

from config import GAME_WINDOW_TITLE, REGIONS, TEMPLATE_SCALE

# 类型别名
GrayImage = np.ndarray  # shape (H, W), dtype uint8
Rect = tuple[int, int, int, int]  # (x1, y1, x2, y2) 像素，相对于全屏


# ---------------------------------------------------------------------------
# 窗口定位
# ---------------------------------------------------------------------------


def find_game_window() -> Optional[Rect]:
    """查找游戏窗口，返回其屏幕坐标 (x1, y1, x2, y2)。
    找不到时返回 None，调用方应 fallback 到全屏截图模式。
    仅在 Windows 上可用（依赖 pygetwindow）。
    """
    try:
        import pygetwindow as gw

        wins = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
        if not wins:
            logger.warning(f"未找到标题含 '{GAME_WINDOW_TITLE}' 的窗口")
            return None
        w = wins[0]
        return (w.left, w.top, w.left + w.width, w.top + w.height)
    except ImportError:
        logger.warning("pygetwindow 不可用（非 Windows 环境），将截取全屏")
        return None
    except Exception as e:
        logger.warning(f"窗口定位失败: {e}")
        return None


# ---------------------------------------------------------------------------
# 截图
# ---------------------------------------------------------------------------


def _grab_gray(bbox: Optional[tuple] = None) -> GrayImage:
    """截取屏幕（或指定区域）并转为灰度图。
    PIL ImageGrab 返回 RGB 格式，这里先把通道顺序反转成 BGR 再转灰度，
    目的是加重蓝色通道、减轻红色通道对灰度值的影响，
    与旧版的 RGB_as_BGR2GRAY 行为保持一致。
    """
    pil_img: Image.Image = ImageGrab.grab(bbox=bbox)
    rgb = np.array(pil_img)
    # [:, :, ::-1] 将 RGB 通道顺序反转为 BGR
    bgr_pil = Image.fromarray(rgb[:, :, ::-1])
    gray = np.array(bgr_pil.convert("L"))
    return gray


def take_screenshot(window_rect: Optional[Rect] = None, stop_event=None) -> Optional[GrayImage]:
    """截取游戏窗口截图（灰度）。
    window_rect 为 None 时截全屏（Linux / 窗口未找到时的 fallback）。
    截图失败（如屏幕超时锁屏）时每 2 秒自动重试，直到成功或收到停止信号为止。
    收到停止信号时返回 None。
    """
    bbox = window_rect  # PIL bbox 格式与 Rect 一致：(left, top, right, bottom)
    while True:
        try:
            return _grab_gray(bbox)
        except Exception:
            if stop_event is not None and stop_event.is_set():
                return None
            logger.warning("截图失败（屏幕可能已超时），2 秒后重试")
            sleep(2)


# ---------------------------------------------------------------------------
# 坐标转换
# ---------------------------------------------------------------------------


def region_to_pixels(region_name: str, window_rect: Rect) -> Rect:
    """将 config.yaml 中的比例坐标转换为截图内的像素坐标。
    比例坐标是相对于窗口尺寸的（0.0–1.0），乘以实际尺寸得到像素值。
    window_rect 为 None 时使用参考分辨率（全屏截图的 fallback）。
    """
    (rx1, ry1), (rx2, ry2) = REGIONS[region_name]

    wx1, wy1, wx2, wy2 = window_rect
    w = wx2 - wx1
    h = wy2 - wy1

    return (
        round(rx1 * w),
        round(ry1 * h),
        round(rx2 * w),
        round(ry2 * h),
    )
