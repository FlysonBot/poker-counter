"""
单例模式模块。定义单例模式的装饰器以防止多次对同一个类创建实例。
"""

from typing import Any, Callable, Type, TypeVar

T = TypeVar("T")


def singleton(cls: Type[T]) -> Callable[..., T]:
    """单例模式装饰器，用于防止多次对同一个类创建实例"""
    instances: dict[Type[T], T] = {}

    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
