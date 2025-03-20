import os
import tkinter as tk
from tkinter import messagebox
from typing import NoReturn
from tempfile import gettempdir

from logger import logger


def backend_error_handler(root: tk.Tk, message: str) -> NoReturn:
    """
    后端错误处理函数，在后端出现错误时调用以弹出错误提示并退出程序。

    :param window: 应用窗口
    :param message: 错误信息
    """

    # 关闭原先的应用窗口
    root.destroy()

    # 提示错误
    messagebox.showerror("错误", message)  # type: ignore

    # 询问用户是否打开日志文件
    if messagebox.askyesno("日志文件", "是否打开日志文件？"):  # type: ignore

        # 打开日志文件
        try:
            log_path = logger._core.handlers[1]._sink  # type: ignore
            os.startfile(log_path)  # type: ignore
        
        # 日志文件打开失败
        except Exception:
            logger.error("日志文件打开失败。")
            messagebox.showerror(  # type: ignore
                "错误",
                "日志文件打开失败，请手动查看日志文件。"\
                f"日志目录：{gettempdir()}"
            )

    # 退出程序
    exit(1)
