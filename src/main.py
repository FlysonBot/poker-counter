"""
主程序入口模块，负责启动应用程序、运行后端代码，并初始化记牌器界面。
"""

from misc.logger import logger
from ui.master_window import MasterWindow


if __name__ == "__main__":
    logger.success("应用程序已启动")

    # 创建主窗口及子窗口
    window = MasterWindow()

    # 保持程序运行
    window.mainloop()
