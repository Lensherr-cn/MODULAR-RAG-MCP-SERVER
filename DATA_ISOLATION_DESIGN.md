# 企业知识库数据隔离方案设计

## 1. 概述

### 1.1 目标
实现基于用户的数据隔离，确保：
- 用户只能访问自己有权限的文档
- 用户数据（收藏、历史记录等）相互隔离
- 支持多级权限：公共 / 部门级 / 私有

### 1.2 当前状态
- ✅ 已完成 MySQL 持久化
- ✅ 数据表已预留隔离字段（owner_id, visibility, department）
- ⚠️ 用户认证为硬编码（user_001）
- ⚠️ API 未接入用户认证

### 1.3 方案范围
本方案涵盖：用户认证、权限中间件、服务端数据隔离、前端适配

---

## 2. 数据模型设计

### 2.1 用户表 (users)
```sql
- id: VARCHAR(36) PK - 用户UUID
- username: VARCHAR(50) UNIQUE - 用户名
- email: VARCHAR(100) - 邮箱
- department: VARCHAR(100) - 所属部门
- password_hash: VARCHAR(255) - 密码哈希
- role: VARCHAR(20) - 角色: admin/user/guest
- is_active: VARCHAR(1) - 是否启用
- created_at/updated_at: DATETIME
```

**新增字段说明：**
- `role`: 区分管理员和普通用户，管理员可查看所有文档
- `department`: 用于部门级数据隔离

### 2.2 文档表 (documents)
```sql
- id: VARCHAR(36) PK
- name/category/file_type/file_size - 基础信息
- owner_id: VARCHAR(36) FK - 所有者ID，NULL表示系统文档
- visibility: VARCHAR(20) - 可见性级别
- department: VARCHAR(100) - 所属部门（部门级可见用）
```

**可见性级别 (visibility)：**
| 级别 | 说明 | 访问规则 |
|-----|------|---------|
| public | 公共文档 | 所有用户可访问 |
| department | 部门文档 | 同部门用户可访问 |
| private | 私有文档 | 仅所有者可访问 |

### 2.3 其他用户数据表
- `favorites` - 收藏：已通过 user_id 关联用户
- `query_history` - 查询历史：已通过 user_id 关联用户
- `conversations` - 对话：已通过 user_id 关联用户
- `feedbacks` - 反馈：已通过 user_id 关联用户

---

## 3. 认证机制设计

### 3.1 JWT Token 方案

**Token 结构（Access Token）：**
```json
{
  "sub": "user_uuid",
  "username": "zhangsan",
  "role": "user",
  "department": "技术部",
  "jti": "unique-token-id",
  "type": "access",
  "iat": 1714531200,
  "exp": 1715136000
}
```

**双 Token 机制：**
| Token 类型 | 有效期 | 用途 | 存储位置 |
|-----------|-------|------|---------|
| Access Token | 15分钟 | API 访问 | httpOnly Cookie |
| Refresh Token | 7天 | 刷新 Access Token | httpOnly Cookie (path=/api/v1/auth/refresh) |

**API 端点：**
```
POST /api/v1/auth/login          - 登录，设置 httpOnly Cookie
POST /api/v1/auth/logout         - 登出，清除 Cookie，加入黑名单
POST /api/v1/auth/refresh        - 刷新 Access Token
GET  /api/v1/auth/me             - 获取当前用户信息
```

**安全传输：**
- 生产环境强制 HTTPS
- Cookie 设置 `Secure`, `SameSite=Strict`
- CSRF Token 用于敏感操作（可选）

### 3.2 密码安全
- **哈希算法**：bcrypt，cost factor = 12
- **密码复杂度要求**：
  - 最小长度：8位
  - 必须包含：大写字母、小写字母、数字
  - 可选：特殊字符
- **登录失败限制**：
  - 5次/分钟，超限锁定15分钟
  - 使用 Redis 或内存缓存记录失败次数
- **密码历史**：禁止重复使用最近3次密码（可选）

