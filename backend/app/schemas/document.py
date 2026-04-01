from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from .common import PaginationResponse


class Chunk(BaseModel):
    """文档片段"""
    id: str = Field(description="片段ID")
    content: str = Field(description="片段内容")
    page: Optional[int] = Field(default=None, description="页码")
    metadata: Optional[dict] = Field(default=None, description="元数据")


class Document(BaseModel):
    """文档模型"""
    id: str = Field(description="文档ID")
    name: str = Field(description="文档名称")
    category: str = Field(description="分类")
    file_type: str = Field(description="文件类型")
    file_size: int = Field(description="文件大小（字节）")
    chunk_count: int = Field(description="片段数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class DocumentDetail(Document):
    """文档详情"""
    content: Optional[str] = Field(default=None, description="文档内容")
    chunks: Optional[List[Chunk]] = Field(default=None, description="片段列表")


class DocumentListResponse(PaginationResponse):
    """文档列表响应"""
    items: List[Document] = Field(description="文档列表")


class Category(BaseModel):
    """分类"""
    name: str = Field(description="分类名称")
    count: int = Field(description="文档数量")


class CategoryListResponse(BaseModel):
    """分类列表响应"""
    categories: List[Category] = Field(description="分类列表")
