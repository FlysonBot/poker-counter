"""
自定义异常类
"""

class TemplateLoadingError(Exception):
    """模板加载失败异常"""
    def __init__(self, template_path: str):
        super().__init__(f"无法加载模板: {template_path}")
        self.template_path = template_path

class GameStateError(Exception):
    """游戏状态异常"""
    pass
