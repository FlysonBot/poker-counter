"""
模板加载模块，负责加载和管理牌型和标记模板。
"""

from pathlib import Path

from cv2 import imread

from exceptions import TemplateLoadingError
from logger import logger

from .image_types import GrayscaleImage

TEMPLATE_DIR = Path("templates")


def load_template(template: str) -> GrayscaleImage:
    """
    加载单个模板。

    :param template: 模板名称
    :return: 模板图像
    """

    logger.trace(f"尝试加载模板: {template}")
    template_path: Path = TEMPLATE_DIR / f"{template}.png"

    if not template_path.exists():
        logger.error(f"模板缺失: {template_path}")
        raise TemplateLoadingError(str(template_path))

    img: GrayscaleImage = imread(str(template_path), 0)  # type: ignore
    if img is None:
        logger.error(f"模板图片无效或无法访问: {template_path}")
        raise TemplateLoadingError(str(template_path))

    logger.debug(f"模板加载成功：{template_path}")
    return img


def load_templates(template_names: set[str]) -> dict[str, GrayscaleImage]:
    """
    加载多个模板。

    :param template_names: 模板名称集合
    :return: 模板字典
    """
    templates: dict[str, GrayscaleImage] = {}

    for template_name in template_names:
        templates[template_name] = load_template(template_name)

    logger.success(f"成功加载以下模板：{template_names}")
    return templates


MARK_TEMPLATE_NAMES: set[str] = {"PASS", "Landlord"}
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


MARKS: dict[str, GrayscaleImage] = load_templates(MARK_TEMPLATE_NAMES)
CARDS: dict[str, GrayscaleImage] = load_templates(CARD_TEMPLATE_NAMES)
