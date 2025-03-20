"""
区域模块的初始化文件，导出牌区域、区域和区域状态类。
"""

from .card_region import CardRegion
from .region import Region
from .region_state import RegionState
from .landlord_location_enum import LandlordLocation

__all__ = [
    "CardRegion",
    "Region",
    "RegionState",
    "LandlordLocation",
]
