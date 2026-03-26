"""
本文件定义程序中所有用到的枚举类型。枚举将一组固定选项定义为具名常量，
便于类型分析工具检查、也能将变量的合法取值限制在预定义的集合内。
"""

from enum import Enum


class Card(Enum):
    """扑克牌面值，大小王不作区分统一用 JOKER 表示。"""

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
    """游戏画面中的特殊标记，不代表具体的牌。"""

    LANDLORD = "Landlord"
    WARNING = "WARNING"  # 游戏弹出警告窗口，会遮挡牌面，检测到后应跳过该帧


class Player(Enum):
    """三个玩家的座位方向，以自己为中心。"""

    LEFT = "上家"
    MIDDLE = "自己"
    RIGHT = "下家"


class WindowsType(Enum):
    """程序显示的三个悬浮计牌窗口。"""

    MAIN = "主窗口"
    LEFT = "左窗口"
    RIGHT = "右窗口"
