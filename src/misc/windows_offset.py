from typing import Optional


def calculate_offset(
    windows_width: int,
    windows_height: int,
    initial_x_offset: Optional[int],
    initial_y_offset: Optional[int],
    center_x_offset: Optional[int],
    center_y_offset: Optional[int],
) -> tuple[int, int]:
    """
    计算窗口偏移量。

    :param windows_width: 窗口宽度
    :param windows_height: 窗口高度
    :param initial_x_offset: 初始化X偏移量
    :param initial_y_offset: 初始化Y偏移量
    :param center_x_offset: 中心X偏移量
    :param center_y_offset: 中心Y偏移量
    :return: 窗口偏移量
    """

    # 计算并应用窗口偏移量
    x_offset, y_offset = 0, 0

    if initial_x_offset is not None:
        x_offset += initial_x_offset
    elif center_x_offset is not None:
        x_offset += center_x_offset - windows_width // 2

    if initial_y_offset is not None:
        y_offset += initial_y_offset
    elif center_y_offset is not None:
        y_offset += center_y_offset - windows_height // 2

    return x_offset, y_offset
