// 搜索相关 API
import { get } from './index'

export interface SearchResult {
  id: string
  title: string
  type: 'document' | 'chunk' | 'question'
  content?: string
  score?: number
  metadata?: Record<string, any>
}

export interface SearchResponse {
  total: number
  items: SearchResult[]
}

// 全局搜索
export function searchApi(keyword: string, params?: { type?: string; limit?: number }) {
  return get<SearchResponse>('/v1/search', {
    params: {
      keyword,
      ...params,
    },
  })
}
