"""
枚举模块，定义各类枚举类型。
"""

from enum import Enum

from loguru import logger


class Card(Enum):
    """卡牌类型"""

    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    J = "J"
    Q = "Q"
    K = "K"
    A = "A"
    TWO = "2"
    JOKER = "JOKER"


class Mark(Enum):
    """标记类型"""

    PASS = "PASS"
    LANDLORD = "Landlord"


class RegionState(Enum):
    """区域状态"""

    WAIT = 0  # 等待出牌
    ACTIVE = 1  # 已出牌
    PASS = 2  # 不出牌


class Player(Enum):
    """玩家类型"""

    LEFT = "上家"
    MIDDLE = "自己"
    RIGHT = "下家"

    def log_landlord(self) -> None:
        """记录地主是谁"""
        logger.info(f"地主是{self.value}")

    def log_region(self) -> None:
        """记录当前区域是哪个"""
        logger.info(f"现在跳转到{self.value}的区域")


class WindowsType(Enum):
    """窗口类型"""

    MAIN = "主窗口"
    LEFT = "左窗口"
    RIGHT = "右窗口"
