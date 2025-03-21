"""
增强型日志记录模块，提供日志记录功能，支持文件和控制台输出。
"""

import sys
import traceback
from pathlib import Path
from tempfile import gettempdir

from loguru import logger

from config import LOG_LEVEL

logger.remove(0)  # 移除默认日志记录器
logger.add(sys.stderr, level=LOG_LEVEL)  # 控制台输出
logger.add(
    Path(gettempdir()) / "poker-counter_{time:YYYY-MM-DD_HH-mm-ss}.log",
    level=LOG_LEVEL,
    retention=3,
)  # 文件输出（每次运行都会创建一个新的日志，最多保留3个日志）


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

    # Format the traceback into a string
    formatted_traceback = "".join(  # type: ignore
        traceback.format_exception(exc_type, exc_value, exc_traceback)  # type: ignore
    )

    # Log the critical error with the formatted traceback
    logger.critical("未处理的异常:\n" + formatted_traceback)


sys.excepthook = handle_exception  # 替换默认的异常处理函数
