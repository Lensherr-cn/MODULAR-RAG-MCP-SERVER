"""
Documents API - 文档接口
"""
from typing import Optional
from fastapi import APIRouter, Query, UploadFile, File

from app.schemas import ApiResponse
from app.schemas.document import DocumentListResponse, CategoryListResponse
from app.services.document_service import document_service

router = APIRouter()


@router.get("", response_model=ApiResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None, description="文件类型筛选，如 pdf, docx, md")
):
    """
    获取文档列表（支持分页、分类筛选、关键词搜索、文件类型筛选）
    """
    result = document_service.list_documents(
        page=page,
        page_size=page_size,
        category=category,
        keyword=keyword,
        file_type=file_type
    )

    return ApiResponse(
        code=200,
        data=result,
        message="success"
    )


@router.get("/{doc_id}", response_model=ApiResponse)
async def get_document(doc_id: str):
    """
    获取文档详情
    """
    doc = document_service.get_document(doc_id)
    if doc:
        return ApiResponse(
            code=200,
            data=doc,
            message="success"
        )
    else:
        return ApiResponse(
            code=404,
            data=None,
            message="Document not found"
        )


@router.post("/upload", response_model=ApiResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = Query(None, description="文档分类")
):
    """
    上传文档

    支持格式：PDF、Word(docx)、Markdown、TXT
    文档内容会被自动解析和分块
    """
    # 读取文件二进制内容
    content = await file.read()

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

    # 创建文档记录（会自动解析内容）
    doc_data = {
        "name": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "category": category,
        "raw_content": content  # 传递二进制内容给解析器
    }

    doc = document_service.create_document(doc_data)

    return ApiResponse(
        code=200,
        data={
            "id": doc["id"],
            "name": doc["name"],
            "category": doc["category"],
            "file_type": doc["file_type"],
            "file_size": doc["file_size"],
            "chunk_count": doc["chunk_count"],
            "created_at": doc["created_at"],
            "metadata": doc.get("metadata", {}),
            "preview": doc["content"][:500] if doc["content"] else ""
        },
        message="Document uploaded and parsed successfully"
    )


@router.delete("/{doc_id}", response_model=ApiResponse)
async def delete_document(doc_id: str):
    """
    删除文档
    """
    success = document_service.delete_document(doc_id)
    if success:
        return ApiResponse(
            code=200,
            data=None,
            message="Document deleted successfully"
        )
    else:
        return ApiResponse(
            code=404,
            data=None,
            message="Document not found"
        )


@router.get("/categories/all", response_model=ApiResponse)
async def get_categories():
    """
    获取文档分类列表
    """
    categories = document_service.get_categories()
    return ApiResponse(
        code=200,
        data={"categories": categories},
        message="success"
    )
