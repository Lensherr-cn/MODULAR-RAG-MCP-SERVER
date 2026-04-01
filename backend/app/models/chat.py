"""
Chat Related Models
对话相关模型
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, comment="对话UUID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    title = Column(String(255), nullable=True, comment="对话标题（自动生成）")
    collection = Column(String(100), default="default", comment="知识库名称")
    message_count = Column(Integer, default=0, comment="消息数量")
    is_active = Column(String(1), default="Y", comment="是否启用：Y/N")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", lazy="dynamic", cascade="all, delete-orphan")
    queries = relationship("QueryHistory", back_populates="conversation", lazy="dynamic")

    def __repr__(self):
        return f"<Conversation {self.id}>"


class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "chat_messages"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, comment="消息UUID")
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="所属对话ID")
    role = Column(String(20), nullable=False, comment="角色：user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    message_index = Column(Integer, default=0, comment="消息序号")

    # 引用来源（JSON字符串存储）
    sources_json = Column(Text, nullable=True, comment="引用来源JSON")

    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关系
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage {self.id}>"
