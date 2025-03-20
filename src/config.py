"""
应用程序配置模块，包含游戏区域坐标、模板匹配阈值、日志路径等配置。
"""

import logging
from pathlib import Path
from typing import Dict, Tuple

# 区域坐标配置 (单位: 像素)
REGIONS: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]] = {
    "playing_left": ((260, 346), (700, 446)),  # 左侧出牌区域
    "playing_middle": ((425, 500), (970, 710)),  # 中间出牌区域
    "playing_right": ((700, 346), (1140, 446)),  # 右侧出牌区域
    "my_cards": ((350, 730), (1020, 820)),  # 中间我的所有牌的显示区域
    "remaining_cards_left": ((20, 555), (85, 580)),  # 左边剩余牌数显示区域
    "remaining_cards_middle": ((765, 900), (830, 930)),  # 中间剩余牌数显示区域
    "remaining_cards_right": ((1310, 555), (1380, 580)),  # 右边剩余牌数显示区域
    "3_displayed_cards": ((540, 120), (860, 140)),  # 游戏结束时上方三张底牌的显示区域
}

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
    # "OFFSET_X": 0,  # 左上角起始X坐标
    "OFFSET_Y": 0,  # 左上角起始Y坐标
    "CENTER_X": 700,  # 中心X坐标
    # "CENTER_Y": 0,  # 中心Y坐标
}

# 其他参数
FONT_SIZE = 25
LOG_PATH = Path.home() / "poker-counter.log"
LOG_LEVEL = logging.INFO
