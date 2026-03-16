"""
叠加层管理器。
管理所有区域调整窗口的显示/隐藏，处理首次启动逻辑，
将调整后的坐标转换回比例值并写回 config.yaml。
"""

from pathlib import Path
from loguru import logger
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq

from capture import find_game_window, region_to_pixels
from config import REGIONS
from ui.overlay_window import OverlayWindow


# config.yaml 的路径（与 config.py 里的逻辑一致）
def _config_path() -> Path:
    import sys

    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "config.yaml"
    return Path(__file__).parent.parent / "config.yaml"


class OverlayManager:
    """管理所有区域叠加窗口的生命周期。

    职责：
    - 首次启动时自动显示叠加层
    - 热键 c 切换显示/隐藏
    - 用户调整后将像素坐标转换回比例值，写回 config.yaml
    """

    def __init__(self, parent) -> None:
        self._parent = parent
        self._windows: dict[str, OverlayWindow] = {}
        self._visible = False

    def toggle(self) -> None:
        """切换叠加层显示/隐藏。热键 c 调用此方法。"""
        if self._visible:
            self._hide()
        else:
            self._show()

    def show_if_first_launch(self) -> None:
        """如果是首次启动，自动显示叠加层并将标志写为 false。
        只有叠加层成功显示后才写入 false，避免窗口未显示就消耗掉首次启动机会。
        """
        from config import raw_config

        if raw_config.get("IS_FIRST_LAUNCH", False):
            logger.info("首次启动，自动显示区域调整叠加层")
            if self._show():
                self._set_first_launch_done()

    def _show(self) -> bool:
        """创建并显示所有区域的叠加窗口。返回是否成功显示。
        找不到游戏窗口时，用屏幕尺寸作为 fallback，确保 overlay 始终能显示。
        """
        if self._visible:
            return True

        # 优先用游戏窗口位置，找不到时 fallback 到屏幕尺寸
        window_rect = find_game_window()
        if window_rect is None:
            logger.warning("找不到游戏窗口，使用屏幕尺寸显示叠加层")
            sw = self._parent.winfo_screenwidth()
            sh = self._parent.winfo_screenheight()
            window_rect = (0, 0, sw, sh)

        for name in REGIONS:
            x1, y1, x2, y2 = region_to_pixels(name, window_rect)
            win = OverlayWindow(self._parent, name, x1, y1, x2, y2)
            win.register_on_change(self._on_region_changed)
            self._windows[name] = win

        self._visible = True
        logger.info("区域调整叠加层已显示")
        return True

    def _hide(self) -> None:
        """销毁所有叠加窗口。"""
        for win in self._windows.values():
            win.destroy()
        self._windows.clear()
        self._visible = False
        logger.info("区域调整叠加层已隐藏")

    def _on_region_changed(
        self, region_name: str, rect: tuple[int, int, int, int]
    ) -> None:
        """用户拖拽完成后触发：把新的像素坐标转换成比例值，写回 config.yaml。"""
        x1, y1, x2, y2 = rect

        # 重新获取游戏窗口位置，把屏幕像素坐标转换回比例值
        # 找不到游戏窗口时用屏幕尺寸作为 fallback（与 _show 的 fallback 保持一致）
        window_rect = find_game_window()
        if window_rect is None:
            sw = self._parent.winfo_screenwidth()
            sh = self._parent.winfo_screenheight()
            wl, wt, ww, wh = 0, 0, sw, sh
        else:
            wl, wt = window_rect[0], window_rect[1]
            ww, wh = window_rect[2] - wl, window_rect[3] - wt

        # 转换为比例值，保留 4 位小数
        rx1 = round((x1 - wl) / ww, 4)
        ry1 = round((y1 - wt) / wh, 4)
        rx2 = round((x2 - wl) / ww, 4)
        ry2 = round((y2 - wt) / wh, 4)

        logger.info(
            f"区域 [{region_name}] 调整为比例坐标: [{rx1}, {ry1}] [{rx2}, {ry2}]"
        )
        self._write_region_to_yaml(region_name, [[rx1, ry1], [rx2, ry2]])

    def _load_yaml(self, path: Path):
        """用 ruamel.yaml 读取配置，保留注释和格式。"""
        yaml = YAML()
        yaml.preserve_quotes = True
        with open(path, "r", encoding="utf-8") as f:
            return yaml, yaml.load(f)

    def _save_yaml(self, path: Path, yaml: YAML, data) -> None:
        """将数据写回 config.yaml，保留原有注释。"""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

    def _flow_seq(self, items) -> CommentedSeq:
        """创建 flow style 的序列，写入 yaml 时显示为行内格式 [a, b] 而非多行块。"""
        seq = CommentedSeq(items)
        seq.fa.set_flow_style()
        return seq

    def _write_region_to_yaml(self, region_name: str, value: list) -> None:
        """将单个区域的新坐标写回 config.yaml，保留注释和格式。"""
        path = _config_path()
        try:
            yaml, data = self._load_yaml(path)
            # 用 flow style 写坐标，保持与原始格式一致：[ [x1, y1], [x2, y2] ]
            flow_value = self._flow_seq([self._flow_seq(pt) for pt in value])
            data["REGIONS"][region_name] = flow_value
            self._save_yaml(path, yaml, data)
            logger.success(f"已将区域 [{region_name}] 保存到 config.yaml")
        except Exception as e:
            logger.error(f"写入 config.yaml 失败: {e}")

    def _set_first_launch_done(self) -> None:
        """将 IS_FIRST_LAUNCH 改为 false 并写回 config.yaml，保留注释和格式。"""
        path = _config_path()
        try:
            yaml, data = self._load_yaml(path)
            data["IS_FIRST_LAUNCH"] = False
            self._save_yaml(path, yaml, data)
            logger.info("已将 IS_FIRST_LAUNCH 设为 false")
        except Exception as e:
            logger.error(f"写入 IS_FIRST_LAUNCH 失败: {e}")
