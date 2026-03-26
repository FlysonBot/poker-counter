"""
配置加载模块。从 config.yaml 读取所有配置并导出为模块级常量。
其他模块直接 import 这里的常量使用，不需要自己读取 yaml 文件。
"""

import sys
from pathlib import Path

from ruamel.yaml import YAML


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
    ryaml = YAML()
    with open(path, encoding="utf-8") as f:
        return dict(ryaml.load(f))


_cfg = _load()

raw_config: dict = _cfg  # 原始配置字典，供需要读取任意 key 的模块使用
REGIONS: dict = _cfg["REGIONS"]  # 各检测区域的比例坐标（0.0–1.0）
THRESHOLDS: dict = _cfg["THRESHOLDS"]  # 各项检测的置信度/占比阈值
SCREENSHOT_INTERVAL: float = _cfg["SCREENSHOT_INTERVAL"]  # 主循环截图间隔（秒）
GAME_START_INTERVAL: float = _cfg["GAME_START_INTERVAL"]  # 等待游戏开始的轮询间隔（秒）
GAME_WINDOW_TITLE: str = _cfg["GAME_WINDOW_TITLE"]  # 用于定位游戏窗口的标题关键字
GUI: dict = _cfg["GUI"]  # 悬浮窗外观配置（颜色、字体、透明度等）
HOTKEYS: dict = _cfg["HOTKEYS"]  # 全局快捷键绑定
LOG_LEVEL: str = _cfg["LOG_LEVEL"]  # 日志输出级别（如 DEBUG、INFO）
LOG_RETENTION: int = _cfg["LOG_RETENTION"]  # 日志文件保留天数

# 模板图片目录（始终相对于源码位置，不受打包影响）
TEMPLATES_DIR: Path = Path(__file__).parent / "templates"
