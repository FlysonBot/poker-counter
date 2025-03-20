"""
主程序入口模块，负责启动应用程序、运行后端代码，并初始化记牌器界面。
"""

import tkinter as tk
from threading import Thread

from config import GUI_UPDATE_INTERVAL
from game_logic.backend_logic import backend_logic
from game_logic.card_counter import CardCounter
from logger import logger
from ui import MainWindow, backend_error_handler

UPDATE_INTERVAL = int(GUI_UPDATE_INTERVAL * 1000)  # 转换为毫秒


if __name__ == "__main__":
    logger.success("应用程序已启动")

    # 创建应用
    root = tk.Tk()

    # 绑定后端错误处理函数
    logger.add(lambda message: backend_error_handler(root, message), level="ERROR")

    # 初始化记牌器
    counter = CardCounter()

    # 第二线程运行后端循环代码
    thread = Thread(target=backend_logic, args=(counter,), daemon=True)
    thread.start()
    logger.success("后端代码成功在第二线程运行")

    # 创建窗口
    window = MainWindow(root, counter)

    # 更新窗口内容
    def update_window() -> None:
        """
        定时更新记牌器界面显示内容。
        """
        window.update_display()
        root.after(UPDATE_INTERVAL, update_window)  # 定时更新界面

    # 保持程序运行
    root.mainloop()
