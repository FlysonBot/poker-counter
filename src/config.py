"""
配置加载模块。从 config.yaml 读取所有配置并导出为模块级常量。
"""

import sys
from pathlib import Path

import yaml


def _config_dir() -> Path:
    """返回配置文件所在目录。
    打包后（PyInstaller frozen）配置文件与 exe 同级；
    开发时配置文件与本模块同级（src/ 目录下）。
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _load() -> dict:
    path = _config_dir() / "config.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


_cfg = _load()

# 原始配置字典，供需要读取任意 key 的模块使用（如 overlay_manager 读取 IS_FIRST_LAUNCH）
raw_config: dict = _cfg

# 区域坐标参考分辨率，用于计算模板缩放比例
TEMPLATE_SCALE: float = _cfg.get("TEMPLATE_SCALE", 1.0)
# 各检测区域的比例坐标（0.0–1.0）
REGIONS: dict = _cfg["REGIONS"]
# 各项检测的置信度/占比阈值
THRESHOLDS: dict = _cfg["THRESHOLDS"]
SCREENSHOT_INTERVAL: float = _cfg["SCREENSHOT_INTERVAL"]
GAME_START_INTERVAL: float = _cfg["GAME_START_INTERVAL"]
# 用于 pygetwindow 定位游戏窗口的标题关键字
GAME_WINDOW_TITLE: str = _cfg["GAME_WINDOW_TITLE"]
GUI: dict = _cfg["GUI"]
HOTKEYS: dict = _cfg["HOTKEYS"]
LOG_LEVEL: str = _cfg["LOG_LEVEL"]
LOG_RETENTION: int = _cfg["LOG_RETENTION"]

# 模板图片目录（始终相对于源码位置，不受打包影响——PyInstaller 会把 templates/ 解包到此处）
TEMPLATES_DIR: Path = Path(__file__).parent / "templates"
