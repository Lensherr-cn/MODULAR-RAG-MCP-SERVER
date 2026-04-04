// 统计相关 API
import { get } from './index'

export interface CategoryStat {
  name: string
  count: number
}

export interface OverviewStats {
  document_count: number
  chunk_count: number
  today_queries: number
  total_queries: number
  active_users: number
  categories: CategoryStat[]
}

export interface HotQuestion {
  id: string
  question: string
  count: number
}

// 获取首页统计数据
export function getOverviewStatsApi() {
  return get<OverviewStats>('/v1/stats/overview')
}

// 获取热门问题
export function getHotQuestionsApi(limit?: number) {
  return get<HotQuestion[]>('/v1/stats/hot-questions', {
    params: { limit },
  })
}
