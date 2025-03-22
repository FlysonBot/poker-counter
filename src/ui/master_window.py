"""
主界面组件模块，负责创建主窗口、左侧玩家窗口和右侧玩家窗口，并实时更新记牌器的内容。
"""

import tkinter as tk
from typing import Callable

from game_logic import CardCounter, GameState
from logger import logger

from config import GUI

from .counter_window import CounterWindow
from .windows_type import WindowsType


class MasterWindow(tk.Tk):
    """
    主界面组件类，显示记牌器的实时信息。
    """

    def __init__(self, counter: CardCounter, gs: GameState) -> None:
        """
        初始化主界面组件。

        :param counter: 记牌器对象
        :param gs: 游戏状态对象
        """
        super().__init__()

        # 设置主窗口为不可见（因为我们使用CounterWindow作为实际显示）
        self.withdraw()

        # 初始化更新函数列表
        self.update_funcs: list[Callable[[], None]] = []

        # 创建主窗口
        if GUI["MAIN"].get("DISPLAY", True):
            self.main_window = CounterWindow(counter, gs, WindowsType.MAIN, self)
            self.update_funcs.append(self.main_window.update_display)

        # 创建左侧玩家窗口
        if GUI["LEFT"].get("DISPLAY", True):
            self.left_window = CounterWindow(counter, gs, WindowsType.LEFT, self)
            self.update_funcs.append(self.left_window.update_display)

        # 创建右侧玩家窗口
        if GUI["RIGHT"].get("DISPLAY", True):
            self.right_window = CounterWindow(counter, gs, WindowsType.RIGHT, self)
            self.update_funcs.append(self.right_window.update_display)

        logger.success("所有窗口初始化完毕")

    def update_display(self) -> None:
        """
        更新所有窗口的显示内容。
        """
        
        for update_func in self.update_funcs:
            update_func()
