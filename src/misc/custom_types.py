"""
自定义类型模块，定义图像类型和匹配结果类型。
"""

import tkinter as tk
from enum import Enum
from typing import Any, TypeVar

import numpy as np

from models.enum import Card

AnyEnum = TypeVar("AnyEnum", bound=Enum)

RGB = tuple[int, int, int]
AnyImage = np.ndarray[Any, np.dtype[np.uint8]]
GrayscaleImage = np.ndarray[tuple[int, int], np.dtype[np.uint8]]
Confidence = float
Location = tuple[int, int]
MatchResult = tuple[Confidence, Location]
CardDict = dict[Card, int]
CardVarDict = dict[Card, tk.IntVar]
EnumTemplateDict = dict[AnyEnum, AnyImage]
ConfigDict = dict[str, Any]
