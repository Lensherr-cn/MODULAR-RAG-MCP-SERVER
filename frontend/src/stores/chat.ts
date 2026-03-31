import { defineStore } from 'pinia'
import { ref } from 'vue'

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

  return {
    conversationId,
    messages,
    isLoading,
    setConversationId,
    addUserMessage,
    addAssistantMessage,
    updateLastAssistantMessage,
    clearMessages
  }
})
