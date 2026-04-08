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
  return post<ChatResponse>('/v1/chat', data)
}

// 获取对话历史
export function getChatHistoryApi(conversation_id?: string) {
  return get<ChatResponse[]>(`/v1/chat/history${conversation_id ? `?conversation_id=${conversation_id}` : ''}`)
}

// 流式问答（使用 fetch + ReadableStream，支持 Cookie）
export async function createChatStream(
  data: ChatRequest,
  onMessage: (data: any) => void,
  onError?: (error: any) => void,
  onDone?: () => void
): Promise<() => void> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  const apiBase = baseUrl.endsWith('/v1') ? baseUrl : `${baseUrl}/v1`
  const url = `${apiBase}/chat/stream?query=${encodeURIComponent(data.query)}${
    data.collection ? `&collection=${data.collection}` : ''
  }${data.conversation_id ? `&conversation_id=${data.conversation_id}` : ''}`

  const abortController = new AbortController()

  try {
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include', // 关键：携带 Cookie
      signal: abortController.signal,
    })

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized')
      }
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    // 读取流数据
    const readStream = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            onDone?.()
            break
          }

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // 保留未完成的部分

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonData = line.slice(6)
              if (jsonData.trim() === '[DONE]') {
                onDone?.()
                return
              }
              try {
                const parsed = JSON.parse(jsonData)
                if (parsed.type === 'done') {
                  onDone?.()
                  return
                }
                onMessage(parsed)
              } catch (e) {
                // 忽略解析错误
              }
            }
          }
        }
      } catch (error: any) {
        if (error.name !== 'AbortError') {
          onError?.(error)
        }
      }
    }

    readStream()

    // 返回取消函数
    return () => {
      abortController.abort()
      reader.cancel()
    }
  } catch (error) {
    onError?.(error)
    // 返回空取消函数
    return () => {}
  }
}
