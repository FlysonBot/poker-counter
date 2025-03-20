from typing import Dict
from logger import logger

class CardCounter:
    """
    牌数统计器，跟踪剩余牌的数量
    """
    INITIAL_COUNTS = {
        "3": 4, "4": 4, "5": 4, "6": 4,
        "7": 4, "8": 4, "9": 4, "10": 4,
        "J": 4, "Q": 4, "K": 4, "A": 4,
        "2": 4, "王": 2
    }

    def __init__(self):
        self.reset()
        logger.info("记牌器初始化成功")

    def reset(self) -> None:
        """重置计数器"""
        self.counts = self.INITIAL_COUNTS.copy()
        logger.debug("记牌器状态已还原")

    def mark(self, card: str) -> None:
        """标记已出的牌"""

        if self.counts.get(card, 0) > 0:
            self.counts[card] -= 1
            logger.info(f"标记牌：{card} (剩余：{self.counts[card]})")
        
        else:
            logger.warning(f"尝试标记不存在的牌型或已出完的牌：{card}")

    def get_count(self, card: str) -> int:
        """获取指定牌的剩余数量"""
        return self.counts.get(card, 0)
