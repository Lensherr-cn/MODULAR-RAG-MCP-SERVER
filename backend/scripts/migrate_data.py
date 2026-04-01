#!/usr/bin/env python3
"""
Data Migration Script
数据迁移脚本 - 将JSON数据迁移到MySQL
"""
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))  # 添加父目录到路径

import json
import uuid
from datetime import datetime
from app.core.database import SessionLocal

# 必须导入所有模型以确保SQLAlchemy能解析所有relationship
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.chat import Conversation, ChatMessage


def migrate_documents():
    """迁移文档数据"""
    # 读取JSON文件
    data_file = PROJECT_ROOT / "data" / "documents.json"

    if not data_file.exists():
        print(f"Data file not found: {data_file}")
        print("No existing data to migrate.")
        return

    print(f"Loading data from {data_file}...")
    with open(data_file, 'r', encoding='utf-8') as f:
        documents_data = json.load(f)

    db = SessionLocal()
    try:
        # 获取默认用户（用于作为文档所有者）
        default_user = db.query(User).filter(User.username == "admin").first()
        owner_id = default_user.id if default_user else None

        migrated_count = 0

        for doc_id, doc_data in documents_data.items():
            # 检查是否已存在
            existing = db.query(Document).filter(Document.id == doc_id).first()
            if existing:
                print(f"  Skipping existing document: {doc_data.get('name', doc_id)}")
                continue

            # 解析时间
            created_at = parse_datetime(doc_data.get('created_at'))
            updated_at = parse_datetime(doc_data.get('updated_at'))

            # 创建文档记录
            document = Document(
                id=doc_id,
                name=doc_data.get('name', '未命名文档'),
                category=doc_data.get('category', '其他'),
                file_type=doc_data.get('file_type', 'unknown'),
                file_size=doc_data.get('file_size', 0),
                chunk_count=doc_data.get('chunk_count', 0),
                owner_id=owner_id,  # 分配给默认用户
                visibility='public',  # 默认公共可见
                content=doc_data.get('content', '')[:10000],  # 限制长度
                created_at=created_at,
                updated_at=updated_at
            )
            db.add(document)

            # 迁移文档片段
            chunks = doc_data.get('chunks', [])
            for idx, chunk_data in enumerate(chunks):
                chunk = DocumentChunk(
                    id=chunk_data.get('id', str(uuid.uuid4())),
                    document_id=doc_id,
                    content=chunk_data.get('content', '')[:5000],  # 限制长度
                    page=chunk_data.get('page'),
                    chunk_index=idx,
                    metadata_json=json.dumps(chunk_data.get('metadata', {})) if chunk_data.get('metadata') else None
                )
                db.add(chunk)

            migrated_count += 1
            print(f"  Migrated: {doc_data.get('name', doc_id)}")

        db.commit()
        print(f"\nMigration completed! {migrated_count} documents migrated.")

    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()


def parse_datetime(dt_str):
    """解析时间字符串"""
    if not dt_str:
        return datetime.now()

    if isinstance(dt_str, str):
        try:
            # 处理ISO格式时间
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1] + '+00:00'
            return datetime.fromisoformat(dt_str.replace('+00:00', ''))
        except:
            return datetime.now()

    return datetime.now()


def main():
    print("=" * 50)
    print("Knowledge Hub Data Migration")
    print("=" * 50)
    print()

    migrate_documents()

    print("\n" + "=" * 50)
    print("Migration finished!")
    print("=" * 50)


if __name__ == "__main__":
    main()
