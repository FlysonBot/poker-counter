from region.region import Region

class CardRegion(Region):
    def update_state(self) -> None:
        """
        更新区域状态
        """

        # 先检查是否为PASS状态
        match_val, _ = cv2.matchTemplate(self.region_screenshot, MARKS["PASS"])
        if match_val > THRESHOLDS["pass"]:
            self.state = RegionState.PASS
            logger.debug("更新区域状态为: PASS")
            return

        # 检查是否为WAIT状态
        wait_color_percentage = self._calculate_color_percentage(self.region_screenshot, COLORS["wait"])
        if wait_color_percentage > THRESHOLDS["wait"]:
            self.state = RegionState.WAIT
            logger.debug("更新区域状态为: WAIT")
            return

        # 否则的话状态为ACTIVE
        self.state = RegionState.ACTIVE
        logger.debug("更新区域状态为: ACTIVE")

    def recognize_cards(self) -> Dict[str, int]:
        """
        识别区域内的牌
        """
        if self.state != RegionState.ACTIVE:
            logger.warning("尝试在非活跃区域（出了牌的区域）进行识牌")
            return {}

        region_image = self.capture(self.region_screenshot)
        return identify_cards(region_image, THRESHOLDS["card"])

