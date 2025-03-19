import cv2

from functions.image_match import match_template_by_threshold
from config import THRESHOLD

THRESHOLD = THRESHOLD["card"]

class CardsIdentifier:
    TEMPLATES = {
        "A": cv2.imread("templates/A.png", 0),
        "2": cv2.imread("templates/2.png", 0),
        "3": cv2.imread("templates/3.png", 0),
        "4": cv2.imread("templates/4.png", 0),
        "5": cv2.imread("templates/5.png", 0),
        "6": cv2.imread("templates/6.png", 0),
        "7": cv2.imread("templates/7.png", 0),
        "8": cv2.imread("templates/8.png", 0),
        "9": cv2.imread("templates/9.png", 0),
        "10": cv2.imread("templates/10.png", 0),
        "J": cv2.imread("templates/J.png", 0),
        "Q": cv2.imread("templates/Q.png", 0),
        "K": cv2.imread("templates/K.png", 0),
        "JOKER": cv2.imread("templates/JOKER.png", 0),
    }  # 加载所有模板图像

    def __init__(self, target_image) -> None:
        self.target_image = target_image  # 直接使用传入的图像

    def match_template_multiple(self, template_card):
        """匹配目标图像中的指定牌面"""
        template_image = CardsIdentifier.TEMPLATES[template_card]
        return match_template_by_threshold(
            self.target_image, template_image, THRESHOLD
        )

    def detect_all_cards(self):
        """自动识别目标图像中的所有牌面"""
        detected_cards = {}

        for card_name in CardsIdentifier.TEMPLATES:
            matches = self.match_template_multiple(card_name)
            if matches:
                detected_cards[card_name] = len(matches)  # 只记录匹配数量

        return detected_cards
