"""
模板匹配模块，通过模板匹配来识别图片中的牌和标记。
"""

from pathlib import Path

import numpy as np
from cv2 import TM_CCOEFF_NORMED, matchTemplate, minMaxLoc
from loguru import logger
from PIL import Image

from misc.custom_types import (
    AnyEnum,
    AnyImage,
    Card,
    CardIntDict,
    EnumTemplateDict,
    Mark,
    MatchResult,
)

TEMPLATE_DIR: Path = Path(__file__).parent.parent / "templates"


def _load_template(template_path: Path) -> AnyImage:
    """加载模板图像。
    :param template_path: 模板图像路径
    :return: 模板图像
    """
    logger.trace(f"尝试加载模板: {template_path.stem}")
    image= np.array(Image.open(template_path).convert("L"))  # type: ignore

    if not template_path.exists():
        logger.error(f"模板缺失: {template_path}")
    if image is None:
        logger.error(f"模板图片无效或无法访问: {template_path}")
    return image  # type: ignore


def _load_enum_templates(enum: type[AnyEnum]) -> EnumTemplateDict[AnyEnum]:
    """加载模板枚举类型下的所有模板。
    :param enum: 枚举类型
    :return: 模板字典
    """
    templates: dict[AnyEnum, AnyImage] = {
        enum_member: _load_template(TEMPLATE_DIR / f"{enum_member.value}.png")
        for enum_member in enum
    }
    # sourcery skip: collection-builtin-to-comprehension
    logger.success(f"成功加载以下模板：{set(member.value for member in enum)}")

    return templates


CARD_TEMPLATES: EnumTemplateDict[Card] = _load_enum_templates(Card)
MARK_TEMPLATES: EnumTemplateDict[Mark] = _load_enum_templates(Mark)


def template_match(
    target: AnyImage, template: AnyImage, threshold: float
) -> list[MatchResult]:
    """根据指定阀值识别图片中指定的模板图片并返回匹配的结果。
    :param target: 目标图像
    :param template: 模板图像
    :param threshold: 匹配阈值
    :return: 匹配的结果列表（包含置信度和位置）
    """
    result = matchTemplate(target, template, TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)

    return [(result[pt[1], pt[0]], pt) for pt in zip(*locations[::-1])]  # type: ignore


def best_template_match(target: AnyImage, template: AnyImage) -> MatchResult:
    """返回最佳匹配结果的位置和置信度。
    :param target: 目标图像
    :param template: 模板图像
    :return: 最佳匹配结果的置信度和位置
    """
    result = matchTemplate(target, template, TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = minMaxLoc(result)

    return max_val, (max_loc[0], max_loc[1])


def identify_cards(image: AnyImage, threshold: float) -> CardIntDict:
    """识别图像中的所有扑克牌。
    :param image: 输入图像
    :param threshold: 匹配阈值
    :return: 识别出的牌及其数量
    """
    results: dict[Card, int] = {}

    for card, template in CARD_TEMPLATES.items():
        result = template_match(image, template, threshold)
        amount: int = len(result)

        if amount > 0:
            results[card] = amount
            logger.debug(f"检测到 {amount} 张 {card}")

    return results
