// 问答相关 API
import { get, post } from './index'

export interface ChatRequest {
  query: string
  collection?: string
  conversation_id?: string
  stream?: boolean
}

export interface ChatSource {
  document_id: string
  document_name: string
  chunk_id: string
  content: string
  page?: number
  score: number
}

export interface ChatResponse {
  answer: string
  sources: ChatSource[]
  related_questions: string[]
  conversation_id: string
}

// 智能问答
export function chatApi(data: ChatRequest) {
  return post<ChatResponse>('/chat', data)
}

// 获取对话历史
export function getChatHistoryApi(conversation_id?: string) {
  return get<ChatResponse[]>(`/chat/history${conversation_id ? `?conversation_id=${conversation_id}` : ''}`)
}

// 流式问答（使用 EventSource）
export function createChatStream(
  data: ChatRequest,
  onMessage: (data: any) => void,
  onError?: (error: any) => void,
  onDone?: () => void
) {
  const token = localStorage.getItem('token')
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  // 移除 baseUrl 末尾的 /v1（如果存在），然后添加 /v1/chat/stream
  const apiBase = baseUrl.endsWith('/v1') ? baseUrl : `${baseUrl}/v1`
  const eventSource = new EventSource(
    `${apiBase}/chat/stream?query=${encodeURIComponent(data.query)}${
      data.collection ? `&collection=${data.collection}` : ''
    }${data.conversation_id ? `&conversation_id=${data.conversation_id}` : ''}${
      token ? `&token=${encodeURIComponent(token)}` : ''
    }`
  )

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'done') {
      eventSource.close()
      onDone?.()
    } else {
      onMessage(data)
    }
  }

  eventSource.onerror = (error) => {
    eventSource.close()
    onError?.(error)
  }

  return eventSource
}
