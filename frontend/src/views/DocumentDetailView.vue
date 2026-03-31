<template>
  <div class="apple-doc-detail">
    <div class="detail-container">
      <!-- Breadcrumb -->
      <nav class="detail-breadcrumb">
        <router-link to="/" class="breadcrumb-link">首页</router-link>
        <el-icon :size="12"><ArrowRight /></el-icon>
        <router-link to="/documents" class="breadcrumb-link">文档中心</router-link>
        <el-icon :size="12"><ArrowRight /></el-icon>
        <span class="breadcrumb-current">文档详情</span>
      </nav>

      <!-- Document Info Card -->
      <div class="info-card" v-loading="loading">
        <div class="info-header">
          <div class="file-icon large" :class="fileIconClass">
            <el-icon :size="32">
              <component :is="fileIcon" />
            </el-icon>
          </div>
          <div class="info-content">
            <h1>{{ document?.name || '加载中...' }}</h1>
            <div class="info-meta">
              <span class="meta-item">
                <el-icon :size="14"><Folder /></el-icon>
                {{ document?.category }}
              </span>
              <span class="meta-item">
                <el-icon :size="14"><Document /></el-icon>
                {{ document?.file_type?.toUpperCase() }}
              </span>
              <span class="meta-item">
                <el-icon :size="14"><DataLine /></el-icon>
                {{ formatFileSize(document?.file_size || 0) }}
              </span>
              <span class="meta-item">
                <el-icon :size="14"><Collection /></el-icon>
                {{ document?.chunk_count }} 片段
              </span>
            </div>
          </div>
          <div class="info-actions">
            <button class="btn-primary" @click="handleDownload">
              <el-icon :size="18"><Download /></el-icon>
              下载
            </button>
            <button
              class="btn-secondary"
              :class="{ active: isFavorite }"
              @click="handleFavorite"
            >
              <el-icon :size="18">
                <component :is="isFavorite ? StarFilled : Star" />
              </el-icon>
              {{ isFavorite ? '已收藏' : '收藏' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Document Content -->
      <div class="content-card" v-loading="contentLoading">
        <div class="card-header">
          <h3>文档内容</h3>
          <span class="update-time">
            更新于 {{ formatDate(document?.updated_at) }}
          </span>
        </div>

        <div class="card-body">
          <div v-if="chunks.length" class="chunks-list">
            <div
              v-for="(chunk, index) in chunks"
              :key="chunk.id || index"
              class="chunk-item"
            >
              <div class="chunk-badge">
                <span class="chunk-number">{{ index + 1 }}</span>
                <span v-if="chunk.page" class="chunk-page">第 {{ chunk.page }} 页</span>
              </div>
              <div class="chunk-content">{{ chunk.content }}</div>
            </div>
          </div>

          <div v-else-if="content" class="document-text">
            <pre>{{ content }}</pre>
          </div>

          <div v-else class="empty-state">
            <div class="empty-icon">
              <el-icon :size="48"><Document /></el-icon>
            </div>
            <h4>暂无内容预览</h4>
            <p>该文档暂无可用预览内容</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Document,
  DocumentCopy,
  Download,
  Star,
  StarFilled,
  ArrowRight,
  Folder,
  DataLine,
  Collection
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getDocumentDetailApi } from '@/api/document'
import { toggleFavoriteApi } from '@/api/user'
import type { DocumentDetail, Chunk } from '@/api/document'

const route = useRoute()
const router = useRouter()
const documentId = route.params.id as string

const loading = ref(true)
const contentLoading = ref(true)
const document = ref<DocumentDetail | null>(null)
const content = ref('')
const chunks = ref<Chunk[]>([])
const isFavorite = ref(false)

const fileIcon = computed(() => {
  const icons: Record<string, any> = {
    pdf: Document,
    docx: DocumentCopy,
    md: Document
  }
  return icons[document.value?.file_type || ''] || Document
})

const fileIconClass = computed(() => {
  const classes: Record<string, string> = {
    pdf: 'red',
    docx: 'blue',
    md: 'gray'
  }
  return classes[document.value?.file_type || ''] || 'gray'
})

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const loadDocument = async () => {
  if (!documentId) {
    router.push('/documents')
    return
  }

  loading.value = true
  contentLoading.value = true

  try {
    const { data } = await getDocumentDetailApi(documentId)
    if (data.data) {
      document.value = data.data
      content.value = data.data.content || ''
      chunks.value = data.data.chunks || []
    }
  } catch {
    // 模拟数据
    document.value = {
      id: documentId,
      name: '产品使用手册 v2.0.pdf',
      category: '产品文档',
      file_type: 'pdf',
      file_size: 2457600,
      chunk_count: 12,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      content: '',
      chunks: [
        { id: 'c1', content: '第一章：产品概述\n\n本产品是一款面向企业的知识库管理系统，采用先进的人工智能技术，帮助团队高效管理和利用知识资产。\n\n主要特性包括：\n- 智能问答系统\n- 文档自动解析\n- 全文检索功能\n- 权限管理控制', page: 1 },
        { id: 'c2', content: '第二章：快速入门\n\n2.1 登录系统\n使用企业邮箱和密码登录系统。首次登录后建议修改默认密码。\n\n2.2 上传文档\n支持 PDF、Word、Markdown 等多种格式的文档上传。系统会自动解析文档内容并建立索引。', page: 3 },
        { id: 'c3', content: '第三章：智能问答\n\n在问答页面输入您的问题，系统会基于知识库内容为您提供准确的答案。\n\n支持的问答类型：\n- 流程咨询\n- 政策查询\n- 技术问题\n- 产品说明', page: 5 },
      ]
    }
    chunks.value = document.value.chunks || []
  } finally {
    loading.value = false
    contentLoading.value = false
  }
}

const handleDownload = () => {
  ElMessage.info('下载功能开发中')
}

const handleFavorite = async () => {
  if (!document.value) return
  try {
    await toggleFavoriteApi(document.value.id)
    isFavorite.value = !isFavorite.value
    ElMessage.success(isFavorite.value ? '收藏成功' : '取消收藏')
  } catch {
    isFavorite.value = !isFavorite.value
    ElMessage.success(isFavorite.value ? '收藏成功' : '取消收藏')
  }
}

onMounted(() => {
  loadDocument()
})
</script>

<style scoped lang="scss">
.apple-doc-detail {
  min-height: calc(100vh - 52px);
  background: var(--apple-bg-secondary);
  padding: 24px;

  @media (max-width: 768px) {
    padding: 16px;
  }
}

.detail-container {
  max-width: 1000px;
  margin: 0 auto;
}

/* Breadcrumb */
.detail-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  font-size: 14px;
  color: var(--apple-text-secondary);

  .breadcrumb-link {
    color: var(--apple-text-secondary);
    text-decoration: none;
    transition: color var(--apple-transition-fast);

    &:hover {
      color: var(--apple-accent);
    }
  }

  .breadcrumb-current {
    color: var(--apple-text-primary);
    font-weight: 500;
  }

  .el-icon {
    color: var(--apple-text-tertiary);
  }
}