### 3.3 Token 黑名单（登出失效）
```python
# 使用 Redis 存储黑名单（内存字典仅适合开发）
# Key: jti (JWT ID), Value: 过期时间戳
# TTL 设置为 token 剩余有效期

REDIS_BLACKLIST_KEY = "jwt:blacklist:{jti}"

async def is_token_blacklisted(jti: str) -> bool:
    return await redis.exists(f"jwt:blacklist:{jti}")

async def blacklist_token(jti: str, exp: int):
    ttl = exp - int(time.time())
    if ttl > 0:
        await redis.setex(f"jwt:blacklist:{jti}", ttl, "1")
```

### 3.4 Token 配置
```python
# 安全：缩短 Access Token 有效期，使用 Refresh Token 续期
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15分钟
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 会话限制
MAX_SESSIONS_PER_USER = 5  # 单用户最大并发登录数
```

---

## 4. 权限控制设计

### 4.1 依赖注入函数
```python
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    从 httpOnly Cookie 中读取并验证 JWT
    """
    # 从 Cookie 读取 token（比 localStorage 更安全）
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    
    # 解析并验证 token
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(401, "Invalid token")
    
    # 检查黑名单
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(401, "Token has been revoked")
    
    # 查询用户
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(401, "User not found")
    if user.is_active != "Y":
        raise HTTPException(403, "User is inactive")
    
    # 将用户信息附加到 request，供后续使用
    request.state.user = user
    request.state.user_role = payload.get("role")
    request.state.user_department = payload.get("department")
    
    return user

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if user.role != "admin":
        raise HTTPException(403, "Admin permission required")
    return user
```

### 4.2 文档访问权限检查
```python
def can_access_document(document: Document, user: User) -> bool:
    """
    检查用户是否有权限访问文档
    安全原则：默认拒绝，明确允许
    """
    # 参数校验
    if not document or not user:
        return False
    
    # 管理员可以访问所有
    if user.role == "admin":
        return True
    
    visibility = document.visibility or "public"  # 默认公共
    
    # 公共文档：所有人可访问
    if visibility == "public":
        return True
    
    # 私有文档：仅所有者可访问
    if visibility == "private":
        # 文档必须有所有者才能设为私有
        if not document.owner_id:
            return False
        return document.owner_id == user.id
    
    # 部门文档：同部门用户可访问
    if visibility == "department":
        # 检查文档和用户是否都有部门信息
        if not document.department or not user.department:
            return False
        return document.department == user.department
    
    # 未知可见性级别：默认拒绝
    return False
```

### 4.3 数据库查询过滤器
```python
from sqlalchemy import or_, and_

def get_document_query_filter(user: User):
    """
    生成文档查询的 SQLAlchemy 过滤条件
    注意：必须返回有效的 SQLAlchemy 表达式，不能返回 True
    """
    if user.role == "admin":
        # 管理员不过滤，返回恒真条件
        return Document.id.isnot(None)  # 或使用 1==1 的等效 SQL
    
    # 构建权限过滤条件
    conditions = [Document.visibility == "public"]  # 公共文档
    
    # 用户的私有文档
    conditions.append(Document.owner_id == user.id)
    
    # 同部门文档（仅当用户有所属部门时）
    if user.department:
        conditions.append(
            and_(
                Document.visibility == "department",
                Document.department == user.department
            )
        )
    
    return or_(*conditions)

# 使用示例
def list_documents(db: Session, user: User, **filters):
    query = db.query(Document).filter(get_document_query_filter(user))
    
    # 应用其他过滤条件
    if filters.get("category"):
        query = query.filter(Document.category == filters["category"])
    
    return query.all()
```

---

## 5. API 改造方案

### 5.1 新增认证模块
```python
# backend/app/api/v1/auth.py
@router.post("/login")
async def login(credentials: LoginRequest):
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    token = create_access_token({
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "department": user.department
    })
    return {"token": token, "user": user}
```

