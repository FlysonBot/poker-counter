import enum

import cv2

from card_matcher import CardMatcher, match_single_template
from color_percentage import calculate_color_percentage


class State(enum.Enum):
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
        self.width = bottom_right[0] - top_left[0]
        self.height = bottom_right[1] - top_left[1]
        self.state = State.WAIT

    def capture_region(self, image):
        """
        从图像中截取区域
        :param image: 输入图像（NumPy 数组）
        :return: 截取的区域图像
        """
        x1, y1 = self.top_left
        x2, y2 = self.bottom_right
        return image[y1:y2, x1:x2]

    def update_region_state(self, region_image):
        """
        更新区域状态
        :param region_image: 区域图像
        """
        # 首先判断区域是否是PASS状态
        if (
            match_single_template(region_image, cv2.imread("templates/PASS.png", 0))[0]
            > 0.9
        ):
            self.state = State.PASS
            return

        # 判断区域是否是WAIT状态
        if calculate_color_percentage(region_image, (118, 40, 75)) > 0.9:
            self.state = State.WAIT
            return

        self.state = State.ACTIVE

    def recognize_cards(self, region_image):
        """
        识别区域内的牌
        :param region_image: 区域图像
        :return: 识别结果（字典，键为牌面名称，值为数量）
        """
        # 调用 CardMatcher 识别牌
        return CardMatcher(region_image).detect_all_cards()


# 示例
if __name__ == "__main__":
    # 初始化区域模块
    region_manager = Region((260, 346), (700, 495))

    # 加载测试图像
    test_image = cv2.imread("test.png", 0)  # 灰度模式

    # 截取区域
    region_image = region_manager.capture_region(test_image)

    # 判断区域状态
    region_manager.update_region_state(region_image)
    print(region_manager.state)
