from enum import Enum
from itertools import cycle
from time import sleep

import cv2
from PIL import ImageGrab

from image_match import match_single_template
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
        max_val, _ = match_single_template(
            screenshot, cv2.imread("templates/Landlord.png", 0)
        )

        # 判断游戏开始
        return max_val >= 0.99

    def determine_landlord(self, screenshot):
        # 寻找地主标记
        _, max_loc = match_single_template(
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
        _, max_loc = match_single_template(
            screenshot, cv2.imread("templates/Score.png", 0)
        )

        # 判断游戏结束
        return (550 <= max_loc[0] <= 850) and (330 <= max_loc[1] <= 550)


def game_loop():
    while True:
        # 初始化游戏对象
        game = Game()

        # 等待游戏开始
        while not game.determine_game_start(ImageGrab.grab()):
            sleep(1)

        # 初始化
        landlord = game.determine_landlord(ImageGrab.grab())
        for _ in range(landlord.value):
            next(game.regions)

        # 实时记录
        interval = 0.2
        screenshot = ImageGrab.grab()
        region = next(game.regions)

        while not game.determine_game_end(screenshot):
            region.capture_region(screenshot)
            region.update_region_state()

            if region.state == State.WAIT:
                sleep(interval)
                continue

            if region.state == State.ACTIVE:
                print(region.recognize_cards())

            region = next(game.regions)
            screenshot = ImageGrab.grab()
