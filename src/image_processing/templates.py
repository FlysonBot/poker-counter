from pathlib import Path

from cv2 import imread

from exceptions import TemplateLoadingError
from logger import logger

from .image_types import GrayscaleImage

TEMPLATE_DIR = Path("templates")


def load_template(template: str) -> GrayscaleImage:
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
    return img  # type: ignore


def load_templates(template_names: set[str]) -> dict[str, GrayscaleImage]:
    """预加载所有模板"""
    templates: dict[str, GrayscaleImage] = {}

    for template_name in template_names:
        templates[template_name] = load_template(template_name)

    return templates


CARD_TEMPLATE_NAMES: set[str] = {
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
MARK_TEMPLATE_NAMES: set[str] = {"PASS", "Landlord"}


CARDS: dict[str, GrayscaleImage] = load_templates(CARD_TEMPLATE_NAMES)
MARKS: dict[str, GrayscaleImage] = load_templates(MARK_TEMPLATE_NAMES)
