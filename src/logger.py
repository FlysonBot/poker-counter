import logging
import os

# 获取桌面路径
desktop_path: str = os.path.expanduser("~")

# 设置日志文件名并清空已有日志文件
log_file: str = os.path.join(desktop_path, "poker-counter.log")
if os.path.exists(log_file):
    os.remove(log_file)

# 设置日志配置
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
)

# 获取日志对象
logger: logging.Logger = logging.getLogger(__name__)

logger.info("日志文件创建成功")
