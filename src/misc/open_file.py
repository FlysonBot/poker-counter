"""
文件打开模块，定义打开文件的函数。
"""

import os
from tempfile import gettempdir
from tkinter import messagebox

from loguru import logger


def open_file(filepath: str, what_file: str) -> None:
    """
    打开文件。

    :param filepath: 文件路径
    :param what_file: 文件类型（用于错误提示）
    """
    try:
        os.startfile(filepath)

    # 文件打开失败
    except Exception:
        logger.error(f"打开{what_file}失败。")
        messagebox.showerror(  # type: ignore
            "错误",
            f"打开{what_file}失败，请手动查看文件。文件路径：{filepath}",
        )


def open_latest_log() -> None:
    """
    打开最新的日志文件。
    """
    # 查找最新的日志文件
    log_dir = gettempdir()

    try:
        logfiles = [
            filename
            for filename in os.listdir(log_dir)
            if filename.startswith("poker-counter_") and filename.endswith(".log")
        ]
        latest_logfile = sorted(logfiles)[-1]
        log_path = os.path.join(log_dir, latest_logfile)

    except Exception:
        logger.error("最新日志文件查找失败。")
        messagebox.showerror(  # type: ignore
            "错误",
            "最新日志文件查找失败，请手动查看日志文件。日志目录：{log_dir}",
        )
        return

    # 打开最新的日志文件
    open_file(log_path, "日志文件")


def open_config() -> None:
    """
    打开配置文件。
    """

    open_file(os.path.join(os.path.dirname(__file__), "../config.yaml"), "配置文件")
