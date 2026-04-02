import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

// 响应数据接口
export interface ApiResponse<T = any> {
  code?: number
  data: T
  message?: string
}

// 创建 Axios 实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  withCredentials: true, // 关键：允许跨域携带 httpOnly Cookie
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // Token 通过 httpOnly Cookie 自动携带，不需要手动设置
    // 保留此拦截器用于未来扩展（如添加 CSRF Token）
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    return response
  },
  (error) => {
    console.error('Request error:', error)
    if (error.response) {
      switch (error.response.status) {
        case 401:
          console.error('Unauthorized, please login again')
          // 让路由守卫处理重定向，不在拦截器中跳转
          break
        case 403:
          console.error('Forbidden')
          break
        case 404:
          console.error('Resource not found')
          break
        case 500:
          console.error('Server error')
          break
        default:
          console.error(error.response.data?.message || 'Request failed')
      }
    }
    return Promise.reject(error)
  }
)

// 导出请求方法
export default request

export function get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
  return request.get(url, config)
}

export function post<T = any>(
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<ApiResponse<T>>> {
  return request.post(url, data, config)
}

export function put<T = any>(
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<ApiResponse<T>>> {
  return request.put(url, data, config)
}

export function del<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
  return request.delete(url, config)
}
