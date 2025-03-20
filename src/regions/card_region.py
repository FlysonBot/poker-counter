from config import THRESHOLDS
from image_processing import MARKS, color_percentage, identify_cards, template_match
from logger import logger
from .region import Region
from .region_state import RegionState


class CardRegion(Region):
    def update_state(self) -> None:
        """
        更新区域状态
        """

        # 先检查是否为PASS状态
        confidences, _ = template_match(
            self.region_screenshot, MARKS["PASS"], THRESHOLDS["pass"]
        )
        if confidences:
            self.state = RegionState.PASS
            logger.debug("更新区域状态为: PASS")
            return

        # 检查是否为WAIT状态
        wait_color_percentage: float = color_percentage(
            self.region_screenshot, (118, 40, 75)
        )
        if wait_color_percentage > THRESHOLDS["wait"]:
            self.state = RegionState.WAIT
            logger.debug("更新区域状态为: WAIT")
            return

        # 否则的话状态为ACTIVE
        self.state = RegionState.ACTIVE
        logger.debug("更新区域状态为: ACTIVE")

    def recognize_cards(self) -> dict[str, int]:
        """
        识别区域内的牌
        """
        if self.state != RegionState.ACTIVE:
            logger.warning("尝试在非活跃区域（出了牌的区域）进行识牌")
            return {}

        self.capture(self.region_screenshot)
        return identify_cards(self.region_screenshot, THRESHOLDS["card"])
