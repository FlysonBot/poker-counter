"""
增强型日志记录模块，提供日志记录功能，支持文件和控制台输出。
"""

import logging
import sys
import traceback
from typing import Any

from config import LOG_LEVEL, LOG_PATH


class Logger:
    """
    日志记录器类，负责初始化日志记录器并设置日志输出格式。
    """

    def __init__(self) -> None:
        """
        初始化日志记录器，设置日志级别、文件和控制台处理器。
        """
        self.logger: logging.Logger = logging.getLogger("poker_counter")
        self.logger.setLevel(LOG_LEVEL)

        # 文件处理器
        file_handler = logging.FileHandler(LOG_PATH, mode="w")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # 设置异常处理器
        sys.excepthook = self.handle_exception

    def handle_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: traceback.TracebackException | None,
    ) -> None:
        """
        处理未捕获的异常，记录异常信息。

        :param exc_type: 异常类型
        :param exc_value: 异常值
        :param exc_traceback: 异常回溯信息
        """
        if issubclass(exc_type, KeyboardInterrupt):
            self.logger.info("用户手动结束了进程")
            sys.exit(0)
        self.logger.error("未处理的异常", exc_info=(exc_type, exc_value, exc_traceback))  # type: ignore

    def __getattr__(self, name: str) -> Any:
        """
        动态获取日志记录器的属性。

        :param name: 属性名称
        :return: 日志记录器的属性值
        """
        return getattr(self.logger, name)


logger = Logger().logger
logger.info("日志文件初始化完成")
