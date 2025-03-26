"""
应用程序配置模块，读取包含游戏区域坐标、模板匹配阈值，和日志路径在内等配置。
"""

import sys
from pathlib import Path

import yaml


def load_config(file_path: Path):
    """
    从 YAML 文件中加载配置。

    :param file_path: 配置文件路径
    :return: 配置字典
    """

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def current_dir() -> Path:
    """
    根据运行状态获取当前目录或编译目录。

    :return: 当前目录或编译目录
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


# 从 YAML 文件中加载配置
config = load_config(current_dir() / "config.yaml")

# 提取配置项
REGIONS = config["REGIONS"]
THRESHOLDS = config["THRESHOLDS"]
SCREENSHOT_INTERVAL = config["SCREENSHOT_INTERVAL"]
GUI_UPDATE_INTERVAL = config["GUI_UPDATE_INTERVAL"]
GAME_START_INTERVAL = config["GAME_START_INTERVAL"]
GUI = config["GUI"]
LOG_LEVEL = config["LOG_LEVEL"]
LOG_RETENTION = config["LOG_RETENTION"]
