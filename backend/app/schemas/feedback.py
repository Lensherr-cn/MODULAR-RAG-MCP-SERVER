"""
Feedback Schemas - 用户反馈数据模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    """创建反馈请求"""
    query: Optional[str] = Field(None, description="用户问题")
    answer: Optional[str] = Field(None, description="AI回答")
    feedback_type: str = Field(..., description="反馈类型: like/dislike/comment")
    content: Optional[str] = Field(None, description="反馈内容/评论")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    message_id: Optional[str] = Field(None, description="消息ID")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    id: str
    query: Optional[str] = None
    answer: Optional[str] = None
    feedback_type: str
    content: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    created_at: datetime


class FeedbackListResponse(BaseModel):
    """反馈列表响应"""
    total: int
    items: List[FeedbackResponse]


class FeedbackStats(BaseModel):
    """反馈统计"""
    total_count: int
    like_count: int
    dislike_count: int
    comment_count: int
