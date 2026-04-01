"""
Document Service - 文档服务 (MySQL版本)
重构为使用SQLAlchemy ORM进行MySQL持久化
"""
import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.database import get_db_context
from app.models.document import Document, DocumentChunk, Category
from app.models.user import User
from app.services.document_parser import document_parser


class DocumentService:
    """文档服务 - MySQL版本"""

    # 预定义分类
    DEFAULT_CATEGORIES = [
        "产品文档",
        "技术文档",
        "规章制度",
        "培训资料",
        "流程规范",
        "其他"
    ]

    def __init__(self):
        pass

    def _get_db(self) -> Session:
        """获取数据库会话（同步上下文）"""
        from backend.app.core.database import SessionLocal
        return SessionLocal()

    def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        file_type: Optional[str] = None,
        user_id: Optional[str] = None  # 为数据隔离预留
    ) -> Dict[str, Any]:
        """
        获取文档列表

        Args:
            user_id: 当前用户ID，用于数据隔离（可选）
        """
        db = self._get_db()
        try:
            query = db.query(Document)

            # 数据隔离：只查询用户有权限看到的文档
            if user_id:
                # 用户能看到：公共文档 + 自己的文档 + 同部门的文档
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    query = query.filter(
                        or_(
                            Document.visibility == "public",
                            Document.owner_id == user_id,
                            (Document.visibility == "department") & (Document.department == user.department)
                        )
                    )
                else:
                    query = query.filter(Document.visibility == "public")
            else:
                # 未登录用户只能看公共文档
                query = query.filter(Document.visibility == "public")

            # 分类筛选
            if category:
                query = query.filter(Document.category == category)

            # 文件类型筛选
            if file_type:
                query = query.filter(Document.file_type == file_type)

            # 关键词搜索（名称或内容）
            if keyword:
                keyword_lower = f"%{keyword}%"
                query = query.filter(
                    or_(
                        Document.name.ilike(keyword_lower),
                        Document.content.ilike(keyword_lower)
                    )
                )

            # 计算总数
            total = query.count()

            # 排序和分页
            query = query.order_by(Document.updated_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            items = query.all()

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [self._doc_to_dict(doc) for doc in items]
            }
        finally:
            db.close()

    def get_document(self, doc_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取文档详情"""
        db = self._get_db()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                return None

            # 权限检查
            if not self._can_access_document(doc, user_id, db):
                return None

            return self._doc_to_dict(doc, include_content=True)
        finally:
            db.close()

    def create_document(self, doc_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """创建文档（支持解析内容）"""
        db = self._get_db()
        try:
            doc_id = str(uuid.uuid4())
            now = datetime.now()

            # 获取文件内容（二进制）
            raw_content = doc_data.get("raw_content")
            file_type = doc_data.get("file_type", "unknown")
            filename = doc_data.get("name", "未命名文档")
            category = doc_data.get("category", "其他")

            # 创建文档记录
            document = Document(
                id=doc_id,
                name=filename,
                category=category,
                file_type=file_type,
                file_size=doc_data.get("file_size", 0),
                chunk_count=0,
                owner_id=user_id,  # 上传者成为所有者
                visibility=doc_data.get("visibility", "public"),
                department=doc_data.get("department"),
                content="",
                created_at=now,
                updated_at=now
            )

            # 如果提供了二进制内容，解析文档
            if raw_content and isinstance(raw_content, bytes):
                try:
                    parse_result = document_parser.parse_document(
                        content=raw_content,
                        file_type=file_type,
                        filename=filename
                    )

                    document.content = parse_result["text"][:10000]  # 限制存储长度
                    document.chunk_count = len(parse_result["chunks"])

                    db.add(document)
                    db.flush()  # 获取文档ID

                    # 创建文档片段
                    for idx, chunk_data in enumerate(parse_result["chunks"]):
                        chunk = DocumentChunk(
                            id=str(uuid.uuid4()),
                            document_id=doc_id,
                            content=chunk_data.get("content", "")[:5000],
                            page=chunk_data.get("page"),
                            chunk_index=idx,
                            metadata_json=json.dumps(chunk_data.get("metadata", {})) if chunk_data.get("metadata") else None
                        )
                        db.add(chunk)

                except Exception as e:
                    print(f"Error parsing document {filename}: {e}")
                    db.add(document)
            else:
                db.add(document)

            db.commit()
            db.refresh(document)

            return self._doc_to_dict(document, include_content=True)
        finally:
            db.close()

    def delete_document(self, doc_id: str, user_id: Optional[str] = None) -> bool:
        """删除文档（只有所有者或管理员可以删除）"""
        db = self._get_db()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                return False

            # 权限检查：只有所有者可以删除
            if user_id and doc.owner_id != user_id:
                # TODO: 检查用户是否是管理员
                return False

            db.delete(doc)
            db.commit()
            return True
        finally:
            db.close()

    def get_categories(self) -> List[Dict[str, Any]]:
        """获取分类列表及文档数量"""
        db = self._get_db()
        try:
            # 从数据库分类表获取
            categories = db.query(Category).filter(Category.is_active == "Y").order_by(Category.sort_order).all()

            result = []
            for cat in categories:
                # 统计每个分类的文档数量
                count = db.query(Document).filter(
                    Document.category == cat.name,
                    Document.visibility == "public"  # 只统计公共文档
                ).count()

                result.append({
                    "name": cat.name,
                    "count": count
                })

            return result
        finally:
            db.close()

    def get_stats(self) -> Dict[str, Any]:
        """获取文档统计"""
        db = self._get_db()
        try:
            total_docs = db.query(Document).filter(Document.visibility == "public").count()
            total_chunks = db.query(func.sum(Document.chunk_count)).filter(
                Document.visibility == "public"
            ).scalar() or 0

            return {
                "document_count": total_docs,
                "chunk_count": total_chunks,
                "categories": self.get_categories()
            }
        finally:
            db.close()

    def _doc_to_dict(self, doc: Document, include_content: bool = False) -> Dict[str, Any]:
        """将文档模型转换为字典"""
        result = {
            "id": doc.id,
            "name": doc.name,
            "category": doc.category,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        }

        if include_content:
            result["content"] = doc.content

            # 加载片段
            chunks = [
                {
                    "id": chunk.id,
                    "content": chunk.content,
                    "page": chunk.page,
                    "metadata": json.loads(chunk.metadata_json) if chunk.metadata_json else {}
                }
                for chunk in doc.chunks
            ]
            result["chunks"] = sorted(chunks, key=lambda x: x.get("page") or 0)

        return result

    def _can_access_document(self, doc: Document, user_id: Optional[str], db: Session) -> bool:
        """检查用户是否有权限访问文档"""
        # 公共文档所有人可访问
        if doc.visibility == "public":
            return True

        # 私有文档只有所有者可访问
        if doc.visibility == "private":
            return user_id is not None and doc.owner_id == user_id

        # 部门文档需要同部门
        if doc.visibility == "department":
            if not user_id:
                return False
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            return doc.department == user.department

        return False


# 全局文档服务实例
document_service = DocumentService()
