<template>
  <div class="apple-source-card" @click="handleClick">
    <div class="source-header">
      <div class="source-icon">
        <el-icon :size="16"><Document /></el-icon>
      </div>
      <span class="source-name">{{ source.document_name }}</span>
      <span v-if="source.score" class="source-score">{{ formatScore(source.score) }}</span>
    </div>
    <div v-if="source.content" class="source-content">
      {{ truncateContent(source.content) }}
    </div>
    <div v-if="source.page" class="source-meta">
      第 {{ source.page }} 页
    </div>
  </div>
</template>

<script setup lang="ts">
import { Document } from '@element-plus/icons-vue'
import type { ChatSource } from '@/api/chat'

const props = defineProps<{
  source: ChatSource
}>()

const emit = defineEmits<{
  click: [source: ChatSource]
}>()

const formatScore = (score: number) => {
  return (score * 100).toFixed(0) + '%'
}

const truncateContent = (content: string, maxLength: number = 60) => {
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}

const handleClick = () => {
  emit('click', props.source)
}
</script>

<style scoped lang="scss">
.apple-source-card {
  width: 240px;
  background: var(--apple-bg-tertiary);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-md);
  padding: 12px;
  cursor: pointer;
  transition: all var(--apple-transition-fast);

  &:hover {
    border-color: var(--apple-accent);
    background: var(--apple-bg-primary);
    box-shadow: var(--apple-shadow-md);
    transform: translateY(-2px);
  }
}

.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  .source-icon {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    background: var(--apple-accent-light);
    color: var(--apple-accent);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .source-name {
    flex: 1;
    font-size: 13px;
    font-weight: 500;
    color: var(--apple-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .source-score {
    font-size: 11px;
    font-weight: 600;
    color: #34c759;
    background: rgba(52, 199, 89, 0.1);
    padding: 2px 8px;
    border-radius: 10px;
  }
}

.source-content {
  font-size: 12px;
  color: var(--apple-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}

.source-meta {
  font-size: 11px;
  color: var(--apple-text-tertiary);
}
</style>
