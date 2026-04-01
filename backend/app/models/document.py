"""
Document Related Models
文档相关模型
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Document(Base):
    """文档表 - 支持数据隔离（通过owner_id）"""
    __tablename__ = "documents"
    id = Column(String(36), primary_key=True, comment="文档UUID")
    name = Column(String(255), nullable=False, comment="文档名称")
    category = Column(String(100), nullable=False, comment="分类")
    file_type = Column(String(20), nullable=False, comment="文件类型：pdf/docx/md/txt")
    file_size = Column(Integer, default=0, comment="文件大小（字节）")
    chunk_count = Column(Integer, default=0, comment="片段数量")

    # 数据隔离字段：null表示公共文档，有值表示属于特定用户
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="文档所有者ID，null为公共文档")

    # 访问控制字段（为未来权限系统预留）
    visibility = Column(String(20), default="public", comment="可见性：public/private/department")
    department = Column(String(100), nullable=True, comment="所属部门（部门级可见时使用）")

    # 内容存储
    content = Column(Text, nullable=True, comment="文档解析后的文本内容")

    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", lazy="dynamic", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="document", lazy="dynamic", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("idx_doc_category", "category"),
        Index("idx_doc_file_type", "file_type"),
        Index("idx_doc_owner", "owner_id"),
        Index("idx_doc_visibility", "visibility"),
        Index("idx_doc_name", "name"),  # 用于搜索
    )

    def __repr__(self):
        return f"<Document {self.name}>"


class DocumentChunk(Base):
    """文档片段表 - 存储分块后的内容"""
    __tablename__ = "document_chunks"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, comment="片段UUID")
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, comment="所属文档ID")
    content = Column(Text, nullable=False, comment="片段内容")
    page = Column(Integer, nullable=True, comment="页码")
    chunk_index = Column(Integer, default=0, comment="片段序号")

    # 元数据（JSON字符串存储）
    metadata_json = Column(Text, nullable=True, comment="元数据JSON")

    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关系
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk {self.id}>"


class Category(Base):
    """文档分类表 - 预定义分类"""
    __tablename__ = "categories"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, comment="分类UUID")
    name = Column(String(100), nullable=False, unique=True, comment="分类名称")
    description = Column(Text, nullable=True, comment="分类描述")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(String(1), default="Y", comment="是否启用：Y/N")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<Category {self.name}>"
