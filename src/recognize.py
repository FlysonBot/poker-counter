"""
卡牌识别模块。负责加载模板并在截图区域内识别牌和标记。
"""

from pathlib import Path

import cv2
import numpy as np
from loguru import logger

from config import TEMPLATES_DIR, THRESHOLDS
from card_types import Card, Mark

# 类型别名
Image = np.ndarray  # 灰度图，shape (H, W), dtype uint8
Region = tuple[int, int, int, int]  # (x1, y1, x2, y2) 像素坐标


# ---------------------------------------------------------------------------
# 模板加载（程序启动时执行一次）
# ---------------------------------------------------------------------------


def _load_templates(enum_cls) -> dict:
    templates = {}
    for member in enum_cls:
        path: Path = TEMPLATES_DIR / f"{member.value}.png"
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.error(f"模板加载失败: {path}")
        else:
            templates[member] = img
            logger.trace(f"已加载模板: {path.stem}")
    logger.success(f"已加载模板: {[m.value for m in enum_cls]}")
    return templates


# 模块导入时加载一次，后续所有识别调用共用同一份模板数据
CARD_TEMPLATES: dict[Card, Image] = _load_templates(Card)
MARK_TEMPLATES: dict[Mark, Image] = _load_templates(Mark)


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _crop(image: Image, region: Region) -> Image:
    x1, y1, x2, y2 = region
    return image[y1:y2, x1:x2]


def _scale_template(template: Image, scale: float) -> Image:
    """按比例缩放模板；scale=1.0 时原样返回。
    缩小用 INTER_AREA（抗锯齿效果最好），放大用 INTER_LINEAR。
    """
    if abs(scale - 1.0) < 0.01:
        return template
    h, w = template.shape[:2]
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    return cv2.resize(template, (new_w, new_h), interpolation=interp)


def _nms_matches(
    matches: list[tuple[float, tuple[int, int]]], min_dist: int
) -> list[tuple[float, tuple[int, int]]]:
    """非极大值抑制（NMS）：对距离小于 min_dist 的匹配点，只保留置信度最高的那个。
    模板匹配的结果是一张热力图，同一张牌周围相邻几个像素都会有高置信度，
    不做 NMS 的话一张牌会被计数多次。
    """
    if not matches:
        return []
    # 按置信度从高到低排序，优先保留最可信的匹配
    matches = sorted(matches, key=lambda x: x[0], reverse=True)
    kept = []
    for conf, (x, y) in matches:
        # 如果与已保留的某个匹配点距离太近，认为是同一张牌，丢弃
        too_close = any(
            abs(x - kx) < min_dist and abs(y - ky) < min_dist for _, (kx, ky) in kept
        )
        if not too_close:
            kept.append((conf, (x, y)))
    return kept


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------


def identify_cards(image: Image, region: Region, scale: float = 1.0) -> dict[Card, int]:
    """在截图的指定区域内识别所有卡牌，返回 {Card: 数量} 字典。
    scale 为模板缩放比例（窗口实际高度 / 参考高度），用于适配不同分辨率。
    """
    crop = _crop(image, region)
    threshold = THRESHOLDS["card"]
    results: dict[Card, int] = {}

    for card, template in CARD_TEMPLATES.items():
        t = _scale_template(template, scale)
        if t.shape[0] > crop.shape[0] or t.shape[1] > crop.shape[1]:
            continue  # 模板比截图区域还大，无法匹配，跳过

        # matchTemplate 返回一张与截图等大的热力图，每个像素值是该位置的匹配置信度
        res = cv2.matchTemplate(crop, t, cv2.TM_CCOEFF_NORMED)
        locs = np.where(res >= threshold)
        raw_matches = [(res[y, x], (x, y)) for x, y in zip(*locs[::-1])]

        # NMS 的最小距离设为模板宽度的一半，确保同一张牌只被计数一次
        min_dist = max(t.shape[1] // 2, 5)
        kept = _nms_matches(raw_matches, min_dist)

        if kept:
            results[card] = len(kept)
            logger.debug(
                f"识别到 {len(kept)} 张 {card.value}（置信度最高: {kept[0][0]:.3f}）"
            )

    return results


def match_mark(image: Image, region: Region, mark: Mark, scale: float = 1.0) -> float:
    """在指定区域内匹配特定标记（地主皇冠、PASS 文字等），返回最高置信度。
    与 identify_cards 不同，标记只需要判断"有没有"，不需要计数，所以直接返回最高分。
    """
    crop = _crop(image, region)
    template = MARK_TEMPLATES.get(mark)
    if template is None:
        return 0.0

    t = _scale_template(template, scale)
    if t.shape[0] > crop.shape[0] or t.shape[1] > crop.shape[1]:
        return 0.0

    res = cv2.matchTemplate(crop, t, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    logger.debug(f"{mark.value} 置信度: {max_val:.3f}")
    return float(max_val)
