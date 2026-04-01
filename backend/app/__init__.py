# Enterprise Knowledge Hub Backend
from pathlib import Path

# 路径配置
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)
