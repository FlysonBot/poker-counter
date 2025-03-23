"""
简单的计数器模块，用于做记牌器的父类。
"""

import tkinter as tk
from typing import Callable

from logger import logger


class TkinterCounter:
    """
    简单的计数器类，用于做记牌器的父类。
    """

    def __init__(
        self, initial_counts: dict[str, int], operation: Callable[[int], int]
    ) -> None:
        """
        初始化计数器，重置牌数为初始值。

        :param initial_counts: 初始值
        :param operation: 运算函数（如加法、减法等）
        """

        self._initial_counts = initial_counts
        self._operation = operation

        self._counts: dict[str, tk.IntVar] = {
            key: tk.IntVar(value=value) for key, value in self._initial_counts.items()
        }

    def reset(self) -> None:
        """
        重置计数器，将牌数恢复为初始值。
        """

        for key, value in self._initial_counts.items():
            self._counts[key].set(value)

    def count(self, item: str) -> None:
        """
        标记一个牌型，并更新计数器。

        :param item: 牌型
        """

        new_count = self._operation(self.get_count(item).get())

        if new_count < 0:
            logger.warning(f"尝试标记不存在的牌型或已出完的牌：{item}")

        self._counts[item].set(new_count)

    def get_count(self, item: str) -> tk.IntVar:
        """
        获取指定牌型的当前计数。

        :param item: 牌型
        :return: 牌型的当前计数Tkinter变量
        """
        return self._counts[item]
