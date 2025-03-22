"""
主程序入口模块，负责启动应用程序、运行后端代码，并初始化记牌器界面。
"""

from config import GUI_UPDATE_INTERVAL
from game_logic import CardCounter, GameState
from logger import logger
from ui.master_window import MasterWindow

UPDATE_INTERVAL = int(GUI_UPDATE_INTERVAL * 1000)  # 转换为毫秒


if __name__ == "__main__":
    logger.success("应用程序已启动")

    # 初始化记牌器和游戏状态
    counter = CardCounter()
    gs = GameState()

    # 创建主窗口及子窗口
    window = MasterWindow(counter, gs)

    # 保持程序运行
    window.mainloop()
