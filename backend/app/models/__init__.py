"""
Database Models
数据库模型模块
"""

# 导入所有模型以确保 SQLAlchemy 正确建立关系
from app.models.user import User, QueryHistory, Favorite, Feedback
from app.models.document import Document, DocumentChunk, Category
from app.models.chat import Conversation, ChatMessage

__all__ = [
    "User",
    "QueryHistory",
    "Favorite",
    "Feedback",
    "Document",
    "DocumentChunk",
    "Category",
    "Conversation",
    "ChatMessage",
]
