"""
Backend Entry Point
可以直接运行: python main.py
"""
import sys
import warnings
from pathlib import Path

# 忽略 jieba 的 SyntaxWarning 警告
warnings.filterwarnings("ignore", category=SyntaxWarning, module="jieba")

# 确保可以导入app
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
