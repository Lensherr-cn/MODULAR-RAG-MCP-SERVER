import request, { type ApiResponse } from './index'
import type { AxiosResponse } from 'axios'

// 登录请求参数
export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
}

// 注册请求参数
export interface RegisterRequest {
  username: string
  email: string
  department: string
  password: string
  role?: 'user' | 'admin' | 'leader'
  permissionCode?: string
}

// 登录响应
export interface LoginResponse {
  user: {
    id: string
    username: string
    department?: string
    role?: string
    avatar?: string
  }
}

// 注册响应
export interface RegisterResponse {
  id: string
  username: string
  email?: string
  department?: string
  role?: string
}

// 用户信息
export interface UserInfo {
  id: string
  username: string
  email?: string
  department?: string
  role?: string
  avatar?: string
  created_at?: string
}

/**
 * 用户认证相关 API
 */
export const authApi = {
  /**
   * 用户登录
   * 使用 httpOnly Cookie，浏览器会自动携带 token
   */
  login(data: LoginRequest): Promise<AxiosResponse<ApiResponse<LoginResponse>>> {
    return request.post('/v1/auth/login', data)
  },

  /**
   * 用户登出
   * 清除 Cookie 并将 token 加入黑名单
   */
  logout() {
    return request.post('/v1/auth/logout')
  },

  /**
   * 刷新 Access Token
   */
  refresh() {
    return request.post('/v1/auth/refresh')
  },

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): Promise<AxiosResponse<ApiResponse<UserInfo>>> {
    return request.get('/v1/auth/me')
  },

  /**
   * 用户注册
   */
  register(data: RegisterRequest): Promise<AxiosResponse<ApiResponse<RegisterResponse>>> {
    return request.post('/v1/auth/register', data)
  }
}
