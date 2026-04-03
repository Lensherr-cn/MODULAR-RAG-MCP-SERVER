"""
Security Utilities
安全工具模块 - 密码哈希、JWT 生成与验证
"""
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        验证是否通过
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        bcrypt 哈希后的密码
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access"
) -> str:
    """
    创建 JWT Token

    Args:
        data: 要编码到 token 中的数据
        expires_delta: 过期时间，默认使用配置中的 ACCESS_TOKEN_EXPIRE_MINUTES
        token_type: token 类型 (access/refresh)

    Returns:
        JWT Token 字符串
    """
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # 添加标准 JWT 字段
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),  # JWT ID，用于黑名单
        "type": token_type
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码并验证 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        解码后的 payload，如果验证失败则返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# WARNING: 内存实现仅适用于单进程开发环境，生产环境必须替换为 Redis
# Token 黑名单存储（内存实现）
_token_blacklist: Dict[str, int] = {}


async def is_token_blacklisted(jti: str) -> bool:
    """
    检查 token 是否在黑名单中

    Args:
        jti: Token 的 JWT ID

    Returns:
        是否在黑名单中
    """
    if jti in _token_blacklist:
        # 检查是否已过期
        exp = _token_blacklist[jti]
        if exp > int(datetime.utcnow().timestamp()):
            return True
        else:
            # 清理过期的黑名单条目
            del _token_blacklist[jti]
    return False


async def blacklist_token(jti: str, exp: int):
    """
    将 token 加入黑名单

    Args:
        jti: Token 的 JWT ID
        exp: Token 的过期时间戳
    """
    _token_blacklist[jti] = exp


# WARNING: 内存实现仅适用于单进程开发环境，生产环境必须替换为 Redis
# 登录失败记录（内存实现）
_login_attempts: Dict[str, list] = {}
MAX_LOGIN_ATTEMPTS = 5  # 5分钟内最多5次尝试
LOCKOUT_MINUTES = 15    # 锁定15分钟


def check_login_attempts(username: str) -> tuple[bool, Optional[str]]:
    """
    检查登录尝试次数

    Args:
        username: 用户名

    Returns:
        (是否允许登录, 错误消息)
    """
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=5)

    # 清理旧的尝试记录
    if username in _login_attempts:
        _login_attempts[username] = [
            t for t in _login_attempts[username]
            if t > window_start
        ]

    attempts = _login_attempts.get(username, [])

    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        lockout_end = max(attempts) + timedelta(minutes=LOCKOUT_MINUTES)
        if now < lockout_end:
            remaining = int((lockout_end - now).total_seconds() / 60)
            return False, f"Account locked. Please try again in {remaining} minutes."

    return True, None


def record_login_attempt(username: str, success: bool = False):
    """
    记录登录尝试

    Args:
        username: 用户名
        success: 是否登录成功
    """
    if success:
        # 登录成功，清除失败记录
        if username in _login_attempts:
            del _login_attempts[username]
    else:
        # 登录失败，记录尝试
        if username not in _login_attempts:
            _login_attempts[username] = []
        _login_attempts[username].append(datetime.utcnow())