/* Info Card */
.info-card {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-xl);
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: var(--apple-shadow-sm);
}

.info-header {
  display: flex;
  align-items: flex-start;
  gap: 24px;

  @media (max-width: 768px) {
    flex-direction: column;
  }

  .file-icon {
    width: 72px;
    height: 72px;
    border-radius: var(--apple-radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.large {
      width: 80px;
      height: 80px;
    }

    &.red {
      background: rgba(255, 59, 48, 0.1);
      color: #ff3b30;
    }

    &.blue {
      background: var(--apple-accent-light);
      color: var(--apple-accent);
    }

    &.gray {
      background: var(--apple-bg-tertiary);
      color: var(--apple-text-secondary);
    }
  }

  .info-content {
    flex: 1;
    min-width: 0;

    h1 {
      font-size: 24px;
      font-weight: 600;
      margin: 0 0 16px;

      @media (max-width: 768px) {
        font-size: 20px;
      }
    }

    .info-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;

      .meta-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;
        color: var(--apple-text-secondary);

        .el-icon {
          color: var(--apple-text-tertiary);
        }
      }
    }
  }

  .info-actions {
    display: flex;
    gap: 12px;
    flex-shrink: 0;

    @media (max-width: 768px) {
      width: 100%;
    }

    .btn-primary,
    .btn-secondary {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
      border-radius: var(--apple-radius-full);
      font-size: 15px;
      font-weight: 500;
      border: none;
      cursor: pointer;
      transition: all var(--apple-transition-fast);

      @media (max-width: 768px) {
        flex: 1;
        justify-content: center;
      }
    }

    .btn-primary {
      background: var(--apple-accent);
      color: white;

      &:hover {
        background: var(--apple-accent-hover);
        transform: scale(1.02);
      }
    }

    .btn-secondary {
      background: var(--apple-bg-tertiary);
      color: var(--apple-text-primary);

      &:hover {
        background: var(--apple-border);
      }

      &.active {
        background: rgba(255, 204, 0, 0.15);
        color: #ff9500;
      }
    }
  }
}

/* Content Card */
.content-card {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-xl);
  box-shadow: var(--apple-shadow-sm);
  overflow: hidden;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 28px;
    border-bottom: 1px solid var(--apple-border);

    @media (max-width: 768px) {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    h3 {
      font-size: 19px;
      font-weight: 600;
    }

    .update-time {
      font-size: 13px;
      color: var(--apple-text-secondary);
    }
  }

  .card-body {
    padding: 28px;
  }
}

/* Chunks List */
.chunks-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chunk-item {
  background: var(--apple-bg-secondary);
  border-radius: var(--apple-radius-lg);
  padding: 24px;
  border-left: 4px solid var(--apple-accent);

  .chunk-badge {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;

    .chunk-number {
      font-size: 13px;
      font-weight: 600;
      color: var(--apple-accent);
    }

    .chunk-page {
      font-size: 12px;
      color: var(--apple-text-tertiary);
      padding: 2px 10px;
      background: var(--apple-bg-tertiary);
      border-radius: 10px;
    }
  }

  .chunk-content {
    font-size: 15px;
    line-height: 1.8;
    color: var(--apple-text-primary);
    white-space: pre-wrap;
    word-break: break-word;
  }
}

/* Document Text */
.document-text {
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

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;

  .empty-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: var(--apple-bg-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--apple-text-tertiary);
    margin-bottom: 20px;
  }

  h4 {
    font-size: 19px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  p {
    font-size: 15px;
    color: var(--apple-text-secondary);
  }
}
</style>
