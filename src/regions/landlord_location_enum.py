"""
地主位置枚举模块，定义地主位置的枚举值。
"""

from enum import Enum


class LandlordLocation(Enum):
    """
    地主位置枚举类，定义地主位置的枚举值。
    """

    LEFT = 0  # 上家是地主
    MIDDLE = 1  # 我是地主
    RIGHT = 2  # 下家是地主
