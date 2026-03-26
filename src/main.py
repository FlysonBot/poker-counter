"""
程序入口模块。

初始化 loguru 日志（按天滚动、自动清理旧文件），注册主线程和子线程的全局异常处理器，
monkey-patch tkinter 的 attributes() 以兼容不支持某些 window attribute 的环境，
最后启动 MasterWindow 主循环。
"""

import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from loguru import logger

from config import LOG_LEVEL, LOG_RETENTION
from ui.counter_window import open_latest_log
from ui.master_window import MasterWindow

# 部分 tkinter window attribute（如 -transparentcolor）在某些环境下不受支持，
# monkey-patch attributes() 忽略这些错误，避免因环境差异导致崩溃。
import tkinter as tk

# 保存原始的 attributes 方法，供安全包装版本内部调用
_orig_attributes = tk.Wm.wm_attributes


def _safe_attributes(self, *args, **kwargs):
    """调用原始 attributes() 方法，但忽略所有异常。
    某些环境不支持特定的 window attribute（如 -transparentcolor），
    原始方法会抛出异常导致程序崩溃，这里将其静默忽略。
    """
    try:
        return _orig_attributes(self, *args, **kwargs)
    except Exception:
        pass


# 将 tkinter 所有窗口的 attributes() 方法替换为上面定义的 _safe_attributes，
# 这样后续任何窗口调用 attributes()（如设置 -transparentcolor）出错时都会被静默忽略
tk.Wm.wm_attributes = _safe_attributes  # type: ignore
tk.Wm.attributes = _safe_attributes  # type: ignore


# ---------------------------------------------------------------------------
# 日志初始化
# ---------------------------------------------------------------------------


def get_log_dir() -> Path:
    """返回日志目录路径，不存在时自动创建。
    打包后日志存放在 exe 同级的 logs/ 目录，便于用户查找。
    开发时存放在 src/logs/。
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    log_dir = base / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


LOG_DIR = get_log_dir()

# 移除 loguru 默认的 stderr handler，重新添加自定义格式的
logger.remove()
if sys.stderr is not None:
    logger.add(sys.stderr, level=LOG_LEVEL)
logger.add(
    LOG_DIR / "{time:YYYY-MM-DD}.log",
    level=LOG_LEVEL,
    retention=f"{LOG_RETENTION} days",  # 按天数保留，超出的日志文件自动删除
    rotation="00:00",  # 每天午夜滚动到新文件
)


# ---------------------------------------------------------------------------
# 全局异常处理
# ---------------------------------------------------------------------------


def _handle_exception(exc_type, exc_value, exc_tb):
    """替换 Python 默认的异常处理，把未捕获的异常写入日志而不是只打印到控制台。"""
    if issubclass(exc_type, KeyboardInterrupt):
        logger.info("用户手动结束进程")
        sys.exit(0)
    formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical("未处理的异常:\n" + formatted)


def _handle_thread_exception(args):
    """捕获子线程未处理的异常并写入日志。"""
    if args.exc_type is SystemExit:
        return
    formatted = "".join(
        traceback.format_exception(args.exc_type, args.exc_value, args.exc_tb)
    )
    logger.critical(f"子线程 [{args.thread.name}] 未处理的异常:\n" + formatted)


def _backend_error_handler(message: str) -> None:
    """loguru ERROR 级别日志的 sink：后端出错时弹窗提示用户并安全退出。"""
    # 弹窗告知用户出错，并询问是否查看日志
    messagebox.showerror("错误", message)
    if messagebox.askyesno("日志文件", "是否打开日志文件？"):
        open_latest_log()

    # 当前函数在后台线程中运行，tkinter 不允许在子线程直接销毁窗口，
    # 所以通过 delayed_destroy() 把销毁操作调度回主线程的事件循环执行
    root: MasterWindow = tk._default_root  # type: ignore
    if root:
        root.delayed_destroy()
    os._exit(1)


# 注册全局异常处理器，确保主线程、子线程的未捕获异常都能弹窗提示并写入日志
logger.add(_backend_error_handler, level="ERROR")
sys.excepthook = _handle_exception
threading.excepthook = _handle_thread_exception


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # 在日志文件里插入启动分隔线，便于区分同一天内的多次运行
    logger.info(
        "\n\n\n"
        + "=" * 80
        + f"\n程序启动 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        + "=" * 80
    )

    # 启动主窗口，进入 tkinter 事件循环（程序入口）
    logger.success("应用程序已启动")
    MasterWindow().mainloop()
