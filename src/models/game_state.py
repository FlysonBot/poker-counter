"""
游戏状态模块，负责监控游戏状态并识别牌局中的牌。
"""

from dataclasses import dataclass

from loguru import logger

from functions.match_template import MARK_TEMPLATES, best_template_match
from misc.custom_types import CardIntDict
from misc.singleton import singleton
from models.config import REGIONS, THRESHOLDS
from models.enum import Mark, Player, RegionState

from .regions import Region

card_regions: dict[Player, Region] = {
    Player.LEFT: Region(*REGIONS["playing_left"]),
    Player.MIDDLE: Region(*REGIONS["playing_middle"]),
    Player.RIGHT: Region(*REGIONS["playing_right"]),
}

landlord_marker: dict[Player, Region] = {
    Player.LEFT: Region(*REGIONS["remaining_cards_left"]),
    Player.MIDDLE: Region(*REGIONS["remaining_cards_middle"]),
    Player.RIGHT: Region(*REGIONS["remaining_cards_right"]),
}

game_end_marker: Region = Region(*REGIONS["three_displayed_cards"])
my_cards_region: Region = Region(*REGIONS["my_cards"])
my_cards_region.state = RegionState.ACTIVE


@singleton
@dataclass
class GameState:
    """游戏状态类，负责监控游戏状态并识别牌局中的牌"""

    @property
    def my_cards(self) -> CardIntDict:
        """识别并返回自己的牌"""
        return my_cards_region.recognize_cards()

    @property
    def _match_landlord_mark(self) -> list[float]:
        """返回三个区域的地主标记匹配置信度"""
        regions = landlord_marker.values()
        region_screenshots = map(lambda region: region.region_screenshot, regions)
        results = map(
            lambda screenshot: best_template_match(
                screenshot, MARK_TEMPLATES[Mark.LANDLORD]
            ),
            region_screenshots,
        )
        return [result[0] for result in results]

    @property
    def is_game_started(self) -> bool:
        """根据地主标记匹配置信度判断游戏是否开始"""
        confidence = max(self._match_landlord_mark)
        if confidence < THRESHOLDS["landlord"]:
            logger.debug(
                f"游戏未开始。地主标记匹配置信度为：{confidence}，低于阈值：{THRESHOLDS['landlord']}"
            )
            return False
        return True

    @property
    def landlord_location(self) -> Player:
        """根据地主标记匹配置信度判断地主是谁"""
        confidences = self._match_landlord_mark
        max_index = confidences.index(max(confidences))
        if max_index == 0:
            return Player.LEFT
        if max_index == 1:
            return Player.MIDDLE
        return Player.RIGHT

    @property
    def is_game_ended(self) -> bool:
        """根据底牌区域的牌判断游戏是否结束"""
        game_end_marker.update_state()

        if game_end_marker.state is not RegionState.ACTIVE:
            logger.debug("游戏未结束。底牌区域状态为：{game_end_marker.state}")
            return False

        cards = game_end_marker.recognize_cards()
        if len(cards) < 0:
            logger.debug("游戏未结束。底牌区域未识别到牌")
            return False

        logger.debug(f"游戏结束。底牌区域的牌为：{cards}")
        return True
