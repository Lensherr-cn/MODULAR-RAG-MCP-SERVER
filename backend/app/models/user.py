"""
User Related Models
用户相关模型
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """用户表 - 为后续数据隔离预留"""
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, comment="用户UUID")
    username = Column(String(50), nullable=False, unique=True, comment="用户名")
    email = Column(String(100), nullable=True, comment="邮箱")
    department = Column(String(100), nullable=True, comment="部门")
    avatar = Column(String(500), nullable=True, comment="头像URL")
    password_hash = Column(String(255), nullable=True, comment="密码哈希（预留）")
    role = Column(String(20), default="user", comment="角色：admin/user/guest")
    is_active = Column(String(1), default="Y", comment="是否启用：Y/N")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    documents = relationship("Document", back_populates="owner", lazy="dynamic")
    query_history = relationship("QueryHistory", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class QueryHistory(Base):
    """查询历史表"""
    __tablename__ = "query_history"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, comment="记录UUID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    query = Column(Text, nullable=False, comment="查询内容")
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, comment="关联对话ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关系
    user = relationship("User", back_populates="query_history")
    conversation = relationship("Conversation", back_populates="queries")

    def __repr__(self):
        return f"<QueryHistory {self.id}>"


class Favorite(Base):
    """用户收藏表"""
    __tablename__ = "favorites"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, comment="收藏UUID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, comment="文档ID")
    created_at = Column(DateTime, default=func.now(), comment="收藏时间")

    # 关系
    user = relationship("User", back_populates="favorites")
    document = relationship("Document", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite user={self.user_id} doc={self.document_id}>"


class Feedback(Base):
    """用户反馈表"""
    __tablename__ = "feedbacks"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, comment="反馈UUID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    content = Column(Text, nullable=False, comment="反馈内容")
    feedback_type = Column(String(20), nullable=False, comment="类型：positive/negative/suggestion")
    query_id = Column(String(36), ForeignKey("query_history.id", ondelete="SET NULL"), nullable=True, comment="关联查询ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关系
    user = relationship("User", back_populates="feedbacks")
    query = relationship("QueryHistory")

    def __repr__(self):
        return f"<Feedback {self.id}>"
