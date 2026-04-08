import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RecentConversation, RecentMessage } from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  // 当前对话 ID
  const conversationId = ref<string | undefined>(undefined)

  // 对话历史
  const messages = ref<Array<{
    role: 'user' | 'assistant'
    content: string
    sources?: any[]
    related_questions?: string[]
    timestamp: number
  }>>([])

  // 最近对话列表（用于侧边栏或历史记录）
  const recentConversations = ref<RecentConversation[]>([])

  // 是否正在加载
  const isLoading = ref(false)

  // 设置对话 ID
  function setConversationId(id: string) {
    conversationId.value = id
  }

  // 添加用户消息
  function addUserMessage(content: string) {
    messages.value.push({
      role: 'user',
      content,
      timestamp: Date.now()
    })
  }

  // 添加助手消息
  function addAssistantMessage(content: string, sources?: any[], related_questions?: string[]) {
    messages.value.push({
      role: 'assistant',
      content,
      sources,
      related_questions,
      timestamp: Date.now()
    })
  }

  // 更新最后一条助手消息（用于流式响应）
  function updateLastAssistantMessage(content: string) {
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage && lastMessage.role === 'assistant') {
      lastMessage.content = content
    }
  }

  // 清除对话
  function clearMessages() {
    messages.value = []
    conversationId.value = undefined
  }

  // 加载最近对话历史到当前消息列表（页面初始加载时调用）
  function loadRecentConversations(conversations: RecentConversation[]) {
    recentConversations.value = conversations

    // 清空当前消息列表
    messages.value = []

    // 如果有对话，加载最新的一个对话的消息（用于 RAG 上下文）
    // 注意：只加载最近 5 轮（10 条消息），满足 rag_service.py 中最多 3 轮（6 条）的需求
    if (conversations.length > 0) {
      const latestConv = conversations[0]
      if (latestConv.messages && latestConv.messages.length > 0) {
        // 取最近 5 轮对话（最多 10 条消息）
        const recentMessages = latestConv.messages.slice(-10)

        for (const msg of recentMessages) {
          if (msg.role === 'user') {
            messages.value.push({
              role: 'user',
              content: msg.content,
              timestamp: new Date(msg.created_at || Date.now()).getTime()
            })
          } else {
            messages.value.push({
              role: 'assistant',
              content: msg.content,
              sources: msg.sources,
              timestamp: new Date(msg.created_at || Date.now()).getTime()
            })
          }
        }

        // 设置当前对话 ID 为最新的对话
        conversationId.value = latestConv.id
      }
    }
  }

  // 切换到指定对话
  function switchConversation(conv: RecentConversation) {
    conversationId.value = conv.id
    messages.value = []

    if (conv.messages && conv.messages.length > 0) {
      // 取最近 5 轮对话（最多 10 条消息）
      const recentMessages = conv.messages.slice(-10)

      for (const msg of recentMessages) {
        if (msg.role === 'user') {
          messages.value.push({
            role: 'user',
            content: msg.content,
            timestamp: new Date(msg.created_at || Date.now()).getTime()
          })
        } else {
          messages.value.push({
            role: 'assistant',
            content: msg.content,
            sources: msg.sources,
            timestamp: new Date(msg.created_at || Date.now()).getTime()
          })
        }
      }
    }
  }

  return {
    conversationId,
    messages,
    recentConversations,
    isLoading,
    setConversationId,
    addUserMessage,
    addAssistantMessage,
    updateLastAssistantMessage,
    clearMessages,
    loadRecentConversations,
    switchConversation
  }
})
