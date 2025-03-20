"""
增强型日志记录模块
"""

import logging
import sys
from typing import Any

from config import LOG_LEVEL, LOG_PATH


class Logger:
    def __init__(self) -> None:
        self.logger: logging.Logger = logging.getLogger("poker_counter")
        self.logger.setLevel(LOG_LEVEL)

        # 文件handler
        file_handler = logging.FileHandler(LOG_PATH, mode="w")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # 设置异常handler
        sys.excepthook = self.handle_exception  # type: ignore

    def handle_exception(self, exc_type, exc_value, exc_traceback) -> None:  # type: ignore
        if issubclass(exc_type, KeyboardInterrupt):
            self.logger.info("用户手动结束了进程")
            sys.exit(0)
        self.logger.error("未处理的异常", exc_info=(exc_type, exc_value, exc_traceback))  # type: ignore

    def __getattr__(self, name: str) -> Any:
        return getattr(self.logger, name)


logger = Logger().logger
logger.info("日志文件初始化完成")
