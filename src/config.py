"""
应用程序配置
"""
import logging
from pathlib import Path
from typing import Dict, Tuple

# 区域坐标配置 (单位: 像素)
REGIONS: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]] = {
    "playing_left": ((260, 346), (700, 446)),
    "playing_middle": ((425, 500), (970, 710)),
    "playing_right": ((700, 346), (1140, 446)),
    "my_cards": ((350, 730), (1020, 820)),
    "20cards_left": ((20, 555), (85, 580)),
    "20cards_middle": ((765, 900), (830, 930)),
    "20cards_right": ((1310, 555), (1380, 580)),
    "3_shown_cards": ((540,120), (860,140)),
}

# 打牌界面分3份，取两条分割线坐标
DIVIDER_LEFT = 600
DIVIDER_RIGHT = 900

# 模板匹配阈值
THRESHOLDS = {
    "pass": 0.9,
    "wait": 0.9,
    "landlord": 0.95,
    "card": 0.95,
    "end-game": 0.25,
}

# 间隔（秒）
SCREENSHOT_INTERVAL = 0.2  # 截图间隔
GUI_UPDATE_INTERVAL = 0.2  # 画面更新间隔
GAME_START_INTERVAL = 1  # 等待下一次判断游戏开始时的间隔

# 记牌器窗口默认显示位置坐标(OFFSET和CENTER二选一)
GUI_LOCATION = {
    #"OFFSET_X": 0,  # 左上角起始X坐标
    "OFFSET_Y": 0,  # 左上角起始Y坐标
    "CENTER_X": 700,  # 中心X坐标
    #"CENTER_Y": 0,  # 中心Y坐标
}

# 其他参数
FONT_SIZE = 25
LOG_PATH = Path.home() / "poker-counter.log"
LOG_LEVEL = logging.INFO
