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


@dataclass
class StringLabelsProperty:
    """记牌器标签样式变量类，用于动态更改标签的某个特定样式"""

    init_value: dict[WindowsType, CardStrDict]

    def __post_init__(self) -> None:
        self._counters = {
            window: _create_cardvar_dict(init_value)
            for window, init_value in self.init_value.items()
        }

    def reset(self) -> None:
        """重置样式值为初始值"""
        for window, counters in self._counters.items():
            _modify_cardvar_dict(counters, self.init_value[window])

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


@singleton
@dataclass
class LabelProperties:
    def __post_init__(self) -> None:
        self._init_variables()

    def _init_variables(self) -> None:
        """初始化标签样式变量"""
        self._text_color = StringLabelsProperty(
            {
                WindowsType.MAIN: {card: "black" for card in Card},
                WindowsType.LEFT: {card: "black" for card in Card},
                WindowsType.RIGHT: {card: "black" for card in Card},
            }
        )

    @property
    def text_color(self) -> StringLabelsProperty:
        """获取标签样式变量"""
        if not hasattr(self, "_text_color"):
            self._init_variables()
        return self._text_color

    def reset(self) -> None:
        """删除标签样式变量以避免在关闭窗口后重复使用Tkinter变量"""
        del self._text_color
