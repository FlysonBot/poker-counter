from pathlib import Path

import numpy as np
from cv2 import imread

from exceptions import TemplateLoadingError
from logger import logger

TEMPLATE_DIR = Path("templates")


def load_template(template: str) -> np.ndarray:
    """加载单个模板"""
    logger.debug(f"尝试加载模板: {template}")
    template_path = TEMPLATE_DIR / f"{template}.png"

    if not template_path.exists():
        logger.error(f"模板缺失: {template_path}")
        raise TemplateLoadingError(str(template_path))

    img = imread(str(template_path), 0)
    if img is None:
        logger.error(f"模板图片无效或无法访问: {template_path}")
        raise TemplateLoadingError(str(template_path))

    logger.debug(f"模板加载成功：{template_path}")
    return img


def load_templates(template_names: set[str]) -> dict[str, np.ndarray]:
    """预加载所有模板"""
    templates = {}

    for template_name in template_names:
        templates[template_name] = load_template(template_name)

    return templates


CARD_TEMPLATE_NAMES = {
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
    "A",
    "2",
    "王",
}
MARK_TEMPLATE_NAMES = {"PASS", "Landlord"}


CARDS = load_templates(CARD_TEMPLATE_NAMES)
MARKS = load_templates(MARK_TEMPLATE_NAMES)
