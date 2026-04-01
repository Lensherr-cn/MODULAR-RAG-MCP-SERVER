#!/usr/bin/env python3
"""
Database Initialization Script
数据库初始化脚本 - 创建数据库、表结构和初始数据
"""
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))  # 添加到backend目录
sys.path.insert(0, str(PROJECT_ROOT.parent))  # 添加到父目录，以backend为根

import pymysql
from app.core.config import settings
from app.core.database import init_db, engine, Base
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid


def create_database():
    """创建数据库（如果不存在）"""
    print(f"Connecting to MySQL at {settings.DB_HOST}:{settings.DB_PORT}...")

    # 连接到MySQL服务器（不指定数据库）
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        charset='utf8mb4'
    )

    try:
        with conn.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME} "
                          f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"Database '{settings.DB_NAME}' created or already exists.")

            # 创建用户并授权（如果需要）
            # cursor.execute(f"GRANT ALL PRIVILEGES ON {settings.DB_NAME}.* TO '{settings.DB_USER}'@'%'")

        conn.commit()
    finally:
        conn.close()


def init_categories(db: Session):
    """初始化预定义分类"""
    from app.models.document import Category

    categories = [
        {"name": "产品文档", "description": "产品相关的文档和手册", "sort_order": 1},
        {"name": "技术文档", "description": "技术架构和设计文档", "sort_order": 2},
        {"name": "规章制度", "description": "公司规章制度文件", "sort_order": 3},
        {"name": "培训资料", "description": "员工培训相关材料", "sort_order": 4},
        {"name": "流程规范", "description": "业务流程和操作规范", "sort_order": 5},
        {"name": "其他", "description": "其他类型文档", "sort_order": 99},
    ]

    for cat_data in categories:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not existing:
            category = Category(
                id=str(uuid.uuid4()),
                **cat_data
            )
            db.add(category)
            print(f"Created category: {cat_data['name']}")

    db.commit()


def init_default_user(db: Session):
    """初始化默认用户（用于数据迁移）"""
    from app.models.user import User

    default_user = db.query(User).filter(User.username == "admin").first()
    if not default_user:
        user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@company.com",
            department="系统管理部",
            is_active="Y"
        )
        db.add(user)
        db.commit()
        print("Created default user: admin")
        return user.id
    return default_user.id


def main():
    print("=" * 50)
    print("Knowledge Hub Database Initialization")
    print("=" * 50)

    # 步骤1: 创建数据库
    create_database()

    # 步骤2: 创建表结构
    print("\nCreating tables...")
    init_db()
    print("Tables created successfully!")

    # 步骤3: 初始化基础数据
    print("\nInitializing base data...")
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        init_categories(db)
        user_id = init_default_user(db)
        print(f"\nDefault user ID: {user_id}")
    finally:
        db.close()

    print("\n" + "=" * 50)
    print("Database initialization completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
