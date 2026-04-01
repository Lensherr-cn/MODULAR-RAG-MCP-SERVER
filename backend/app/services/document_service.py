"""
Document Service - 文档服务
"""
import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from app.services.document_parser import document_parser


class DocumentService:
    """文档服务"""

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
        self.data_dir = Path(__file__).resolve().parents[2] / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.documents_file = self.data_dir / "documents.json"
        self.documents: Dict[str, Dict] = {}
        self._load_documents()

    def _load_documents(self):
        """加载文档数据"""
        if self.documents_file.exists():
            try:
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            except Exception:
                self.documents = {}
        else:
            # 初始化示例数据
            self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例文档数据"""
        sample_docs = [
            {
                "id": "doc_001",
                "name": "产品使用手册 v2.0.pdf",
                "category": "产品文档",
                "file_type": "pdf",
                "file_size": 2457600,
                "chunk_count": 45,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "content": "第一章：产品概述\n\n本产品是一款面向企业的知识库管理系统...\n\n第二章：快速入门\n\n2.1 登录系统...",
                "chunks": [
                    {"id": "chunk_001", "content": "第一章：产品概述...", "page": 1},
                    {"id": "chunk_002", "content": "第二章：快速入门...", "page": 3},
                ]
            },
            {
                "id": "doc_002",
                "name": "技术架构设计文档.docx",
                "category": "技术文档",
                "file_type": "docx",
                "file_size": 1843200,
                "chunk_count": 32,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "content": "技术架构概述...",
                "chunks": []
            },
            {
                "id": "doc_003",
                "name": "员工手册 2024 版.pdf",
                "category": "规章制度",
                "file_type": "pdf",
                "file_size": 3174400,
                "chunk_count": 58,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "content": "员工手册内容...",
                "chunks": []
            },
            {
                "id": "doc_004",
                "name": "培训资料 - 新员工入职.md",
                "category": "培训资料",
                "file_type": "md",
                "file_size": 45000,
                "chunk_count": 12,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "content": "新员工入职培训内容...",
                "chunks": []
            },
            {
                "id": "doc_005",
                "name": "API 接口文档.pdf",
                "category": "技术文档",
                "file_type": "pdf",
                "file_size": 1200000,
                "chunk_count": 28,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "content": "API接口文档内容...",
                "chunks": []
            },
            {
                "id": "doc_006",
                "name": "产品路线图 2024.pdf",
                "category": "产品文档",
                "file_type": "pdf",
                "file_size": 3200000,
                "chunk_count": 15,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "content": "产品路线图内容...",
                "chunks": []
            },
        ]

        for doc in sample_docs:
            self.documents[doc["id"]] = doc

        self._save_documents()

    def _save_documents(self):
        """保存文档数据"""
        try:
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving documents: {e}")

    def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取文档列表

        Returns:
            {
                "total": int,
                "page": int,
                "page_size": int,
                "items": List[Document]
            }
        """
        items = list(self.documents.values())

        # 分类筛选
        if category:
            items = [d for d in items if d["category"] == category]

        # 类型筛选
        if file_type:
            items = [d for d in items if d["file_type"] == file_type]

        # 关键词搜索
        if keyword:
            keyword_lower = keyword.lower()
            items = [
                d for d in items
                if keyword_lower in d["name"].lower()
                or keyword_lower in d.get("content", "").lower()
            ]

        # 按更新时间排序
        items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        # 分页
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        items = items[start:end]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """获取文档详情"""
        return self.documents.get(doc_id)

    def get_categories(self) -> List[Dict[str, Any]]:
        """获取分类列表及文档数量"""
        category_counts = {}
        for doc in self.documents.values():
            cat = doc.get("category", "其他")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # 确保所有默认分类都在列表中
        for cat in self.DEFAULT_CATEGORIES:
            if cat not in category_counts:
                category_counts[cat] = 0

        return [
            {"name": name, "count": count}
            for name, count in sorted(category_counts.items())
        ]

    def create_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建文档（支持解析内容）"""
        doc_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # 获取文件内容（二进制）
        raw_content = doc_data.get("raw_content")
        file_type = doc_data.get("file_type", "unknown")
        filename = doc_data.get("name", "未命名文档")

        # 初始化文档数据
        doc = {
            "id": doc_id,
            "name": filename,
            "category": doc_data.get("category", "其他"),
            "file_type": file_type,
            "file_size": doc_data.get("file_size", 0),
            "chunk_count": 0,
            "created_at": now,
            "updated_at": now,
            "content": doc_data.get("content", ""),
            "chunks": [],
            "metadata": {}
        }

        # 如果提供了二进制内容，解析文档
        if raw_content and isinstance(raw_content, bytes):
            try:
                parse_result = document_parser.parse_document(
                    content=raw_content,
                    file_type=file_type,
                    filename=filename
                )

                doc["content"] = parse_result["text"][:10000]  # 限制存储长度
                doc["chunks"] = parse_result["chunks"]
                doc["chunk_count"] = len(parse_result["chunks"])
                doc["metadata"] = parse_result["metadata"]

            except Exception as e:
                print(f"Error parsing document {filename}: {e}")
                doc["metadata"]["parse_error"] = str(e)

        self.documents[doc_id] = doc
        self._save_documents()
        return doc

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save_documents()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取文档统计"""
        total_docs = len(self.documents)
        total_chunks = sum(d.get("chunk_count", 0) for d in self.documents.values())

        return {
            "document_count": total_docs,
            "chunk_count": total_chunks,
            "categories": self.get_categories()
        }


# 全局文档服务实例
document_service = DocumentService()
