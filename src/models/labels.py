"""
记牌器标签模块，用于更改记牌器标签的样式。
"""

import tkinter as tk
from dataclasses import dataclass
from typing import Callable

from misc.custom_types import Card, CardStrDict, CardStrVarDict, WindowsType
from misc.singleton import singleton


def _create_cardvar_dict(initial_value: CardStrDict) -> CardStrVarDict:
    """根据提供的初始值字典创建一个Tkinter变量字典"""
    return {key: tk.StringVar(value=value) for key, value in initial_value.items()}


def _modify_cardvar_dict(intvar_dict: CardStrVarDict, new_values: CardStrDict) -> None:
    """根据提供的新值字典修改Tkinter变量字典"""
    for key, value in new_values.items():
        intvar_dict[key].set(value)


@singleton
@dataclass
class StringLabelsProperty:
    """记牌器标签样式变量类，用于动态更改标签的某个特定样式"""

    initial_value: CardStrDict

    def __post_init__(self) -> None:
        self._counters = {
            WindowsType.MAIN: _create_cardvar_dict(self.initial_value),
            WindowsType.LEFT: _create_cardvar_dict(self.initial_value),
            WindowsType.RIGHT: _create_cardvar_dict(self.initial_value),
        }

    def reset(self) -> None:
        """重置样式值为初始值"""
        list(
            map(
                lambda counter: _modify_cardvar_dict(counter, self.initial_value),
                self._counters.values(),
            )
        )

    def change_style(self, card: Card, window: WindowsType, style: str) -> None:
        """更改标签样式值"""
        self._counters[window][card].set(style)

    def bind_callback(
        self, window: WindowsType, card: Card, callback: Callable[[str], None]
    ) -> None:
        """绑定标签样式值的变化回调函数"""
        self._counters[window][card].trace_add(
            "write",
            lambda str1, str2, str3: callback(self._counters[window][card].get()),
        )
