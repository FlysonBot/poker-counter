"""
主界面组件模块，负责创建主窗口、左侧玩家窗口和右侧玩家窗口，并实时更新记牌器的内容。
"""

import tkinter as tk
from threading import Event, Thread

from config import GUI, GUI_UPDATE_INTERVAL
from game_logic import CardCounter, GameState, backend_logic
from logger import logger
from misc.windows_offset import calculate_offset

from .counter_window import CounterWindow
from .windows_type import WindowsType

UPDATE_INTERVAL = int(GUI_UPDATE_INTERVAL * 1000)  # 转换为毫秒


class MasterWindow(tk.Tk):
    """
    主界面组件类，显示记牌器的实时信息。
    """

    def __init__(self) -> None:
        """
        初始化主界面组件。

        :param counter: 记牌器对象
        :param gs: 游戏状态对象
        """
        super().__init__()

        # 初始化对象
        self.counter = CardCounter()
        self.gs = GameState()
        self.windows: list[CounterWindow] = []
        self.program_started = False

        # 初始化窗口
        self._setup_window()

        logger.success("顶级窗口初始化完毕")

    def _setup_window(self) -> None:
        """
        设置窗口属性，包括窗口大小、位置、背景等。
        """

        # 基本外观设置
        self.title("记牌器开关")
        self.attributes("-topmost", True)  # 置顶  # type: ignore
        self.overrideredirect(True)  # 去掉窗口边框
        self.configure(bg="white")  # 窗口背景设为白色
        self.attributes(  # type: ignore
            "-transparentcolor", "white"
        )  # 使白色背景变得透明

        # 创建开关按钮
        font_size: int = GUI.get("SWITCH", {}).get("FONT_SIZE", 16)
        self.switch = tk.Button(
            self,
            text="打开记牌器",
            command=self._turn_on_program,
            width=10,
            font=(None, font_size),  # type: ignore
        )
        self.switch.pack(padx=0, pady=0)

        # 创建退出按钮
        self.exit = tk.Button(
            self,
            text="退出程序",
            command=self.destroy,
            width=10,
            font=(None, font_size),  # type: ignore
        )
        self.exit.pack(padx=0, pady=0)

        # 动态调整窗口大小以匹配内容大小
        self.update_idletasks()  # 刷新窗口大小

        # 设置窗口偏移量
        location_config = GUI.get("SWITCH", {})
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        x_offset, y_offset = calculate_offset(
            window_width,
            window_height,
            location_config.get("OFFSET_X", None),
            location_config.get("OFFSET_Y", None),
            location_config.get("CENTER_X", None),
            location_config.get("CENTER_Y", None),
        )

        self.geometry(f"+{x_offset}+{y_offset}")  # 应用偏移量
        logger.info(f"开关窗口偏移量为：{x_offset}，{y_offset}")
        logger.info(f"开关窗口大小为：{window_width}x{window_height}")

    def _turn_on_program(self) -> None:
        """
        打开记牌器。
        """

        logger.info("用户尝试打开记牌器")

        # 创建主窗口
        if GUI["MAIN"].get("DISPLAY", True):
            self.main_window = CounterWindow(
                self.counter, self.gs, WindowsType.MAIN, self
            )
            self.windows.append(self.main_window)

        # 创建左侧玩家窗口
        if GUI["LEFT"].get("DISPLAY", True):
            self.left_window = CounterWindow(
                self.counter, self.gs, WindowsType.LEFT, self
            )
            self.windows.append(self.left_window)

        # 创建右侧玩家窗口
        if GUI["RIGHT"].get("DISPLAY", True):
            self.right_window = CounterWindow(
                self.counter, self.gs, WindowsType.RIGHT, self
            )
            self.windows.append(self.right_window)

        self.program_started = True
        logger.success("所有窗口创建完毕")

        # 第二线程运行后端循环代码
        self._backend_terminate_signal = Event()
        self._backend_thread = Thread(
            target=backend_logic,
            args=(self.counter, self.gs, self._backend_terminate_signal),
            daemon=True,
        )
        self._backend_thread.start()
        logger.success("后端代码成功在第二线程运行")

        # 更新开关按钮状态
        self.switch.config(text="关闭记牌器", command=self._turn_off_program)

        logger.success("记牌器成功打开")

    def _turn_off_program(self) -> None:
        """
        关闭记牌器。
        """

        logger.info("用户尝试关闭记牌器")

        # 关闭所有子窗口
        for window in self.windows:
            window.destroy()

        # 关闭后端线程
        self._backend_terminate_signal.set()
        self._backend_thread.join()

        # 重置开关按钮状态
        self.switch.config(text="打开记牌器", command=self._turn_on_program)

        self.program_started = False
        logger.success("记牌器成功关闭")
