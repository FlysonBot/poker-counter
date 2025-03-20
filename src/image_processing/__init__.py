"""
图像处理模块的初始化文件，导出颜色占比计算、模板匹配和自定义图像类型。
"""

from .color_percentage import color_percentage
from .image_types import RGB, AnyImage, GrayscaleImage, MatchResult
from .template_match import best_template_match, identify_cards, template_match
from .templates import CARDS, MARKS

__all__ = [
    "color_percentage",
    "template_match",
    "best_template_match",
    "identify_cards",
    "CARDS",
    "MARKS",
    "GrayscaleImage",
    "AnyImage",
    "RGB",
    "MatchResult",
]
