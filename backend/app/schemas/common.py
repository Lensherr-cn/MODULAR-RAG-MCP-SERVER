from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """通用API响应模型"""
    code: int = Field(default=200, description="状态码")
    data: Optional[dict] = Field(default=None, description="响应数据")
    message: Optional[str] = Field(default=None, description="提示信息")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginationResponse(BaseModel):
    """分页响应"""
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")


class TokenPayload(BaseModel):
    """JWT Token payload"""
    sub: Optional[str] = None
    exp: Optional[datetime] = None
