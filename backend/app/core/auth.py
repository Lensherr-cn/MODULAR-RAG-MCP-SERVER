"""
Authentication Dependencies
认证依赖模块 - 获取当前用户、权限检查
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token, is_token_blacklisted
from app.core.config import settings
from app.models.user import User

# Cookie scheme for API documentation
cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    从 httpOnly Cookie 中读取并验证 JWT，获取当前用户

    Args:
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        当前登录的用户对象

    Raises:
        HTTPException: 401 未认证，403 用户被禁用
    """
    # 从 Cookie 读取 token
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 解码并验证 token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 token 类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查黑名单
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否启用
    if user.is_active != "Y":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    # 将用户信息附加到 request.state，供后续使用
    request.state.user = user
    request.state.user_role = payload.get("role", "user")
    request.state.user_department = payload.get("department")

    return user


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User | None:
    """
    获取当前用户（可选，未登录返回 None）

    用于某些不需要强制登录但需要识别用户的接口
    """
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


async def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    """
    要求管理员权限

    Args:
        user: 当前用户

    Returns:
        用户对象

    Raises:
        HTTPException: 403 非管理员
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )
    return user


class PermissionChecker:
    """
    权限检查类

    用法:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(PermissionChecker("admin"))):
            pass
    """

    def __init__(self, *allowed_roles: str):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(self.allowed_roles)}",
            )
        return user
