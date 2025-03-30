"""
主界面组件模块，负责创建主窗口、左侧玩家窗口和右侧玩家窗口，并实时更新记牌器的内容。
"""

import tkinter as tk

from loguru import logger

from core.backend_thread import BackendThread
from functions.windows_offset import calculate_offset
from misc.custom_types import ConfigDict, WindowsType
from models.config import GUI

from .counter_window import CounterWindow


class MasterWindow(tk.Tk):
    """顶级窗口；显示开始/关闭和退出按钮，并控制后端"""

    def __init__(self) -> None:
        super().__init__()

        # 初始化对象
        self.windows: list[CounterWindow] = []
        self.backend = BackendThread()

        # 初始化窗口
        config = GUI.get("SWITCH", {})
        self._setup_window_style()
        self._setup_switch(config)
        self._setup_exit(config)
        self._setup_window_position(config)

        logger.success("顶级窗口初始化完毕")

    def _setup_window_style(self) -> None:
        """设置窗口样式"""
        self.title("记牌器开关")
        self.attributes("-topmost", True)  # 置顶  # type: ignore
        self.overrideredirect(True)  # 去掉窗口边框
        self.configure(bg="white")  # 窗口背景设为白色
        self.attributes(  # type: ignore
            "-transparentcolor", "white"
        )  # 使白色背景变得透明

    def _setup_switch(self, config: ConfigDict) -> None:
        """创建开关按钮"""
        self.switch = tk.Button(
            self,
            text="打开记牌器",
            command=self._switch_on,
            width=10,
            font=("TkDefaultFont", config.get("FONT_SIZE", 12)),  # type: ignore
        )
        self.switch.pack(padx=0, pady=0)

    def _setup_exit(self, config: ConfigDict) -> None:
        """创建退出按钮"""
        self.exit = tk.Button(
            self,
            text="退出程序",
            command=self.destroy,
            width=10,
            font=("TkDefaultFont", config.get("FONT_SIZE", 12)),  # type: ignore
        )
        self.exit.pack(padx=0, pady=0)

    def _setup_window_position(self, config: ConfigDict) -> None:
        """设置窗口偏移量"""
        self.update_idletasks()  # 刷新窗口大小

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        x_offset, y_offset = calculate_offset(
            window_width,
            window_height,
            config.get("OFFSET_X", None),
            config.get("OFFSET_Y", None),
            config.get("CENTER_X", None),
            config.get("CENTER_Y", None),
        )

        self.geometry(f"+{x_offset}+{y_offset}")  # 应用偏移量
        logger.info(f"开关窗口偏移量为：{x_offset}，{y_offset}")
        logger.info(f"开关窗口大小为：{window_width}x{window_height}")

    def _switch_on(self) -> None:
        """打开记牌器"""
        logger.info("用户尝试打开记牌器")
        self.switch.config(state="disabled")  # 禁用开关按钮以避免重复点击

        # 创建主窗口
        if GUI["MAIN"].get("DISPLAY", True):
            self.main_window = CounterWindow(WindowsType.MAIN, self)
            self.windows.append(self.main_window)

        # 创建左侧玩家窗口
        if GUI["LEFT"].get("DISPLAY", True):
            self.left_window = CounterWindow(WindowsType.LEFT, self)
            self.windows.append(self.left_window)

        # 创建右侧玩家窗口
        if GUI["RIGHT"].get("DISPLAY", True):
            self.right_window = CounterWindow(WindowsType.RIGHT, self)
            self.windows.append(self.right_window)

        logger.success("所有记牌器窗口创建完毕")

        self.backend.start()  # 运行后端循环代码
        self.switch.config(
            text="关闭记牌器", command=self._switch_off
        )  # 更新开关按钮状态

        # 等待100毫秒后再启用开关按钮，避免后端线程过早关闭
        self.after(100, lambda: self.switch.config(state="normal"))
        logger.success("记牌器成功打开")

    def _switch_off(self) -> None:
        """关闭记牌器"""
        logger.info("用户尝试关闭记牌器")
        self.switch.config(state="disabled")  # 禁用开关按钮以避免重复点击

        self.backend.terminate()  # 关闭后端线程

        for window in self.windows:  # 关闭所有子窗口
            window.destroy()

        self.switch.config(
            text="打开记牌器", command=self._switch_on
        )  # 重置开关按钮状态

        logger.success("记牌器成功关闭")
        self._enable_switch()

    def _enable_switch(self) -> None:
        """在旧的线程（如果存在）终止后启用开关按钮"""
        if self.backend.is_old_running:
            self.after(200, self._enable_switch)  # 等待200毫秒后再次检查
        else:
            self.switch.config(state="normal")  # 启用开关按钮

    def delayed_destroy(self) -> None:
        """延迟销毁窗口，允许后端线程出错时让主窗口自己关闭自身（而不是由后端线程），避免卡死"""
        self.after(1000, self.destroy)
