"""
FastAPI Main Entry Point
企业知识库后端API服务
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
src_path = PROJECT_ROOT / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.api.v1 import api_router
from backend.app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    print("=" * 50)
    print("Enterprise Knowledge Hub API Starting...")
    print(f"Version: {settings.VERSION}")
    print(f"Debug Mode: {settings.DEBUG}")
    print("=" * 50)

    yield

    # 关闭时执行
    print("Shutting down...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查
@app.get("/health", tags=["health"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


# 根路径
@app.get("/", tags=["root"])
async def root():
    """API根路径"""
    return {
        "message": "Enterprise Knowledge Hub API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


# 注册API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