### 4.4 权限装饰器（简化权限控制）
```python
from functools import wraps
from fastapi import HTTPException

def require_permission(visibility: str = None):
    """
    权限检查装饰器
    visibility: 要求的可见性级别（None 表示只要求登录）
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if visibility == "admin" and current_user.role != "admin":
                raise HTTPException(403, "Admin permission required")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.post("/admin-only")
@require_permission("admin")
async def admin_endpoint(current_user: User = Depends(get_current_user)):
    pass
```

---

## 5. API 改造方案

### 5.2 改造现有 API

**文档相关 API：**
```python
# GET /api/v1/documents
async def list_documents(
    current_user: User = Depends(get_current_user),
    category: str = Query(None),
    file_type: str = Query(None)
):
    # 自动过滤用户有权限的文档
    return document_service.list_documents(
        user_id=current_user.id,
        category=category,
        file_type=file_type
    )

# GET /api/v1/documents/{doc_id}
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    doc = document_service.get_document(doc_id, user_id=current_user.id)
    if not doc:
        raise HTTPException(404, "Document not found or no permission")
    return doc

# POST /api/v1/documents/upload
async def upload_document(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    visibility: str = Form("public")  # 新增参数
):
    # 文档归属当前用户
    return document_service.create_document(
        doc_data={...},
        user_id=current_user.id,
        visibility=visibility
    )
```

**用户相关 API：**
```python
# GET /api/v1/user/profile
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

# GET /api/v1/user/history
async def get_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20)
):
    return user_service.get_query_history(
        user_id=current_user.id,  # 使用当前用户ID
        limit=limit
    )
```

### 5.3 新增用户管理 API（管理员）
```python
# GET /api/v1/admin/users - 用户列表（分页、搜索、筛选）
# POST /api/v1/admin/users - 创建用户
# PUT /api/v1/admin/users/{id} - 更新用户信息
# PUT /api/v1/admin/users/{id}/status - 启用/禁用用户（推荐替代删除）
# DELETE /api/v1/admin/users/{id} - 删除用户（谨慎操作）
```

**用户删除策略：**
| 策略 | 处理方式 | 适用场景 |
|-----|---------|---------|
| 软删除（推荐） | `is_active = 'N'` | 用户离职，保留历史数据 |
| 硬删除 | 删除用户记录，文档转给系统账号 | 彻底清除用户数据 |
| 数据转移 | 将文档转给指定用户后删除 | 工作交接场景 |

```python
async def delete_user(user_id: str, strategy: str = "deactivate"):
    """
    删除用户的三种策略
    """
    if strategy == "deactivate":
        # 软删除：禁用用户，保留所有数据
        user.is_active = "N"
        db.commit()
    
    elif strategy == "transfer":
        # 转移文档后删除
        system_user_id = get_system_user_id()
        db.query(Document).filter(Document.owner_id == user_id).update({
            "owner_id": system_user_id,
            "visibility": "public"  # 或保持原可见性
        })
        db.delete(user)
        db.commit()
    
    elif strategy == "hard_delete":
        # 硬删除：级联删除所有关联数据
        # 注意：外键已设置 ON DELETE CASCADE
        db.delete(user)
        db.commit()
```

---

## 6. 前端适配方案

### 6.1 登录页面
- 路径：`/login`
- 功能：用户名/密码输入、Token 存储、登录状态管理

### 6.2 请求配置
```typescript
// api/index.ts
// 重要：使用 withCredentials 让浏览器自动携带 httpOnly Cookie
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  withCredentials: true,  // 关键：允许跨域携带 Cookie
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器：处理 401 未授权
request.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        // 尝试刷新 token
        await authApi.refresh()
        // 刷新成功，重试原请求
        return request(originalRequest)
      } catch (refreshError) {
        // 刷新失败，跳转登录页
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)
```

### 6.3 路由守卫
```typescript
// router/index.ts
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const isLoggedIn = !!token
  
  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})
```

