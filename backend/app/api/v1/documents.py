"""
Documents API - 文档接口
已接入用户认证和数据隔离
"""
from typing import Optional
from fastapi import APIRouter, Query, UploadFile, File, Form, Depends, HTTPException, status

from app.schemas import ApiResponse
from app.schemas.document import DocumentListResponse, CategoryListResponse
from app.services.document_service import document_service
from app.core.auth import get_current_user, require_admin
from app.models.user import User

router = APIRouter()


@router.get("", response_model=ApiResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None, description="文件类型筛选，如 pdf, docx, md"),
    current_user: User = Depends(get_current_user)
):
    """
    获取文档列表（支持分页、分类筛选、关键词搜索、文件类型筛选）

    - 用户只能看到自己有权限的文档
    - 管理员可以看到所有文档
    """
    result = document_service.list_documents(
        page=page,
        page_size=page_size,
        category=category,
        keyword=keyword,
        file_type=file_type,
        user_id=current_user.id
    )

    return ApiResponse(
        code=200,
        data=result,
        message="success"
    )


@router.get("/{doc_id}", response_model=ApiResponse)
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取文档详情

    - 检查用户是否有权限访问该文档
    """
    doc = document_service.get_document(doc_id, user_id=current_user.id)
    if doc:
        return ApiResponse(
            code=200,
            data=doc,
            message="success"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or no permission"
        )


@router.post("/upload", response_model=ApiResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None, description="文档分类"),
    visibility: Optional[str] = Form("public", description="可见性: public/department/private"),
    current_user: User = Depends(get_current_user)
):
    """
    上传文档

    支持格式：PDF、Word(docx)、Markdown、TXT

    - 上传的文档归属当前用户
    - 可设置可见性级别
    - department字段自动设置为当前用户的部门
    - chunk_count和content字段为空，由后续功能更新
    """
    # 验证可见性参数
    if visibility not in ["public", "department", "private"]:
        return ApiResponse(
            code=400,
            data=None,
            message="Invalid visibility. Must be: public, department, or private"
        )

    # 读取文件二进制内容
    content = await file.read()

    # 检查文件内容是否为空
    if not content:
        return ApiResponse(
            code=400,
            data=None,
            message="File content is empty"
        )

    # 确定文件类型
    file_type = file.filename.split(".")[-1].lower() if "." in file.filename else "unknown"

    # 验证支持的格式
    supported_types = ["pdf", "docx", "doc", "md", "markdown", "txt"]
    if file_type not in supported_types:
        return ApiResponse(
            code=400,
            data=None,
            message=f"Unsupported file type: {file_type}. Supported: {', '.join(supported_types)}"
        )

    # 创建文档记录（不解析内容，chunk_count和content留空，由其他功能后续更新）
    doc_data = {
        "name": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "category": category,
        "visibility": visibility,
        "department": current_user.department,  # 使用当前用户的部门
        "raw_content": None  # 不传递二进制内容，避免解析
    }

    # parse=False 表示只保存文件记录，不解析内容和生成chunks
    doc = document_service.create_document(doc_data, user_id=current_user.id, parse=False)

    return ApiResponse(
        code=200,
        data={
            "id": doc["id"],
            "name": doc["name"],
            "category": doc["category"],
            "file_type": doc["file_type"],
            "file_size": doc["file_size"],
            "chunk_count": 0,  # 初始为0，后续由其他功能更新
            "visibility": visibility,
            "department": current_user.department,
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
            "metadata": doc.get("metadata", {}),
            "preview": ""  # content为空，预览为空
        },
        message="Document uploaded successfully"
    )


@router.delete("/{doc_id}", response_model=ApiResponse)
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除文档

    - 只有文档所有者或管理员可以删除
    """
    success = document_service.delete_document(doc_id, user_id=current_user.id)
    if success:
        return ApiResponse(
            code=200,
            data=None,
            message="Document deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or no permission to delete"
        )


@router.get("/categories/all", response_model=ApiResponse)
async def get_categories(
    current_user: User = Depends(get_current_user)
):
    """
    获取文档分类列表
    """
    categories = document_service.get_categories()
    return ApiResponse(
        code=200,
        data={"categories": categories},
        message="success"
    )
