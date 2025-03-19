import logging
import os

from config import LOG_PATH


# 清空已有日志文件
if os.path.exists(LOG_PATH):
    os.remove(LOG_PATH)

# 设置日志配置
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
)

# 获取日志对象
logger: logging.Logger = logging.getLogger(__name__)

logger.info("日志文件创建成功")
