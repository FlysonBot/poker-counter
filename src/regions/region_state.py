"""
区域状态枚举模块，定义区域状态的枚举值。
"""

from enum import Enum


class RegionState(Enum):
    """
    区域状态枚举
    """

    WAIT = 0  # 等待出牌
    ACTIVE = 1  # 已出牌
    PASS = 2  # 不出牌
