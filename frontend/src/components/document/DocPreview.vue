<template>
  <div class="apple-doc-preview">
    <div v-if="loading" class="preview-loading">
      <div class="loading-spinner">
        <div class="spinner-dot"></div>
        <div class="spinner-dot"></div>
        <div class="spinner-dot"></div>
      </div>
      <span>正在加载文档内容...</span>
    </div>

    <div v-else-if="error" class="preview-error">
      <div class="error-icon">
        <el-icon :size="48"><WarningFilled /></el-icon>
      </div>
      <p>{{ error }}</p>
    </div>

    <div v-else class="preview-content">
      <div class="content-body">
        <div v-if="chunks.length" class="chunks-list">
          <div
            v-for="(chunk, index) in chunks"
            :key="chunk.id || index"
            class="chunk-card"
          >
            <div class="chunk-header">
              <span class="chunk-number">片段 {{ index + 1 }}</span>
              <span v-if="chunk.page" class="chunk-page">第 {{ chunk.page }} 页</span>
            </div>
            <div class="chunk-text">{{ chunk.content }}</div>
          </div>
        </div>

        <div v-else-if="content" class="document-text">
          <pre>{{ content }}</pre>
        </div>

        <div v-else class="preview-empty">
          <div class="empty-icon">
            <el-icon :size="48"><Document /></el-icon>
          </div>
          <h4>暂无内容预览</h4>
          <p>该文档暂无可用预览内容</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { WarningFilled, Document } from '@element-plus/icons-vue'
import { getDocumentDetailApi } from '@/api/document'
import type { Document as DocType, DocumentDetail, Chunk } from '@/api/document'

const props = defineProps<{
  document?: DocType | null
}>()

const loading = ref(false)
const error = ref('')
const content = ref('')
const chunks = ref<Chunk[]>([])

const loadDetail = async () => {
  if (!props.document) {
    content.value = ''
    chunks.value = []
    return
  }

  loading.value = true
  error.value = ''

  try {
    const { data } = await getDocumentDetailApi(props.document.id)
    const detail: DocumentDetail = data.data
    content.value = detail.content || ''
    chunks.value = detail.chunks || []
  } catch (err) {
    error.value = '加载文档失败'
    content.value = ''
    chunks.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.document, loadDetail, { immediate: true })
</script>

<style scoped lang="scss">
.apple-doc-preview {
  height: 100%;
  background: var(--apple-bg-secondary);
  overflow-y: auto;
}

.preview-loading,
.preview-error,
.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--apple-text-secondary);
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  display: flex;
  gap: 6px;

  .spinner-dot {
    width: 10px;
    height: 10px;
    background: var(--apple-accent);
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

.preview-error {
  color: #ff3b30;

  .error-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: rgba(255, 59, 48, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.preview-empty {
  .empty-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: var(--apple-bg-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--apple-text-tertiary);
  }

  h4 {
    font-size: 19px;
    font-weight: 600;
    color: var(--apple-text-primary);
  }
}

.preview-content {
  padding: 24px;
}

.content-body {
  max-width: 800px;
  margin: 0 auto;
}

.chunks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chunk-card {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  padding: 20px;
  box-shadow: var(--apple-shadow-sm);

  .chunk-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--apple-border);

    .chunk-number {
      font-size: 13px;
      font-weight: 600;
      color: var(--apple-accent);
    }

    .chunk-page {
      font-size: 12px;
      color: var(--apple-text-tertiary);
    }
  }

  .chunk-text {
    font-size: 15px;
    line-height: 1.7;
    color: var(--apple-text-primary);
    white-space: pre-wrap;
    word-break: break-word;
  }
}

.document-text {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  padding: 24px;
  box-shadow: var(--apple-shadow-sm);

  pre {
    margin: 0;
    font-family: var(--apple-font-text);
    font-size: 15px;
    line-height: 1.8;
    color: var(--apple-text-primary);
    white-space: pre-wrap;
    word-break: break-word;
  }
}
</style>
