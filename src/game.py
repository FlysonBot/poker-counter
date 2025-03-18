from enum import Enum
from itertools import cycle
from time import sleep

import cv2
from PIL import ImageGrab

from image_match import match_template_best_result
from region import Region, State


class Landlord(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


class Game:
    def __init__(self):
        self.left_region = Region((260, 346), (700, 400))
        self.middle_region = Region((425, 500), (970, 560))
        self.right_region = Region((700, 346), (1140, 400))
        self.regions = cycle([self.left_region, self.middle_region, self.right_region])

    def determine_game_start(self, screenshot):
        # 寻找地主标记
        max_val, _ = match_template_best_result(
            screenshot, cv2.imread("templates/Landlord.png", 0)
        )

        # 判断游戏开始
        return max_val >= 0.99

    def determine_landlord(self, screenshot):
        # 寻找地主标记
        _, max_loc = match_template_best_result(
            screenshot, cv2.imread("templates/Landlord.png", 0)
        )

        # 判断地主是谁
        if max_loc[0] < 600:
            return Landlord.LEFT
        elif max_loc[0] < 900:
            return Landlord.MIDDLE
        else:
            return Landlord.RIGHT

    def determine_game_end(self, screenshot):
        # 寻找分数统计标记
        max_val, max_loc = match_template_best_result(
            screenshot, cv2.imread("templates/Score.png", 0)
        )

        # 判断游戏结束
        return (
            max_val > 0.8 and (550 <= max_loc[0] <= 850) and (330 <= max_loc[1] <= 550)
        )


def game_loop(interval, counter):

    while True:
        # 初始化游戏对象
        game = Game()

        # 等待游戏开始
        while not game.determine_game_start(ImageGrab.grab()):
            sleep(1)

        # 初始化
        counter.reset()
        landlord = game.determine_landlord(ImageGrab.grab())
        for _ in range(landlord.value):
            next(game.regions)
        screenshot = ImageGrab.grab()
        current_region = next(game.regions)
        current_region.is_landlord = True  # 标记地主区域

        # 实时记录
        while not game.determine_game_end(screenshot):
            current_region.capture_region(screenshot)
            current_region.update_region_state()

            # 如果区域处于等待状态，则等待
            if current_region.state == State.WAIT:
                sleep(interval)
                continue

            # 如果区域有牌，则识别牌
            if current_region.state == State.ACTIVE:
                cards = current_region.recognize_cards()

                # 标记牌
                for card, count in cards.items():
                    for _ in range(count):
                        counter.mark_card(card)

            # 并更新截图及当前区域
            current_region = next(game.regions)
            screenshot = ImageGrab.grab()
