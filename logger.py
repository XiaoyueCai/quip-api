import logging.config
from config import logging_config

# 配置日志记录
logging.config.dictConfig(logging_config)

# 获取日志记录器
logger = logging.getLogger('my_module')
