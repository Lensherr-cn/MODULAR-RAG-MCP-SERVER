<template>
  <div class="apple-doc-card" @click="emit('preview', document)">
    <div class="card-header">
      <div class="file-icon" :class="fileIconClass">
        <el-icon :size="24">
          <component :is="fileIcon" />
        </el-icon>
      </div>
      <div class="file-info">
        <h4 class="file-name">{{ document.name }}</h4>
        <div class="file-meta">
          <span class="file-category">{{ document.category }}</span>
          <span class="file-size">{{ formatFileSize(document.file_size) }}</span>
          <span v-if="document.visibility" class="visibility-badge" :class="document.visibility">
            <el-icon :size="12">
              <component :is="visibilityIcon" />
            </el-icon>
            {{ visibilityLabel }}
          </span>
        </div>
      </div>
    </div>

    <div class="card-stats">
      <div class="stat">
        <el-icon :size="14"><Collection /></el-icon>
        <span>{{ document.chunk_count }} 片段</span>
      </div>
      <div class="stat">
        <el-icon :size="14"><Clock /></el-icon>
        <span>{{ formatDate(document.updated_at) }}</span>
      </div>
    </div>

    <div class="card-actions" @click.stop>
      <button class="action-btn" title="预览" @click="emit('preview', document)">
        <el-icon :size="16"><View /></el-icon>
      </button>
      <button class="action-btn" title="下载" @click="handleDownload">
        <el-icon :size="16"><Download /></el-icon>
      </button>
      <button
        class="action-btn"
        :class="{ active: isFavorite }"
        :title="isFavorite ? '取消收藏' : '收藏'"
        @click="handleFavorite"
      >
        <el-icon :size="16">
          <component :is="isFavorite ? StarFilled : Star" />
        </el-icon>
      </button>
      <button
        class="action-btn delete-btn"
        title="删除"
        @click="handleDelete"
      >
        <el-icon :size="16"><Delete /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Document,
  DocumentCopy,
  View,
  Download,
  Star,
  StarFilled,
  Collection,
  Clock,
  Delete,
  View as IconView,
  OfficeBuilding,
  Lock
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { Document as DocType } from '@/api/document'
import { toggleFavoriteApi, getFavoriteStatusApi } from '@/api/document'

const props = defineProps<{
  document: DocType
  favorite?: boolean
}>()

const emit = defineEmits<{
  preview: [doc: DocType]
  download: [doc: DocType]
  delete: [doc: DocType]
  favoriteChange: [docId: string, isFavorite: boolean]
}>()

const isFavorite = ref(props.favorite || false)
const isLoading = ref(false)

// 组件挂载时获取收藏状态
onMounted(async () => {
  if (!props.favorite) {
    try {
      const { data } = await getFavoriteStatusApi(props.document.id)
      if (data.data) {
        isFavorite.value = data.data.is_favorite
      }
    } catch {
      // 忽略错误，保持默认状态
    }
  }
})

const fileIcon = computed(() => {
  const icons: Record<string, any> = {
    pdf: Document,
    docx: DocumentCopy,
    md: Document
  }
  return icons[props.document.file_type] || Document
})

const fileIconClass = computed(() => {
  const classes: Record<string, string> = {
    pdf: 'red',
    docx: 'blue',
    md: 'gray'
  }
  return classes[props.document.file_type] || 'gray'
})

const visibilityIcon = computed(() => {
  const icons: Record<string, any> = {
    public: IconView,
    department: OfficeBuilding,
    private: Lock
  }
  return icons[props.document.visibility] || IconView
})

const visibilityLabel = computed(() => {
  const labels: Record<string, string> = {
    public: '公共',
    department: '部门',
    private: '私有'
  }
  return labels[props.document.visibility] || ''
})

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days} 天前`
  if (days < 30) return `${Math.floor(days / 7)} 周前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const handleDownload = () => {
  emit('download', props.document)
}

const handleFavorite = async () => {
  if (isLoading.value) return

  isLoading.value = true
  // 乐观更新
  const previousState = isFavorite.value
  isFavorite.value = !isFavorite.value

  try {
    const { data } = await toggleFavoriteApi(props.document.id)
    if (data.data) {
      isFavorite.value = data.data.is_favorite
      ElMessage.success(isFavorite.value ? '收藏成功' : '取消收藏')
      // 触发事件通知父组件
      emit('favorite-change', props.document.id, isFavorite.value)
    }
  } catch (error: any) {
    // 失败时回滚状态
    isFavorite.value = previousState
    ElMessage.error(error.response?.data?.detail || '操作失败，请重试')
  } finally {
    isLoading.value = false
  }
}

const handleDelete = () => {
  emit('delete', props.document)
}
</script>

<style scoped lang="scss">
.apple-doc-card {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  padding: 20px;
  box-shadow: var(--apple-shadow-sm);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--apple-transition-base);

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--apple-shadow-lg);
    border-color: var(--apple-border);

    .card-actions {
      opacity: 1;
    }
  }
}

.card-header {
  display: flex;
  gap: 14px;
  margin-bottom: 16px;

  .file-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--apple-radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

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

  .file-info {
    flex: 1;
    min-width: 0;

    .file-name {
      font-size: 15px;
      font-weight: 600;
      color: var(--apple-text-primary);
      margin: 0 0 6px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .file-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: var(--apple-text-secondary);

      .file-category {
        padding: 2px 8px;
        background: var(--apple-bg-tertiary);
        border-radius: 4px;
      }

      .visibility-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;

        &.public {
          background: rgba(52, 199, 89, 0.1);
          color: #34c759;
        }

        &.department {
          background: rgba(0, 122, 255, 0.1);
          color: #007aff;
        }

        &.private {
          background: rgba(255, 59, 48, 0.1);
          color: #ff3b30;
        }
      }
    }
  }
}

.card-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;

  .stat {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--apple-text-tertiary);

    .el-icon {
      opacity: 0.7;
    }
  }
}

.card-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity var(--apple-transition-base);

  @media (max-width: 1024px) {
    opacity: 1;
  }

  .action-btn {
    width: 36px;
    height: 36px;
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

    &.active {
      background: rgba(255, 204, 0, 0.15);
      color: #ff9500;
    }

    &.delete-btn {
      &:hover {
        background: rgba(255, 59, 48, 0.15);
        color: #ff3b30;
      }
    }
  }
}
</style>
