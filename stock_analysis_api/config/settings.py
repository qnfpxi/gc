# 配置管理模块
from dynaconf import Dynaconf
from pathlib import Path
import os

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent

# 配置实例
settings = Dynaconf(
    envvar_prefix="STOCK_API",
    settings_files=[
        BASE_DIR / 'config.yaml',
        BASE_DIR / '.env'
    ],
    environments=True,
    load_dotenv=True,
    defaults={
        "TUSHARE_TOKEN": "",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_PASSWORD": None,
        "API_KEYS": "workflow-key-1,workflow-key-2,workflow-key-3",
        "REQUIRE_AUTH": True,
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "stock_api.log",
        "LOG_FILE_MAX_BYTES": 10 * 1024 * 1024,
        "LOG_FILE_BACKUP_COUNT": 5,
        "PREHEAT_TOP_N_STOCKS": 0,
        "MAX_WORKERS": 4,
        "REQUEST_TIMEOUT": 30,
        "RATE_LIMIT_PER_MINUTE": 100,
    }
)

# 应用参数
app_params = settings.get('APP_PARAMS', {})
template_settings = settings.get('TEMPLATE_SETTINGS', {})

# 验证必需的配置
def validate_config():
    """验证配置完整性"""
    required_settings = ['TUSHARE_TOKEN']
    missing = [key for key in required_settings if not settings.get(key)]
    
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")

# 导出配置
__all__ = ['settings', 'app_params', 'template_settings', 'validate_config']
