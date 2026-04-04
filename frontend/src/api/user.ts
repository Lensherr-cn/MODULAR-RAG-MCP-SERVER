// 用户相关 API
import { get, post, del } from './index'

export interface UserProfile {
  id: string
  username: string
  department?: string
  email?: string
  avatar?: string
  created_at: string
}

export interface QueryHistory {
  id: string
  query: string
  created_at: string
  conversation_id?: string
}

export interface Feedback {
  id: string
  content: string
  type: 'positive' | 'negative' | 'suggestion'
  created_at: string
}

// 获取用户信息
export function getUserProfileApi() {
  return get<UserProfile>('/v1/user/profile')
}

// 获取查询历史
export function getQueryHistoryApi(params?: { limit?: number }) {
  return get<QueryHistory[]>('/v1/user/history', { params })
}

// 提交反馈
export interface FeedbackRequest {
  content: string
  type: 'positive' | 'negative' | 'suggestion'
  query_id?: string
}

export function submitFeedbackApi(data: FeedbackRequest) {
  return post('/v1/feedback', data)
}

// 获取反馈列表
export function getFeedbacksApi() {
  return get<Feedback[]>('/v1/feedback')
}
