"""
Authentication API
认证相关接口 - 登录、登出、刷新 Token、获取当前用户
"""
import uuid
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    verify_password, get_password_hash, create_access_token, decode_token,
    blacklist_token, check_login_attempts, record_login_attempt
)
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()


# ============= Schemas =============

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    rememberMe: Optional[bool] = Field(default=False, description="记住我（延长 Refresh Token 有效期）")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    email: str = Field(..., max_length=100, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="邮箱")
    department: str = Field(..., min_length=1, max_length=100, description="部门")
    password: str = Field(..., min_length=6, description="密码")
    role: Optional[str] = Field(default="user", pattern=r"^(user|admin|leader)$", description="角色：user/admin/leader")
    permissionCode: Optional[str] = Field(default=None, description="权限标识码（admin/leader 必填）")


class RegisterResponse(BaseModel):
    """注册响应"""
    id: str
    username: str
    email: Optional[str] = None
    department: Optional[str] = None
    role: str


class LoginResponse(BaseModel):
    """登录响应"""
    user: dict


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: Optional[str] = None
    department: Optional[str] = None
    role: str
    avatar: Optional[str] = None
    created_at: Optional[str] = None


class RefreshResponse(BaseModel):
    """刷新 Token 响应"""
    message: str


class LogoutResponse(BaseModel):
    """登出响应"""
    message: str


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str


# ============= Helper Functions =============

def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_expire: int,
    refresh_expire: int
):
    """
    设置认证相关的 httpOnly Cookie
    """
    # Access Token Cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,  # 生产环境必须为 True
        samesite="lax",  # 使用 lax 以支持一定程度的跨站请求
        max_age=access_expire,
        path="/"
    )

    # Refresh Token Cookie（仅限刷新接口）
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=refresh_expire,
        path="/api/v1/auth/refresh"  # 仅限刷新接口使用
    )


def clear_auth_cookies(response: Response):
    """
    清除认证相关的 Cookie
    """
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")


# ============= API Endpoints =============

@router.post(
    "/register",
    response_model=dict,
    summary="用户注册",
    description="注册新用户，普通用户直接注册；管理员/领导需提供权限标识码"
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册接口

    - 校验用户名唯一性
    - admin/leader 角色需校验 permissionCode（后续可替换为更严格的逻辑）
    - 密码 bcrypt 哈希后入库
    """
    # 清理输入
    username = request.username.strip()
    email = request.email.strip()
    department = request.department.strip()
    permission_code = request.permissionCode.strip() if request.permissionCode else None

    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # 权限角色校验（TODO: 后续补充更严格的权限标识校验逻辑）
    role = (request.role or "user").lower()
    if role in ("admin", "leader"):
        if not permission_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission code is required for admin/leader registration"
            )
        # 占位校验：当前仅要求非空，后续可对接配置中心或数据库白名单

    # 创建用户
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        department=department,
        password_hash=get_password_hash(request.password),
        role=role,
        is_active="Y"
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to database error"
        )

    return {
        "code": 200,
        "message": "Registration successful",
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "department": user.department,
            "role": user.role,
        }
    }


@router.post(
    "/login",
    response_model=dict,
    summary="用户登录",
    description="使用用户名和密码登录，成功后在 httpOnly Cookie 中设置 Token"
)
async def login(
    response: Response,
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录接口

    - 验证用户名和密码
    - 生成双 Token（Access + Refresh）
    - 设置 httpOnly Cookie
    - 登录失败次数限制：5次/5分钟，超限锁定15分钟
    """
    # 检查登录尝试次数
    allowed, error_msg = check_login_attempts(request.username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        )

    # 查询用户
    user = db.query(User).filter(User.username == request.username).first()

    # 验证用户存在、密码正确、账号启用
    if not user or not user.password_hash:
        record_login_attempt(request.username, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not verify_password(request.password, user.password_hash):
        record_login_attempt(request.username, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if user.is_active != "Y":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # 登录成功，清除失败记录
    record_login_attempt(request.username, success=True)

    # 生成 Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role or "user",
            "department": user.department,
        },
        expires_delta=access_token_expires,
        token_type="access"
    )

    # 生成 Refresh Token
    refresh_expire_days = 30 if request.rememberMe else 7
    refresh_token_expires = timedelta(days=refresh_expire_days)
    refresh_token = create_access_token(
        data={"sub": user.id},
        expires_delta=refresh_token_expires,
        token_type="refresh"
    )

    # 设置 Cookie
    set_auth_cookies(
        response,
        access_token,
        refresh_token,
        int(access_token_expires.total_seconds()),
        int(refresh_token_expires.total_seconds())
    )

    return {
        "code": 200,
        "message": "Login successful",
        "data": {
            "user": {
                "id": user.id,
                "username": user.username,
                "department": user.department,
                "role": user.role,
                "avatar": user.avatar,
            }
        }
    }


@router.post(
    "/logout",
    response_model=dict,
    summary="用户登出",
    description="清除 Cookie 并将 Access Token 加入黑名单"
)
async def logout(
    response: Response,
    request: Request
):
    """
    用户登出接口

    - 将 Access Token 加入黑名单（使其立即失效）
    - 清除所有认证 Cookie
    """
    # 获取 Access Token 并加入黑名单
    access_token = request.cookies.get("access_token")
    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("jti"):
            await blacklist_token(payload["jti"], payload.get("exp", 0))

    # 清除 Cookie
    clear_auth_cookies(response)

    return {
        "code": 200,
        "message": "Logout successful",
        "data": {"message": "Logged out successfully"}
    }


@router.post(
    "/refresh",
    response_model=dict,
    summary="刷新 Access Token",
    description="使用 Refresh Token 获取新的 Access Token"
)
async def refresh_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    刷新 Access Token 接口

    - 从 httpOnly Cookie 中读取 Refresh Token
    - 验证 Refresh Token 有效性
    - 生成新的 Access Token 并更新 Cookie
    """
    # 从 Cookie 读取 Refresh Token
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    # 解码 Refresh Token
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # 验证 token 类型
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # 获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_active != "Y":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # 生成新的 Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role or "user",
            "department": user.department,
        },
        expires_delta=access_token_expires,
        token_type="access"
    )

    # 更新 Access Token Cookie
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=int(access_token_expires.total_seconds()),
        path="/"
    )

    return {
        "code": 200,
        "message": "Token refreshed successfully",
        "data": {"message": "Token refreshed"}
    }


@router.get(
    "/me",
    response_model=dict,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息"
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    """
    return {
        "code": 200,
        "message": "Success",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "department": current_user.department,
            "role": current_user.role,
            "avatar": current_user.avatar,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        }
    }


@router.get(
    "/check",
    response_model=dict,
    summary="检查登录状态",
    description="检查当前用户是否已登录（用于前端初始化）"
)
async def check_auth(current_user: User = Depends(get_current_user)):
    """
    检查认证状态
    """
    return {
        "code": 200,
        "message": "Authenticated",
        "data": {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "role": current_user.role,
            }
        }
    }
