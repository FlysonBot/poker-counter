"""
图像类型模块，定义图像类型和匹配结果类型。
"""

from typing import Any

import numpy as np

RGB = tuple[int, int, int]
AnyImage = np.ndarray[Any, np.dtype[np.uint8]]
GrayscaleImage = np.ndarray[tuple[int, int], np.dtype[np.uint8]]
Confidence = float
Location = tuple[int, int]
MatchResult = tuple[Confidence, Location]
