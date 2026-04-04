"""
Documents API - 文档接口
已接入用户认证和数据隔离
"""
import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.schemas import ApiResponse
from app.schemas.document import DocumentListResponse, CategoryListResponse
from app.services.document_service import document_service
from app.core.auth import get_current_user, require_admin
from app.models.user import User
import uuid

# 文件上传目录配置
UPLOAD_DIR = Path(__file__).resolve().parents[4] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

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


@router.get("/categories/all", response_model=ApiResponse)
async def get_categories(
    current_user: User = Depends(get_current_user)
):
    """
    获取文档分类列表及各分类下的文档数量

    - 返回每个分类及其下的文档数量
    - 数量根据当前用户的权限计算（公共文档 + 自己的文档 + 同部门文档）
    """
    categories = document_service.get_categories(user_id=current_user.id)
    return ApiResponse(
        code=200,
        data={"categories": categories},
        message="success"
    )


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载文档

    - 检查用户是否有权限访问该文档
    - 返回文件流供下载
    """
    doc = document_service.get_document(doc_id, user_id=current_user.id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or no permission"
        )

    file_path = doc.get("url")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    return FileResponse(
        path=file_path,
        filename=doc["name"],
        media_type="application/octet-stream"
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
    - 文件保存到本地uploads目录，路径存入url字段
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

    # 生成文件保存路径
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    # 保存文件到本地
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        return ApiResponse(
            code=500,
            data=None,
            message=f"Failed to save file: {str(e)}"
        )

    # 创建文档记录（不解析内容，chunk_count和content留空，由其他功能后续更新）
    doc_data = {
        "name": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "category": category,
        "visibility": visibility,
        "department": current_user.department,  # 使用当前用户的部门
        "url": str(file_path),  # 文件存储路径
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
            "url": str(file_path),  # 返回文件路径
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


@router.post("/{doc_id}/favorite", response_model=ApiResponse)
async def toggle_favorite(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    切换文档收藏状态（收藏/取消收藏）

    - 用户只能收藏自己有权限访问的文档
    """
    result = document_service.toggle_favorite(doc_id, user_id=current_user.id)

    if result.get("message") == "Document not found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if result.get("message") == "No permission to access this document":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this document"
        )

    return ApiResponse(
        code=200,
        data={"is_favorite": result["is_favorite"]},
        message=result["message"]
    )


@router.get("/{doc_id}/favorite/status", response_model=ApiResponse)
async def get_favorite_status(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取文档的收藏状态

    - 返回当前用户是否已收藏该文档
    """
    is_fav = document_service.is_favorite(doc_id, user_id=current_user.id)

    return ApiResponse(
        code=200,
        data={"is_favorite": is_fav},
        message="success"
    )


@router.get("/favorites/my", response_model=ApiResponse)
async def get_my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的收藏文档列表

    - 支持分页
    - 只返回用户有权限访问的收藏文档
    """
    result = document_service.get_favorites(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )

    return ApiResponse(
        code=200,
        data=result,
        message="success"
    )


@router.get("/favorites/count", response_model=ApiResponse)
async def get_favorite_count(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的收藏数量

    - 用于个人中心等场景展示
    """
    count = document_service.get_favorite_count(user_id=current_user.id)

    return ApiResponse(
        code=200,
        data={"count": count},
        message="success"
    )
