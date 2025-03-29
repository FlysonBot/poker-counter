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
        if hasattr(self, "_thread"):
            self._old_thread = self._thread
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
            self._update_thread()
            return logger.success("后端线程终止成功")
        return logger.warning("后端线程已停止，无需再次终止")

    @property
    def is_running(self) -> bool:
        """检查后端线程是否正在运行"""
        return self._thread.is_alive()

    @property
    def is_old_running(self) -> bool:
        """检查上一次启动的后端线程是否还在运行"""
        return self._old_thread.is_alive() if hasattr(self, "_old_thread") else False
