"""
自定义异常类模块，包含模板加载失败和游戏状态异常。
"""


class TemplateLoadingError(Exception):
    """
    模板加载失败异常，当无法加载模板时抛出。
    """

    def __init__(self, template_path: str) -> None:
        """
        初始化异常类。

        :param template_path: 模板路径
        """
        super().__init__(f"无法加载模板: {template_path}")
        self.template_path = template_path


class ScreenshotError(Exception):
    """
    截图或截图裁剪失败异常，当无法正确截取区域时抛出。
    """
