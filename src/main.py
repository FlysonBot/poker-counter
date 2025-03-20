import tkinter as tk
from threading import Thread

from config import GUI_UPDATE_INTERVAL
from game_logic.backend_logic import backend_logic
from game_logic.card_counter import CardCounter
from logger import logger
from main_window import MainWindow

UPDATE_INTERVAL = int(GUI_UPDATE_INTERVAL * 1000)  # 转换为毫秒

if __name__ == "__main__":
    logger.info("应用程序已启动")

    # 创建应用
    root = tk.Tk()

    # 初始化记牌器
    counter = CardCounter()

    # 第二线程运行后端循环代码
    thread = Thread(target=backend_logic, args=(counter,), daemon=True)
    thread.start()
    logger.info("后端代码成功在第二线程运行")

    # 创建窗口
    window = MainWindow(root, counter)

    # 更新窗口内容
    def update_window():
        window.update_display()
        root.after(UPDATE_INTERVAL, update_window)  # 定时更新界面

    # 保持程序运行
    root.mainloop()
