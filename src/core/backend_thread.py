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
        self._backend_logic = BackendLogic()
        self._backend_logic.set_stop_event(self._stop_event)
        self._update_thread()

    def _update_thread(self) -> None:
        """更新后端线程"""
        self._thread = Thread(target=self._backend_logic.run, daemon=True)

    def start(self) -> None:
        """启动后端线程"""
        self._stop_event.clear()
        if not self.is_running:
            self._thread.start()
            return logger.success("后端线程启动成功")
        return logger.warning("后端线程已在运行中，无需重复启动")

    def terminate(self) -> None:
        """由前段调用，终止后端线程"""
        if self.is_running:
            self._stop_event.set()
            self._thread.join()
            self._update_thread()
            return logger.success("后端线程终止成功")
        return logger.warning("后端线程已停止，无需再次终止")

    @property
    def is_running(self) -> bool:
        return self._thread.is_alive()
