// 文档相关 API
import { get, post, del } from './index'

export interface Document {
  id: string
  name: string
  category: string
  file_type: string
  file_size: number
  chunk_count: number
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
  return get<DocumentListResponse>('/documents', { params })
}

// 获取文档详情
export function getDocumentDetailApi(id: string) {
  return get<DocumentDetail>(`/documents/${id}`)
}

// 上传文档
export function uploadDocumentApi(formData: FormData) {
  return post<{ id: string }>('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

// 删除文档
export function deleteDocumentApi(id: string) {
  return del(`/documents/${id}`)
}

// 获取分类列表
export function getCategoriesApi() {
  return get<Category[]>('/categories')
}
