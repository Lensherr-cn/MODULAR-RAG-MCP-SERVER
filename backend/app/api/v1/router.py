"""
API Router - 路由汇总
"""
from fastapi import APIRouter

from app.api.v1 import auth, chat, documents, user, stats, feedback

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