### 6.4 文档上传组件改造
- 新增可见性选择：公共 / 部门 / 私有
- 默认选中"公共"

---

## 7. 服务端实现步骤

### 7.1 第一阶段：认证基础设施
1. 安装依赖：`pip install pyjwt bcrypt`
2. 创建 `app/core/security.py`：
   - `verify_password()` - 密码验证
   - `get_password_hash()` - 密码哈希
   - `create_access_token()` - 生成 JWT
   - `decode_token()` - 解析 JWT
3. 创建 `app/core/auth.py`：
   - `get_current_user()` - 依赖注入函数
4. 创建 `app/api/v1/auth.py` - 登录接口

### 7.2 第二阶段：改造现有 API
1. 修改 `documents.py`：
   - 所有接口接入 `current_user`
   - 使用数据隔离过滤器
2. 修改 `user.py`：
   - 使用 `current_user.id` 替代硬编码
3. 修改 `chat.py`、`feedback.py` 等

### 7.3 第三阶段：权限增强
1. 实现管理员角色检查
2. 实现文档权限检查中间件
3. 添加操作日志记录

---

## 8. 前端实现步骤

### 8.1 第一阶段：登录功能
1. 创建 `views/LoginView.vue`
2. 添加登录 API：`api/auth.ts`
3. 完善 `stores/user.ts`：
   - 实现 `login()` 方法
   - 实现 `fetchUserInfo()` 方法

### 8.2 第二阶段：请求适配
1. 完善 API 拦截器
2. 处理 401 错误

### 8.3 第三阶段：UI 适配
1. 文档上传添加可见性选择
2. 个人中心显示用户部门信息
3. 管理员后台（可选）

---

## 9. 测试验证清单

### 9.1 认证测试
- [ ] 用户能正常登录并获取 token
- [ ] Token 过期后自动跳转到登录页
- [ ] 密码错误返回 401

### 9.2 数据隔离测试
- [ ] 用户 A 看不到用户 B 的私有文档
- [ ] 同部门用户能看到部门级文档
- [ ] 所有用户都能看到公共文档
- [ ] 用户只能看到自己的收藏/历史记录

### 9.3 权限测试
- [ ] 管理员能看到所有文档
- [ ] 普通用户不能访问管理接口
- [ ] 用户不能修改其他用户的数据

---

## 10. 安全注意事项

### 10.1 Cookie 安全
- **httpOnly**: true - 禁止 JavaScript 访问，防 XSS
- **Secure**: true - 仅 HTTPS 传输
- **SameSite**: Strict - 防止 CSRF
- **Max-Age**: 与 token 有效期一致

### 10.2 CORS 配置
```python
# 允许的域名必须明确指定，不能通配符
cors_origins = [
    "https://your-domain.com",
    "https://app.your-domain.com"
]
# 允许携带 Cookie
allow_credentials = True
```

### 10.3 其他安全措施
1. **HTTPS 强制**：生产环境必须使用 HTTPS，HSTS 头部
2. **Token 安全**：JWT secret 使用强随机字符串（256位以上）
3. **密码策略**：bcrypt cost=12，最小8位，需包含大小写+数字
4. **SQL 注入**：SQLAlchemy ORM 已防护，禁止原始 SQL 拼接
5. **XSS 防护**：输出转义，Content-Security-Policy 头部
6. **Rate Limiting**：登录接口限速 5次/分钟，API 100次/分钟
7. **审计日志**：记录所有敏感操作（登录、权限变更、删除）

---

## 11. 扩展规划

### 11.1 角色权限扩展
```python
roles_permissions = {
    "admin": ["*"],  # 所有权限
    "manager": ["read_all", "write_department"],
    "user": ["read_public", "write_own"],
    "guest": ["read_public"]
}
```

### 11.2 细粒度权限
- 文档级别的用户白名单
- 操作审计日志
- 数据导出权限控制

---

## 12. 参考代码片段

