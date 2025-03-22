"""
窗口类型枚举模块，定义窗口类型的枚举值。
"""

from enum import Enum


class WindowsType(Enum):
    """
    窗口类型枚举
    """

    MAIN = "主窗口"
    LEFT = "左窗口"
    RIGHT = "右窗口"
