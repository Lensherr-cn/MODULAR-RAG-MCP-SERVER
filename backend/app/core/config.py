"""
Core Configuration
核心配置管理
"""
import os
from typing import List
from pathlib import Path


class Settings:
    """应用配置"""

    # 应用信息
    APP_TITLE = "Enterprise Knowledge Hub API"
    APP_DESCRIPTION = "企业知识库系统后端API"
    VERSION = "1.0.0"

    # 调试模式
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite开发服务器
        "http://localhost:3000",  # React开发服务器
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # 数据目录
    BASE_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = BASE_DIR / "data"

    # 确保数据目录存在
    DATA_DIR.mkdir(exist_ok=True)

    # JWT配置（简化实现，实际应使用更安全的配置）
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天


# 全局配置实例
settings = Settings()