### 12.1 完整登录接口实现（使用 httpOnly Cookie）
```python
# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from pydantic import BaseModel
from datetime import timedelta

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(
    response: Response,
    request: LoginRequest
):
    from app.services.user_service import user_service
    from app.core.security import verify_password, create_access_token
    from app.core.config import settings
    
    # 验证用户
    user = user_service.get_user_by_username(request.username)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")
    
    # 生成双 token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "department": user.department,
            "type": "access"
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_access_token(
        data={
            "sub": user.id,
            "type": "refresh"
        },
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    # 设置 httpOnly Cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # 生产环境必须为 True
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/v1/auth/refresh",  # 仅限刷新接口使用
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "department": user.department,
            "role": user.role
        }
    }

@router.post("/logout")
async def logout(response: Response, request: Request):
    """登出：清除 Cookie 并将 token 加入黑名单"""
    from app.core.security import decode_token, blacklist_token
    
    # 获取 token 并加入黑名单
    access_token = request.cookies.get("access_token")
    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("jti"):
            await blacklist_token(payload["jti"], payload["exp"])
    
    # 清除 Cookie
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
    
    return {"message": "Logged out successfully"}
```

### 12.2 当前用户依赖（使用 Cookie + 依赖注入）
```python
# app/core/auth.py
from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# 可选：用于文档显示的 scheme
cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    从 httpOnly Cookie 中读取并验证 JWT
    使用依赖注入管理数据库会话
    """
    # 从 Cookie 读取 token
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 验证 token 类型
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        
        # 检查黑名单（如果使用 Redis）
        jti = payload.get("jti")
        if jti and await is_token_blacklisted(jti):
            raise HTTPException(401, "Token has been revoked")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
            
    except JWTError:
        raise HTTPException(401, "Invalid token")
    
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "User not found")
    if user.is_active != "Y":
        raise HTTPException(403, "User is inactive")
    
    # 将用户信息附加到 request.state
    request.state.user = user
    
    return user

# 管理员权限依赖
async def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Admin permission required")
    return user
```

---

## 附录：设计缺陷修正记录

### 修正 1：Token 存储安全（严重）
**原设计**：使用 localStorage 存储 JWT，通过 Header 发送
**问题**：XSS 攻击可导致 Token 泄露
**修正**：使用 httpOnly Cookie，浏览器自动携带，JS 不可访问

### 修正 2：权限检查边界（严重）
**原设计**：未处理 null 值，缺少默认拒绝
**问题**：空指针异常或意外授权
**修正**：所有检查函数添加参数校验，遵循"默认拒绝"原则

### 修正 3：SQL 查询过滤器（严重）
**原设计**：`return True` 给管理员
**问题**：SQLAlchemy 会错误解析为恒真条件
**修正**：返回 `Document.id.isnot(None)` 作为恒真条件

### 修正 4：数据库连接管理（中等）
**原设计**：手动创建 SessionLocal
**问题**：连接泄漏，不符合 FastAPI 依赖注入规范
**修正**：使用 `Depends(get_db)` 标准模式

### 修正 5：Token 黑名单（中等）
**原设计**：登出仅清除客户端存储
**问题**：Token 在过期前仍有效
**修正**：增加 Redis 黑名单，或使用短期 Access Token + Refresh Token

### 修正 6：会话并发控制（中等）
**原设计**：未限制单用户登录数
**问题**：用户可在多处无限登录
**修正**：增加 MAX_SESSIONS_PER_USER = 5 限制

### 修正 7：用户删除策略（中等）
**原设计**：简单的 DELETE 接口
**问题**：用户删除后文档归属不明
**修正**：提供软删除、数据转移、硬删除三种策略

### 修正 8：CORS 安全配置（中等）
**原设计**：未明确 CORS 配置
**问题**：可能配置不当导致安全隐患
**修正**：明确指定允许的域名，启用 withCredentials

---

**文档版本**: v1.1  
**创建日期**: 2026-04-02  
**最后修正**: 2026-04-02  
**作者**: Claude Code
