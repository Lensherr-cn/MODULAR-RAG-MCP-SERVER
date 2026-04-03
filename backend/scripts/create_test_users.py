"""
创建测试用户脚本
用于开发和测试阶段初始化用户数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uuid
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.document import Document  # 需要导入以建立关系
from app.models.chat import Conversation, ChatMessage  # 需要导入以建立关系
from app.core.security import get_password_hash


def create_test_users():
    """创建测试用户"""
    db = SessionLocal()

    try:
        # 检查是否已有用户
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"已有 {existing_users} 个用户存在，跳过创建")
            return

        # 定义测试用户
        test_users = [
            {
                "id": str(uuid.uuid4()),
                "username": "admin",
                "email": "admin@company.com",
                "department": "技术部",
                "role": "admin",
                "password": "Admin123!",
                "is_active": "Y"
            },
            {
                "id": str(uuid.uuid4()),
                "username": "zhangsan",
                "email": "zhangsan@company.com",
                "department": "技术部",
                "role": "user",
                "password": "User123!",
                "is_active": "Y"
            },
            {
                "id": str(uuid.uuid4()),
                "username": "lisi",
                "email": "lisi@company.com",
                "department": "产品部",
                "role": "user",
                "password": "User123!",
                "is_active": "Y"
            },
            {
                "id": str(uuid.uuid4()),
                "username": "wangwu",
                "email": "wangwu@company.com",
                "department": "人事部",
                "role": "user",
                "password": "User123!",
                "is_active": "Y"
            }
        ]

        print("=" * 50)
        print("Creating test users...")
        print("=" * 50)

        for user_data in test_users:
            # 创建用户
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data["email"],
                department=user_data["department"],
                role=user_data["role"],
                password_hash=get_password_hash(user_data["password"]),
                is_active=user_data["is_active"]
            )

            db.add(user)

            print(f"\nUsername: {user_data['username']}")
            print(f"Password: {user_data['password']}")
            print(f"Role: {user_data['role']}")
            print(f"Department: {user_data['department']}")

        db.commit()

        print("\n" + "=" * 50)
        print(f"Successfully created {len(test_users)} test users!")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"Error creating test users: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
