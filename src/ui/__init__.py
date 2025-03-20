"""
界面模块的初始化文件，导出主窗口、错误窗口和异常处理函数。
"""

from .error_window import backend_error_handler
from .main_window import MainWindow

__all__ = [
    "MainWindow",
    "backend_error_handler",
]
