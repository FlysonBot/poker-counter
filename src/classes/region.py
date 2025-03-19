from enum import Enum

import cv2

from classes.card_identifier import CardsIdentifier
from config import THRESHOLD
from functions.color_percentage import calculate_color_percentage
from functions.image_match import match_template_best_result
from logger import logger


class State(Enum):
    """
    区域状态
    """

    WAIT = 0  # 等待出牌
    ACTIVE = 1  # 已出牌
    PASS = 2  # 不出牌


class Region:
    def __init__(self, top_left, bottom_right):
        """
        初始化区域模块
        :param top_left: 区域左上角坐标 (x1, y1)
        :param bottom_right: 区域右下角坐标 (x2, y2)
        """
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.state = State.WAIT
        self.is_landlord = False
        self.is_me = False

    def capture_region(self, image):
        """
        从图像中截取区域
        :param image: 输入图像（NumPy 数组）
        :return: 截取的区域图像
        """
        x1, y1 = self.top_left
        x2, y2 = self.bottom_right
        self.image = image[y1:y2, x1:x2]

    def update_region_state(self):
        """
        更新区域状态
        """
        # 首先判断区域是否是PASS状态
        if (
            match_template_best_result(self.image, cv2.imread("templates/PASS.png", 0))[
                0
            ]
            > THRESHOLD["pass"]
        ):
            logger.debug("区域是PASS状态")
            self.state = State.PASS
            return

        # 判断区域是否是WAIT状态
        if calculate_color_percentage(self.image, (118, 40, 75)) > THRESHOLD["wait"]:
            logger.debug("区域是WAIT状态")
            self.state = State.WAIT
            return

        logger.debug("区域是ACTIVE状态")
        self.state = State.ACTIVE

    def recognize_cards(self):
        """
        识别区域内的牌
        :return: 识别结果（字典，键为牌面名称，值为数量）
        """
        # 调用 CardMatcher 识别牌
        return CardsIdentifier(self.image).detect_all_cards()
