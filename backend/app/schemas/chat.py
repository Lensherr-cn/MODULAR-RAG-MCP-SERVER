from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ChatSource(BaseModel):
    """引用来源"""
    document_id: str = Field(description="文档ID")
    document_name: str = Field(description="文档名称")
    chunk_id: str = Field(description="片段ID")
    content: str = Field(description="引用内容")
    page: Optional[int] = Field(default=None, description="页码")
    score: float = Field(description="相似度分数")


class ChatRequest(BaseModel):
    """问答请求"""
    query: str = Field(description="用户问题")
    collection: Optional[str] = Field(default="default", description="知识库名称")
    conversation_id: Optional[str] = Field(default=None, description="对话ID（多轮对话）")
    stream: bool = Field(default=False, description="是否流式响应")


class ChatResponse(BaseModel):
    """问答响应"""
    answer: str = Field(description="AI回答")
    sources: List[ChatSource] = Field(default=[], description="引用来源")
    related_questions: List[str] = Field(default=[], description="相关问题推荐")
    conversation_id: str = Field(description="对话ID")


class ChatMessage(BaseModel):
    """对话消息"""
    id: str = Field(description="消息ID")
    role: str = Field(description="角色：user/assistant")
    content: str = Field(description="消息内容")
    sources: Optional[List[ChatSource]] = Field(default=None, description="引用来源")
    created_at: datetime = Field(description="创建时间")


class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    conversation_id: str = Field(description="对话ID")
    messages: List[ChatMessage] = Field(description="消息列表")
