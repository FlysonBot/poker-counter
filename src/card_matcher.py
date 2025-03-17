import cv2


def match_single_template(target_image, template_image):
    """Match a single template in the target image and return location and value if found"""
    result = cv2.matchTemplate(target_image, template_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc


class CardMatcher:
    # 类常量：加载所有模板图像
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
    }
    THRESHOLD = 0.99  # 匹配相似度阈值

    def __init__(self, target_image):
        self.target_image = target_image  # 直接使用传入的图像

    def match_template_multiple(self, template_card):
        """匹配目标图像中的指定牌面"""
        template_image = CardMatcher.TEMPLATES[template_card]
        matches = []

        # 复制目标图像，避免修改原图
        target_copy = self.target_image.copy()

        while True:
            # 进行模板匹配
            max_val, max_loc = match_single_template(target_copy, template_image)

            # 如果匹配相似度低于阈值，停止匹配
            if max_val < CardMatcher.THRESHOLD:
                break

            # 记录匹配结果
            matches.append((max_loc, max_val))

            # 屏蔽已匹配的区域
            h, w = template_image.shape
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            cv2.rectangle(
                target_copy, top_left, bottom_right, 0, -1
            )  # 将匹配区域设置为 0

        return matches

    def detect_all_cards(self):
        """自动识别目标图像中的所有牌面"""
        detected_cards = {}

        for card_name in CardMatcher.TEMPLATES:
            matches = self.match_template_multiple(card_name)
            if matches:
                detected_cards[card_name] = len(matches)  # 只记录匹配数量

        return detected_cards
