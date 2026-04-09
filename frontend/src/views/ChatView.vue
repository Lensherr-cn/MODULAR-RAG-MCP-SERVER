<template>
  <div class="apple-chat">
    <div class="chat-container">
      <!-- Messages Area -->
      <div class="chat-messages" ref="messagesContainer">
        <!-- Empty State -->
        <div v-if="chatStore.messages.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
              <path d="M8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="9" cy="10" r="1" fill="currentColor"/>
              <circle cx="15" cy="10" r="1" fill="currentColor"/>
              <path d="M9 15C9.5 15.5 10.5 16 12 16C13.5 16 14.5 15.5 15 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <h1>今天有什么可以帮你的？</h1>
          <p>基于企业知识库，为你提供精准、即时的答案</p>

          <div class="quick-prompts">
            <button
              v-for="q in defaultQuestions"
              :key="q"
              class="prompt-card"
              @click="handleQuickQuestion(q)"
            >
              <el-icon :size="18"><ChatDotRound /></el-icon>
              <span>{{ q }}</span>
              <el-icon class="prompt-arrow" :size="14"><ArrowRight /></el-icon>
            </button>
          </div>
        </div>

        <!-- Message List -->
        <template v-else>
          <div class="messages-wrapper">
            <ChatMessage
              v-for="(msg, index) in chatStore.messages"
              :key="index"
              :message="msg"
              @related-select="handleRelatedSelect"
            />

            <!-- Loading Indicator -->
            <div v-if="chatStore.isLoading" class="loading-message">
              <div class="loading-avatar">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
                  <path d="M8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  <circle cx="9" cy="10" r="1" fill="currentColor"/>
                  <circle cx="15" cy="10" r="1" fill="currentColor"/>
                </svg>
              </div>
              <div class="loading-content">
                <div class="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Input Area -->
      <div class="chat-input-area">
        <div class="input-container">
          <ChatInput
            v-model="inputText"
            :disabled="chatStore.isLoading"
            placeholder="输入你的问题..."
            @send="handleSend"
          />
          <div class="input-footer">
            <span class="input-hint">
              <el-icon :size="12"><InfoFilled /></el-icon>
              AI 生成的内容仅供参考
            </span>
            <button
              v-if="chatStore.messages.length > 0"
              class="clear-button"
              @click="handleClear"
            >
              <el-icon><Delete /></el-icon>
              清空对话
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChatDotRound,
  ArrowRight,
  InfoFilled,
  Delete
} from '@element-plus/icons-vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import { useChatStore } from '@/stores/chat'
import { chatApi, createChatStream, getRecentConversationsApi } from '@/api/chat'
import { ElMessage } from 'element-plus'

const route = useRoute()
const chatStore = useChatStore()

const inputText = ref('')
const messagesContainer = ref<HTMLElement>()

