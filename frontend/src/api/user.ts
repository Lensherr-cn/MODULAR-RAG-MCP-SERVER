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

export interface Favorite {
  id: string
  document_id: string
  document_name: string
  created_at: string
}

export interface Feedback {
  id: string
  content: string
  type: 'positive' | 'negative' | 'suggestion'
  created_at: string
}

// 获取用户信息
export function getUserProfileApi() {
  return get<UserProfile>('/user/profile')
}

// 获取查询历史
export function getQueryHistoryApi(params?: { limit?: number }) {
  return get<QueryHistory[]>('/user/history', { params })
}

// 获取收藏列表
export function getFavoritesApi() {
  return get<Favorite[]>('/user/favorites')
}

// 添加/取消收藏
export function toggleFavoriteApi(documentId: string) {
  return post(`/user/favorites/${documentId}`)
}

// 删除收藏
export function deleteFavoriteApi(id: string) {
  return del(`/user/favorites/${id}`)
}

// 提交反馈
export interface FeedbackRequest {
  content: string
  type: 'positive' | 'negative' | 'suggestion'
  query_id?: string
}

export function submitFeedbackApi(data: FeedbackRequest) {
  return post('/feedback', data)
}

// 获取反馈列表
export function getFeedbacksApi() {
  return get<Feedback[]>('/feedback')
}
