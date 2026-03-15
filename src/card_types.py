from enum import Enum


class Card(Enum):
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
    PASS = "PASS"
    LANDLORD = "Landlord"


class Player(Enum):
    LEFT = "上家"
    MIDDLE = "自己"
    RIGHT = "下家"


class WindowsType(Enum):
    MAIN = "主窗口"
    LEFT = "左窗口"
    RIGHT = "右窗口"
