#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加 url 字段到 documents 表
"""
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

import pymysql
from app.core.config import settings


def migrate():
    """添加 url 字段到 documents 表"""
    print("Connecting to MySQL...")

    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4'
    )

    try:
        with conn.cursor() as cursor:
            # 检查 url 字段是否已存在
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = 'documents'
                AND COLUMN_NAME = 'url'
            """, (settings.DB_NAME,))

            result = cursor.fetchone()
            if result[0] > 0:
                print("Column 'url' already exists in documents table.")
                return

            # 添加 url 字段
            cursor.execute("""
                ALTER TABLE documents
                ADD COLUMN url VARCHAR(500) NULL COMMENT '文件存储路径'
                AFTER chunk_count
            """)

            conn.commit()
            print("Successfully added 'url' column to documents table.")

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
