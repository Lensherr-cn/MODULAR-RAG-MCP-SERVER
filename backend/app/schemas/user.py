from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """用户资料"""
    id: str = Field(description="用户ID")
    username: str = Field(description="用户名")
    department: Optional[str] = Field(default=None, description="部门")
    email: Optional[str] = Field(default=None, description="邮箱")
    avatar: Optional[str] = Field(default=None, description="头像URL")
    created_at: datetime = Field(description="注册时间")


class QueryHistory(BaseModel):
    """查询历史"""
    id: str = Field(description="记录ID")
    query: str = Field(description="查询内容")
    conversation_id: Optional[str] = Field(default=None, description="对话ID")
    created_at: datetime = Field(description="创建时间")


class Favorite(BaseModel):
    """收藏"""
    id: str = Field(description="收藏ID")
    document_id: str = Field(description="文档ID")
    document_name: str = Field(description="文档名称")
    created_at: datetime = Field(description="收藏时间")


class Feedback(BaseModel):
    """反馈"""
    id: str = Field(description="反馈ID")
    content: str = Field(description="反馈内容")
    type: str = Field(description="类型：positive/negative/suggestion")
    created_at: datetime = Field(description="创建时间")


class FeedbackRequest(BaseModel):
    """提交反馈请求"""
    content: str = Field(description="反馈内容")
    type: str = Field(description="类型：positive/negative/suggestion")
    query_id: Optional[str] = Field(default=None, description="关联查询ID")
