"""
截图与窗口定位模块。

负责定位游戏窗口、截取灰度截图，以及将 config.yaml 中的比例坐标转换为像素坐标。
截图使用 mss，默认不捕获本程序自身的悬浮窗叠加层。
窗口定位依赖 pygetwindow，仅在 Windows 上可用；其他平台自动 fallback 到全屏截图。
"""

from time import sleep
from typing import Optional

import cv2
import mss
import numpy as np
from loguru import logger

from config import GAME_WINDOW_TITLE, REGIONS

# 类型别名，让函数签名更易读。
GrayImage = np.ndarray  # shape (H, W), dtype uint8，表示一张灰度图
Rect = tuple[int, int, int, int]  # (x1, y1, x2, y2) 像素坐标，相对于全屏左上角


# ---------------------------------------------------------------------------
# 窗口定位
# ---------------------------------------------------------------------------


def _full_screen_rect() -> Rect:
    """返回主屏幕的全屏坐标 (0, 0, width, height)。"""

    with mss.mss() as sct:
        # monitors[0] 是所有显示器合并后的虚拟屏幕，monitors[1] 起才是单个显示器
        m = sct.monitors[0]
        return 0, 0, m["width"], m["height"]


def find_game_window() -> Rect:
    """查找游戏窗口，返回其屏幕坐标 (x1, y1, x2, y2)。
    找不到时 fallback 到全屏坐标。
    仅在 Windows 上可用（依赖 pygetwindow）。
    """

    try:
        import pygetwindow as gw

        # 遍历所有窗口，找到标题中包含游戏关键字的窗口
        wins = [w for w in gw.getAllWindows() if GAME_WINDOW_TITLE in w.title]
        if not wins:
            logger.warning(f"未找到标题含 '{GAME_WINDOW_TITLE}' 的窗口，将使用全屏截图")
            return _full_screen_rect()
        w = wins[0]
        return w.left, w.top, w.left + w.width, w.top + w.height
    except ImportError:
        logger.warning("pygetwindow 不可用（非 Windows 环境），将截取全屏")
        return _full_screen_rect()
    except Exception as e:
        logger.warning(f"窗口定位失败: {e}")
        return _full_screen_rect()


# ---------------------------------------------------------------------------
# 截图
# ---------------------------------------------------------------------------


def _grab_gray(bbox: Optional[tuple] = None) -> GrayImage:
    """截取屏幕（或指定区域）并转为灰度图。
    mss 返回 BGRA 格式，cv2.COLOR_BGRA2GRAY 权重为 0.299*B + 0.587*G + 0.114*R，
    与旧版 PIL channel-flip 技巧的加权结果完全一致。
    mss 默认支持多显示器且不捕获叠加层窗口（如本程序自身的悬浮窗）。
    """

    with mss.mss() as sct:
        # 如果指定了区域，则只截取该区域；否则截取整个主屏幕
        monitor = (
            {
                "left": bbox[0],
                "top": bbox[1],
                "width": bbox[2] - bbox[0],
                "height": bbox[3] - bbox[1],
            }
            if bbox
            else sct.monitors[0]
        )
        raw = sct.grab(monitor)
    bgra = np.array(raw)
    return cv2.cvtColor(bgra, cv2.COLOR_BGRA2GRAY)


def take_screenshot(
    window_rect: Optional[Rect] = None, stop_event=None
) -> Optional[GrayImage]:
    """截取游戏窗口截图（灰度）。
    window_rect 为 None 时截全屏（Linux / 窗口未找到时的 fallback）。
    截图失败（如屏幕超时锁屏）时每 2 秒自动重试，直到成功或收到停止信号为止。
    收到停止信号时返回 None。
    """

    bbox = window_rect  # PIL bbox 格式与 Rect 一致：(left, top, right, bottom)
    logger.debug("正在截图...")
    while True:
        try:
            return _grab_gray(bbox)
        except Exception:
            # 截图失败时检查是否应该退出，否则等待后重试
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
    """

    # 从配置中取出该区域的左上角和右下角比例坐标
    (rx1, ry1), (rx2, ry2) = REGIONS[region_name]

    # 计算窗口的实际宽高（像素）
    wx1, wy1, wx2, wy2 = window_rect
    w = wx2 - wx1
    h = wy2 - wy1

    # 将比例坐标乘以实际尺寸，得到截图内的像素坐标
    return (
        round(rx1 * w),
        round(ry1 * h),
        round(rx2 * w),
        round(ry2 * h),
    )
