#!/usr/bin/env python3
"""
数据库迁移脚本 - 创建 favorites 表
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
    """创建 favorites 表"""
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
            # 检查 favorites 表是否已存在
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = 'favorites'
            """, (settings.DB_NAME,))

            result = cursor.fetchone()
            if result[0] > 0:
                print("Table 'favorites' already exists.")
                return

            # 创建 favorites 表
            cursor.execute("""
                CREATE TABLE favorites (
                    id VARCHAR(36) PRIMARY KEY COMMENT '收藏UUID',
                    user_id VARCHAR(36) NOT NULL COMMENT '用户ID',
                    document_id VARCHAR(36) NOT NULL COMMENT '文档ID',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user_doc_fav (user_id, document_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏表'
            """)

            conn.commit()
            print("Successfully created 'favorites' table.")

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
