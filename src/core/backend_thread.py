"""
后端线程模块，负责启动和管理后端线程。
"""

from threading import Event, Thread

from loguru import logger

from misc.singleton import singleton

from .backend_logic import BackendLogic


@singleton
class BackendThread:
    """后端线程类，用于启动和管理后端线程"""

    def __init__(self) -> None:
        self._keep_running = True
        self._stop_event = Event()
        self._backend_logic = BackendLogic(self._stop_event)
        self._thread = Thread(target=self._backend_logic.run, daemon=True)

    def start(self) -> None:
        """启动后端线程"""
        self._stop_event.clear()
        self._thread.start()
        logger.success("后端线程启动成功")

    def terminate(self) -> None:
        """由前段调用，终止后端线程"""
        self._stop_event.set()
        self._thread.join()
        logger.success("后端线程终止成功")
