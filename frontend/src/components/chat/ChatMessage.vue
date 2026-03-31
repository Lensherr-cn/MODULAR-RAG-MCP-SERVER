<template>
  <div class="apple-chat-message" :class="message.role">
    <div class="message-avatar">
      <div v-if="message.role === 'user'" class="avatar user-avatar">
        <img v-if="userStore.userProfile?.avatar" :src="userStore.userProfile.avatar" alt="User">
        <span v-else>{{ getInitials(userStore.userProfile?.username) }}</span>
      </div>
      <div v-else class="avatar assistant-avatar">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <path d="M8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <circle cx="9" cy="10" r="1" fill="currentColor"/>
          <circle cx="15" cy="10" r="1" fill="currentColor"/>
        </svg>
      </div>
    </div>
    <div class="message-content">
      <div class="message-bubble">
        <div class="message-text" v-html="formatContent(message.content)"></div>
      </div>

      <!-- Sources -->
      <div v-if="message.sources && message.sources.length" class="message-sources">
        <div class="sources-header">
          <el-icon :size="14"><Document /></el-icon>
          <span>引用来源</span>
        </div>
        <div class="sources-list">
          <SourceCard
            v-for="(source, index) in message.sources"
            :key="source.chunk_id || index"
            :source="source"
          />
        </div>
      </div>

      <!-- Related Questions -->
      <div v-if="message.related_questions && message.related_questions.length" class="message-related">
        <RelatedQuestions
          :questions="message.related_questions"
          @select="handleRelatedSelect"
        />
      </div>

      <!-- Actions -->
      <div v-if="message.role === 'assistant' && message.content" class="message-actions">
        <button class="action-button" @click="handleCopy" title="复制">
          <el-icon :size="16"><CopyDocument /></el-icon>
        </button>
        <button class="action-button" @click="handleFeedback('positive')" title="有帮助">
          <el-icon :size="16"><CircleCheck /></el-icon>
        </button>
        <button class="action-button" @click="handleFeedback('negative')" title="无帮助">
          <el-icon :size="16"><CircleClose /></el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CopyDocument, CircleCheck, CircleClose, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import SourceCard from './SourceCard.vue'
import RelatedQuestions from './RelatedQuestions.vue'
import { submitFeedbackApi } from '@/api/user'
import { useUserStore } from '@/stores/user'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
  related_questions?: string[]
  timestamp?: number
}

const props = defineProps<{
  message: Message
}>()

const emit = defineEmits<{
  relatedSelect: [question: string]
}>()

const userStore = useUserStore()

const getInitials = (name?: string) => {
  if (!name) return 'U'
  return name.slice(0, 2).toUpperCase()
}

const formatContent = (content: string) => {
  if (!content) return ''
  // 转义 HTML 特殊字符
  const escaped = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 处理换行
  return escaped.replace(/\n/g, '<br>')
}

const handleRelatedSelect = (question: string) => {
  emit('relatedSelect', question)
}

const handleCopy = () => {
  navigator.clipboard.writeText(props.message.content)
  ElMessage.success('已复制到剪贴板')
}

const handleFeedback = async (type: 'positive' | 'negative') => {
  try {
    await submitFeedbackApi({
      content: type === 'positive' ? '回答很有帮助' : '回答没有帮助',
      type
    })
    ElMessage.success(type === 'positive' ? '感谢你的认可' : '我们会继续改进')
  } catch {
    ElMessage.success(type === 'positive' ? '感谢你的认可' : '我们会继续改进')
  }
}
</script>

<style scoped lang="scss">
.apple-chat-message {
  display: flex;
  gap: 12px;
  padding: 0 4px;

  &.user {
    flex-direction: row-reverse;

    .message-content {
      align-items: flex-end;
    }

    .message-bubble {
      background: var(--apple-accent);
      color: white;
      border-bottom-right-radius: 4px;
    }
  }

  &.assistant {
    .message-bubble {
      background: var(--apple-bg-primary);
      color: var(--apple-text-primary);
      border-bottom-left-radius: 4px;
      box-shadow: var(--apple-shadow-sm);
    }
  }
}

.message-avatar {
  flex-shrink: 0;

  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;

    &.user-avatar {
      background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
      color: white;
      font-size: 12px;
      font-weight: 600;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    &.assistant-avatar {
      background: var(--apple-accent-light);
      color: var(--apple-accent);
    }
  }
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: calc(100% - 60px);
  gap: 12px;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.6;
  word-wrap: break-word;

  .message-text {
    white-space: pre-wrap;
  }
}

/* Sources */
.message-sources {
  .sources-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--apple-text-secondary);
    margin-bottom: 10px;
  }

  .sources-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

/* Actions */
.message-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity var(--apple-transition-fast);

  .apple-chat-message:hover & {
    opacity: 1;
  }
}

.action-button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--apple-bg-tertiary);
  color: var(--apple-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--apple-transition-fast);

  &:hover {
    background: var(--apple-border);
    color: var(--apple-text-primary);
    transform: scale(1.05);
  }
}

/* Related Questions */
.message-related {
  margin-top: 4px;
}
</style>
