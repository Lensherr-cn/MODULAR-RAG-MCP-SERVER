<template>
  <div class="apple-profile">
    <div class="profile-container">
      <!-- Profile Header -->
      <div class="profile-header-card">
        <div class="profile-avatar-section">
          <div class="profile-avatar">
            <img
              v-if="userStore.userProfile?.avatar"
              :src="userStore.userProfile.avatar"
              alt="Avatar"
            >
            <span v-else>{{ getInitials(userStore.userProfile?.username) }}</span>
          </div>
          <div class="profile-info">
            <h1>{{ userStore.userProfile?.username || '用户' }}</h1>
            <p class="profile-email">{{ userStore.userProfile?.email || 'user@example.com' }}</p>
            <div class="profile-badges">
              <span v-if="userStore.userProfile?.department" class="badge">
                <el-icon :size="12"><OfficeBuilding /></el-icon>
                {{ userStore.userProfile.department }}
              </span>
              <span class="badge">
                <el-icon :size="12"><Calendar /></el-icon>
                加入于 {{ formatDate(userStore.userProfile?.created_at) }}
              </span>
            </div>
          </div>
        </div>
        <button class="logout-btn" @click="handleLogout">
          <el-icon :size="18"><SwitchButton /></el-icon>
          退出登录
        </button>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon blue">
            <el-icon :size="24"><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ queryHistory.length }}</span>
            <span class="stat-label">历史查询</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon yellow">
            <el-icon :size="24"><Star /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ favoriteCount }}</span>
            <span class="stat-label">收藏文档</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green">
            <el-icon :size="24"><ChatLineRound /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ feedbacks.length }}</span>
            <span class="stat-label">反馈记录</span>
          </div>
        </div>
      </div>

      <!-- Tabs Section -->
      <div class="tabs-section">
        <div class="tabs-header">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-button"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <el-icon :size="18">
              <component :is="tab.icon" />
            </el-icon>
            <span>{{ tab.label }}</span>
          </button>
        </div>

        <div class="tabs-content">
          <!-- History Tab -->
          <div v-if="activeTab === 'history'" v-loading="loadingHistory" class="tab-panel">
            <div v-if="queryHistory.length === 0" class="panel-empty">
              <div class="empty-icon">
                <el-icon :size="40"><ChatDotRound /></el-icon>
              </div>
              <h4>暂无查询记录</h4>
              <p>您还没有进行过任何查询</p>
            </div>
            <div v-else class="history-list">
              <div
                v-for="item in queryHistory"
                :key="item.id"
                class="history-item"
                @click="goToChat(item.query)"
              >
                <div class="item-icon">
                  <el-icon :size="20"><ChatDotRound /></el-icon>
                </div>
                <div class="item-content">
                  <span class="item-title">{{ item.query }}</span>
                  <span class="item-time">{{ formatDateTime(item.created_at) }}</span>
                </div>
                <el-icon class="item-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>

          <!-- Favorites Tab -->
          <div v-if="activeTab === 'favorites'" v-loading="loadingFavorites" class="tab-panel">
            <div v-if="favorites.length === 0" class="panel-empty">
              <div class="empty-icon">
                <el-icon :size="40"><Star /></el-icon>
              </div>
              <h4>暂无收藏文档</h4>
              <p>您还没有收藏任何文档</p>
            </div>
            <div v-else class="favorites-list">
              <div
                v-for="item in favorites"
                :key="item.id"
                class="favorite-item"
                @click="goToDocument(item.id)"
              >
                <div class="item-icon document">
                  <el-icon :size="20"><Document /></el-icon>
                </div>
                <div class="item-content">
                  <span class="item-title">{{ item.name }}</span>
                  <span class="item-time">{{ formatDateTime(item.updated_at) }}</span>
                </div>
                <button class="remove-btn" @click.stop="removeFavorite(item.id)">
                  <el-icon :size="16"><StarFilled /></el-icon>
                </button>
              </div>
            </div>
          </div>

          <!-- Feedback Tab -->
          <div v-if="activeTab === 'feedback'" v-loading="loadingFeedbacks" class="tab-panel">
            <div v-if="feedbacks.length === 0" class="panel-empty">
              <div class="empty-icon">
                <el-icon :size="40"><ChatLineRound /></el-icon>
              </div>
              <h4>暂无反馈记录</h4>
              <p>您还没有提交过任何反馈</p>
            </div>
            <div v-else class="feedback-list">
              <div
                v-for="item in feedbacks"
                :key="item.id"
                class="feedback-item"
                :class="item.type"
              >
                <div class="feedback-icon" :class="item.type">
                  <el-icon :size="20">
                    <component :is="getFeedbackIcon(item.type)" />
                  </el-icon>
                </div>
                <div class="feedback-content">
                  <p class="feedback-text">{{ item.content }}</p>
                  <span class="feedback-time">{{ formatDateTime(item.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  SwitchButton,
  OfficeBuilding,
  Calendar,
  ChatDotRound,
  Star,
  StarFilled,
  ChatLineRound,
  ArrowRight,
  Document,
  CircleCheck,
  CircleClose,
  Lightning
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getFavoritesApi, getFavoriteCountApi, toggleFavoriteApi } from '@/api/document'
import {
  getQueryHistoryApi,
  getFeedbacksApi,
  type QueryHistory,
  type Feedback
} from '@/api/user'
import type { Document as DocType } from '@/api/document'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('history')
const tabs = [
  { key: 'history', label: '查询历史', icon: ChatDotRound },
  { key: 'favorites', label: '收藏文档', icon: Star },
  { key: 'feedback', label: '反馈记录', icon: ChatLineRound },
]

const queryHistory = ref<QueryHistory[]>([])
const favorites = ref<DocType[]>([])
const favoriteCount = ref(0)
const feedbacks = ref<Feedback[]>([])

const loadingHistory = ref(false)
const loadingFavorites = ref(false)
const loadingFeedbacks = ref(false)

const getInitials = (name?: string) => {
  if (!name) return 'U'
  return name.slice(0, 2).toUpperCase()
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days} 天前`
  if (days < 30) return `${Math.floor(days / 7)} 周前`

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const loadQueryHistory = async () => {
  loadingHistory.value = true
  try {
    const { data } = await getQueryHistoryApi({ limit: 20 })
    if (data.data) {
      queryHistory.value = data.data
    }
  } catch {
    queryHistory.value = [
      { id: '1', query: '报销流程是什么？', created_at: new Date().toISOString() },
      { id: '2', query: '如何申请年假？', created_at: new Date(Date.now() - 86400000).toISOString() },
      { id: '3', query: '技术架构文档在哪？', created_at: new Date(Date.now() - 172800000).toISOString() },
    ]
  } finally {
    loadingHistory.value = false
  }
}

const loadFavorites = async () => {
  loadingFavorites.value = true
  try {
    const { data } = await getFavoritesApi()
    if (data.data?.items) {
      favorites.value = data.data.items
    }
  } catch {
    favorites.value = []
  } finally {
    loadingFavorites.value = false
  }
}

const loadFavoriteCount = async () => {
  try {
    const { data } = await getFavoriteCountApi()
    if (data.data) {
      favoriteCount.value = data.data.count
    }
  } catch {
    favoriteCount.value = 0
  }
}

const loadFeedbacks = async () => {
  loadingFeedbacks.value = true
  try {
    const { data } = await getFeedbacksApi()
    if (data.data) {
      feedbacks.value = data.data
    }
  } catch {
    feedbacks.value = [
      { id: '1', content: '报销流程回答很有帮助', type: 'positive', created_at: new Date().toISOString() },
      { id: '2', content: '年假申请流程需要更新', type: 'suggestion', created_at: new Date(Date.now() - 86400000).toISOString() },
    ]
  } finally {
    loadingFeedbacks.value = false
  }
}

const getFeedbackIcon = (type: string) => {
  switch (type) {
    case 'positive': return CircleCheck
    case 'negative': return CircleClose
    default: return Lightning
  }
}

const goToChat = (query: string) => {
  router.push({ path: '/chat', query: { q: query } })
}

const goToDocument = (id: string) => {
  router.push({ path: `/documents/${id}` })
}

const removeFavorite = async (id: string) => {
  try {
    await toggleFavoriteApi(id)
    favorites.value = favorites.value.filter(f => f.id !== id)
    favoriteCount.value = Math.max(0, favoriteCount.value - 1)
    ElMessage.success('已取消收藏')
  } catch {
    ElMessage.error('取消收藏失败')
  }
}

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/')
}

onMounted(() => {
  loadQueryHistory()
  loadFavorites()
  loadFavoriteCount()
  loadFeedbacks()
})
</script>

<style scoped lang="scss">
.apple-profile {
  min-height: calc(100vh - 52px);
  background: var(--apple-bg-secondary);
  padding: 32px 24px;

  @media (max-width: 768px) {
    padding: 16px;
  }
}

.profile-container {
  max-width: 1000px;
  margin: 0 auto;
}

/* Profile Header Card */
.profile-header-card {
  background: linear-gradient(135deg, var(--apple-accent), #5856d6);
  border-radius: var(--apple-radius-xl);
  padding: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;

  @media (max-width: 768px) {
    flex-direction: column;
    text-align: center;
    padding: 24px;
  }
}

.profile-avatar-section {
  display: flex;
  align-items: center;
  gap: 24px;

  @media (max-width: 768px) {
    flex-direction: column;
  }

  .profile-avatar {
    width: 88px;
    height: 88px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 3px solid rgba(255, 255, 255, 0.3);
    overflow: hidden;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    span {
      font-size: 32px;
      font-weight: 600;
      color: white;
    }
  }

  .profile-info {
    h1 {
      font-size: 28px;
      color: white;
      margin-bottom: 4px;

      @media (max-width: 768px) {
        font-size: 24px;
      }
    }

    .profile-email {
      font-size: 15px;
      color: rgba(255, 255, 255, 0.8);
      margin-bottom: 12px;
    }

    .profile-badges {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;

      @media (max-width: 768px) {
        justify-content: center;
      }

      .badge {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: rgba(255, 255, 255, 0.15);
        border-radius: var(--apple-radius-full);
        font-size: 13px;
        color: white;
      }
    }
  }
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--apple-radius-full);
  color: white;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--apple-transition-fast);

  &:hover {
    background: rgba(255, 255, 255, 0.25);
  }

  @media (max-width: 768px) {
    width: 100%;
    justify-content: center;
  }
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--apple-shadow-sm);
  transition: transform var(--apple-transition-base);

  &:hover {
    transform: translateY(-2px);
  }

  .stat-icon {
    width: 52px;
    height: 52px;
    border-radius: var(--apple-radius-md);
    display: flex;
    align-items: center;
    justify-content: center;

    &.blue {
      background: var(--apple-accent-light);
      color: var(--apple-accent);
    }

    &.yellow {
      background: rgba(255, 204, 0, 0.15);
      color: #ff9500;
    }

    &.green {
      background: rgba(52, 199, 89, 0.15);
      color: #34c759;
    }
  }

  .stat-info {
    .stat-value {
      display: block;
      font-size: 28px;
      font-weight: 600;
      color: var(--apple-text-primary);
    }

    .stat-label {
      font-size: 14px;
      color: var(--apple-text-secondary);
    }
  }
}

/* Tabs Section */
.tabs-section {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-xl);
  box-shadow: var(--apple-shadow-sm);
  overflow: hidden;
}

.tabs-header {
  display: flex;
  border-bottom: 1px solid var(--apple-border);
  padding: 8px;
  gap: 8px;

  @media (max-width: 640px) {
    overflow-x: auto;
  }
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: var(--apple-radius-md);
  border: none;
  background: transparent;
  font-size: 15px;
  font-weight: 500;
  color: var(--apple-text-secondary);
  cursor: pointer;
  transition: all var(--apple-transition-fast);
  white-space: nowrap;

  &:hover {
    background: var(--apple-bg-tertiary);
    color: var(--apple-text-primary);
  }

  &.active {
    background: var(--apple-accent-light);
    color: var(--apple-accent);
  }
}

.tabs-content {
  padding: 24px;
  min-height: 400px;
}

/* Tab Panels */
.tab-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.panel-empty {
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

/* Lists */
.history-list,
.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item,
.favorite-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--apple-bg-secondary);
  border-radius: var(--apple-radius-md);
  cursor: pointer;
  transition: all var(--apple-transition-fast);

  &:hover {
    background: var(--apple-bg-tertiary);

    .item-arrow {
      opacity: 1;
      transform: translateX(4px);
    }
  }

  .item-icon {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: var(--apple-accent-light);
    color: var(--apple-accent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.document {
      background: rgba(255, 204, 0, 0.15);
      color: #ff9500;
    }
  }

  .item-content {
    flex: 1;
    min-width: 0;

    .item-title {
      display: block;
      font-size: 15px;
      font-weight: 500;
      color: var(--apple-text-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-bottom: 4px;
    }

    .item-time {
      font-size: 13px;
      color: var(--apple-text-tertiary);
    }
  }

  .item-arrow {
    opacity: 0;
    color: var(--apple-text-tertiary);
    transition: all var(--apple-transition-fast);
  }

  .remove-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: #ff9500;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--apple-transition-fast);

    &:hover {
      background: rgba(255, 204, 0, 0.15);
      transform: scale(1.1);
    }
  }
}

/* Feedback List */
.feedback-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feedback-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--apple-bg-secondary);
  border-radius: var(--apple-radius-lg);

  &.positive {
    border-left: 4px solid #34c759;
  }

  &.negative {
    border-left: 4px solid #ff3b30;
  }

  &.suggestion {
    border-left: 4px solid #ff9500;
  }

  .feedback-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.positive {
      background: rgba(52, 199, 89, 0.15);
      color: #34c759;
    }

    &.negative {
      background: rgba(255, 59, 48, 0.15);
      color: #ff3b30;
    }

    &.suggestion {
      background: rgba(255, 149, 0, 0.15);
      color: #ff9500;
    }
  }

  .feedback-content {
    flex: 1;

    .feedback-text {
      font-size: 15px;
      color: var(--apple-text-primary);
      margin-bottom: 8px;
      line-height: 1.5;
    }

    .feedback-time {
      font-size: 13px;
      color: var(--apple-text-tertiary);
    }
  }
}
</style>