const defaultQuestions = [
  '报销流程是什么？',
  '如何申请年假？',
  '公司福利有哪些？',
  '考勤制度是怎样的？'
]

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTo({
        top: messagesContainer.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

const handleSend = async (text: string) => {
  if (!text.trim()) return

  // 用户开始新对话，清除清空标记
  clearChatClearedMark()

  chatStore.addUserMessage(text)
  chatStore.isLoading = true
  scrollToBottom()

  try {
    let answer = ''
    let sources: any[] = []
    let relatedQuestions: string[] = []
    let conversationId = ''

    chatStore.addAssistantMessage('')
    scrollToBottom()

    createChatStream(
      {
        query: text,
        conversation_id: chatStore.conversationId,
        stream: true
      },
      (data) => {
        if (data.type === 'token') {
          answer += data.content
          chatStore.updateLastAssistantMessage(answer)
          scrollToBottom()
        } else if (data.type === 'sources') {
          sources = data.sources || []
        } else if (data.type === 'related_questions') {
          relatedQuestions = data.related_questions || []
        } else if (data.conversation_id) {
          conversationId = data.conversation_id
        }
      },
      (error) => {
        console.error('Stream error:', error)
        chatStore.updateLastAssistantMessage(answer || '抱歉，服务出现了一些问题，请稍后重试。')
        chatStore.isLoading = false
      },
      () => {
        const lastMsg = chatStore.messages[chatStore.messages.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.content = answer
          lastMsg.sources = sources
          lastMsg.related_questions = relatedQuestions
        }
        if (conversationId) {
          chatStore.setConversationId(conversationId)
        }
        chatStore.isLoading = false
        scrollToBottom()
      }
    )
  } catch (error) {
    console.error('Chat error:', error)
    try {
      const { data } = await chatApi({
        query: text,
        conversation_id: chatStore.conversationId,
        stream: false
      })
      const resp = data.data
      if (resp) {
        chatStore.messages.pop()
        chatStore.addAssistantMessage(resp.answer, resp.sources, resp.related_questions)
        if (resp.conversation_id) {
          chatStore.setConversationId(resp.conversation_id)
        }
      }
    } catch (err) {
      chatStore.updateLastAssistantMessage('抱歉，服务暂时不可用，请稍后重试。')
    } finally {
      chatStore.isLoading = false
      scrollToBottom()
    }
  }
}

const handleQuickQuestion = (q: string) => {
  handleSend(q)
}

const handleRelatedSelect = (question: string) => {
  handleSend(question)
}

// 检查用户是否已经清空过对话
const hasUserClearedChat = () => {
  return localStorage.getItem('chat_cleared') === 'true'
}

// 标记对话已清空
const markChatCleared = () => {
  localStorage.setItem('chat_cleared', 'true')
}

// 清除清空标记（当用户开始新对话时）
const clearChatClearedMark = () => {
  localStorage.removeItem('chat_cleared')
}

const handleClear = () => {
  chatStore.clearMessages()
  markChatCleared()
  ElMessage.success('对话已清空')
}

// 加载最近对话历史
const loadRecentConversations = async () => {
  // 如果用户已经清空过对话，则不加载历史
  if (hasUserClearedChat()) {
    console.log('[Chat] User has cleared chat, skip loading history')
    return
  }

  console.log('[Chat] Loading recent conversations...')
  try {
    const { data } = await getRecentConversationsApi()
    console.log('[Chat] API response:', data)
    if (data.data && data.data.conversations) {
      console.log('[Chat] Loaded', data.data.conversations.length, 'conversations')
      chatStore.loadRecentConversations(data.data.conversations)
      console.log('[Chat] Messages after load:', chatStore.messages.length)
    } else {
      console.log('[Chat] No conversations in response')
    }
  } catch (error) {
    console.error('[Chat] Failed to load recent conversations:', error)
  }
}

onMounted(() => {
  console.log('[Chat] onMounted')
  // 优先加载最近对话历史
  loadRecentConversations()

  const q = route.query.q as string
  if (q) {
    inputText.value = q
    handleSend(q)
  }
})

// 监听路由变化，当从其他页面返回时重新加载
watch(
  () => route.path,
  (newPath, oldPath) => {
    console.log('[Chat] Route changed from', oldPath, 'to', newPath)
    if (newPath === '/chat') {
      console.log('[Chat] Reloading conversations...')
      loadRecentConversations()
    }
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
.apple-chat {
  height: calc(100vh - 52px);
  background: var(--apple-bg-secondary);
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  height: 100%;
}

/* Messages Area */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 40px 24px;

  @media (max-width: 768px) {
    padding: 24px 16px;
  }
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;

  .empty-icon {
    width: 80px;
    height: 80px;
    color: var(--apple-text-tertiary);
    margin-bottom: 24px;
    animation: pulse 3s ease-in-out infinite;
  }

  h1 {
    font-size: 32px;
    font-weight: 600;
    color: var(--apple-text-primary);
    margin-bottom: 8px;

    @media (max-width: 768px) {
      font-size: 26px;
    }
  }

  p {
    font-size: 17px;
    color: var(--apple-text-secondary);
    margin-bottom: 40px;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

/* Quick Prompts */
.quick-prompts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 600px;
  width: 100%;

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.prompt-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--apple-bg-primary);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-lg);
  cursor: pointer;
  text-align: left;
  transition: all var(--apple-transition-base);

  .el-icon {
    color: var(--apple-text-tertiary);
    flex-shrink: 0;
  }

  span {
    flex: 1;
    font-size: 15px;
    color: var(--apple-text-primary);
  }

  .prompt-arrow {
    opacity: 0;
    transform: translateX(-4px);
    transition: all var(--apple-transition-fast);
  }

  &:hover {
    border-color: var(--apple-accent);
    background: var(--apple-bg-tertiary);
    transform: translateY(-2px);
    box-shadow: var(--apple-shadow-md);

    .prompt-arrow {
      opacity: 1;
      transform: translateX(0);
      color: var(--apple-accent);
    }
  }
}

/* Messages Wrapper */
.messages-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Loading Message */
.loading-message {
  display: flex;
  gap: 12px;
  padding: 0 4px;

  .loading-avatar {
    width: 32px;
    height: 32px;
    color: var(--apple-accent);
    flex-shrink: 0;
  }

  .loading-content {
    background: var(--apple-bg-primary);
    border-radius: 18px;
    padding: 16px 20px;
    box-shadow: var(--apple-shadow-sm);
  }

  .loading-dots {
    display: flex;
    gap: 6px;

    span {
      width: 8px;
      height: 8px;
      background: var(--apple-text-tertiary);
      border-radius: 50%;
      animation: bounce 1.4s ease-in-out infinite both;

      &:nth-child(1) {
        animation-delay: -0.32s;
      }

      &:nth-child(2) {
        animation-delay: -0.16s;
      }
    }
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Input Area */
.chat-input-area {
  padding: 24px;
  background: var(--apple-bg-secondary);
  border-top: 1px solid var(--apple-border);

  @media (max-width: 768px) {
    padding: 16px;
  }
}

.input-container {
  max-width: 900px;
  margin: 0 auto;
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding: 0 4px;

  .input-hint {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--apple-text-tertiary);

    .el-icon {
      opacity: 0.7;
    }
  }

  .clear-button {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 12px;
    background: transparent;
    border: none;
    border-radius: var(--apple-radius-full);
    font-size: 13px;
    color: var(--apple-text-secondary);
    cursor: pointer;
    transition: all var(--apple-transition-fast);

    &:hover {
      background: var(--apple-bg-tertiary);
      color: #ff3b30;
    }
  }
}
</style>
