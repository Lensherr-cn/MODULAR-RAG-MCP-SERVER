"""
Database Connection Management
数据库连接管理 - 使用SQLAlchemy 2.0
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 自动检测断开的连接
    echo=settings.DEBUG  # 调试模式下输出SQL
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明式基类
Base = declarative_base()


def get_db() -> Session:
    """
    获取数据库会话 - 用于FastAPI依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    上下文管理器方式获取数据库会话
    用于非FastAPI上下文（如后台任务）
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    初始化数据库 - 创建所有表
    """
    # 导入所有模型以确保它们被注册到Base
    import app.models.user
    import app.models.document
    import app.models.chat

    Base.metadata.create_all(bind=engine)
