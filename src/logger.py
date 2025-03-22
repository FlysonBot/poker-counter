"""
增强型日志记录模块，提供日志记录功能，支持文件和控制台输出。
"""

import sys
import traceback
from pathlib import Path
from tempfile import gettempdir
from tkinter import messagebox
from typing import NoReturn

from loguru import logger

from config import LOG_LEVEL
from misc.open_file import open_latest_log


def handle_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: traceback.TracebackException | None,
) -> None:
    """
    自定义的异常处理函数，替换默认的异常处理函数，以将异常信息记录到日志文件中。

    :param exc_type: 异常类型
    :param exc_value: 异常值
    :param exc_traceback: 异常回溯信息
    """
    if issubclass(exc_type, KeyboardInterrupt):
        logger.info("用户手动结束了进程")
        sys.exit(0)  # 退出进程

    # 格式化错误为字符串
    formatted_traceback: str = "".join(  # type: ignore
        traceback.format_exception(exc_type, exc_value, exc_traceback)  # type: ignore
    )

    # 记录格式化后的错误
    logger.critical("未处理的异常:\n" + formatted_traceback)  # type: ignore


def backend_error_handler(message: str) -> NoReturn:
    """
    后端错误处理函数，在后端出现错误时调用以弹出错误提示并退出程序。

    :param window: 应用窗口
    :param message: 错误信息
    """

    # 提示错误
    messagebox.showerror("错误", message)  # type: ignore

    # 询问用户是否打开日志文件
    if messagebox.askyesno("日志文件", "是否打开日志文件？"):  # type: ignore
        open_latest_log()

    # 退出程序
    exit(1)


logger.remove(0)  # 移除默认日志记录器
logger.add(sys.stderr, level=LOG_LEVEL)  # 控制台输出
logger.add(
    Path(gettempdir()) / "poker-counter_{time:YYYY-MM-DD_HH-mm-ss}.log",
    level=LOG_LEVEL,
    retention=3,
)  # 文件输出（每次运行都会创建一个新的日志，最多保留3个日志）
logger.add(backend_error_handler, level="ERROR")

sys.excepthook = handle_exception  # 替换默认的异常处理函数
