// 文档相关 API
import { get, post, del } from './index'

export interface Document {
  id: string
  name: string
  category: string
  file_type: string
  file_size: number
  chunk_count: number
  url?: string
  visibility?: 'public' | 'department' | 'private'
  created_at: string
  updated_at: string
}

export interface DocumentListResponse {
  total: number
  page: number
  page_size: number
  items: Document[]
}

export interface DocumentDetail extends Document {
  content?: string
  chunks?: Chunk[]
}

export interface Chunk {
  id: string
  content: string
  page?: number
  metadata?: Record<string, any>
}

export interface Category {
  name: string
  count: number
}

// 获取文档列表
export function getDocumentsApi(params?: {
  page?: number
  page_size?: number
  category?: string
  keyword?: string
  file_type?: string
}) {
  return get<DocumentListResponse>('/v1/documents', { params })
}

// 获取文档详情
export function getDocumentDetailApi(id: string) {
  return get<DocumentDetail>(`/v1/documents/${id}`)
}

// 上传文档
export function uploadDocumentApi(formData: FormData) {
  return post<{ id: string }>('/v1/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

// 删除文档
export function deleteDocumentApi(id: string) {
  return del(`/v1/documents/${id}`)
}

// 下载文档
export function downloadDocumentApi(id: string): string {
  return `/api/v1/documents/${id}/download`
}

// 获取分类列表
export function getCategoriesApi() {
  return get<{ categories: Category[] }>('/v1/documents/categories/all')
}

// 切换收藏状态
export function toggleFavoriteApi(documentId: string) {
  return post<{ is_favorite: boolean }>(`/v1/documents/${documentId}/favorite`)
}

// 获取收藏状态
export function getFavoriteStatusApi(documentId: string) {
  return get<{ is_favorite: boolean }>(`/v1/documents/${documentId}/favorite/status`)
}

// 获取收藏列表
export function getFavoritesApi(params?: { page?: number; page_size?: number }) {
  return get<DocumentListResponse>('/v1/documents/favorites/my', { params })
}

// 获取收藏数量
export function getFavoriteCountApi() {
  return get<{ count: number }>('/v1/documents/favorites/count')
}

// 解析文档
export function parseDocumentApi(documentId: string) {
  return post<{ doc_id: string; status: string; message: string }>(`/v1/documents/${documentId}/parse`)
}
