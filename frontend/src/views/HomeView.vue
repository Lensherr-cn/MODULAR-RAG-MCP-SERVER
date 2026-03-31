<template>
  <div class="apple-home">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge apple-animate-fade-up" style="animation-delay: 0.1s">
          <span class="badge-new">全新</span>
          <span>企业知识库 AI 2.0</span>
        </div>
        <h1 class="hero-title apple-animate-fade-up" style="animation-delay: 0.2s">
          知识，<br>触手可及。
        </h1>
        <p class="hero-subtitle apple-animate-fade-up" style="animation-delay: 0.3s">
          基于先进的人工智能技术，<br>为您的团队提供即时、准确的知识服务。
        </p>
        <div class="hero-search apple-animate-fade-up" style="animation-delay: 0.4s">
          <div class="search-box">
            <el-icon class="search-icon" :size="20"><Search /></el-icon>
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索文档、问题或知识..."
              @keyup.enter="handleSearch"
            >
            <button class="search-button" @click="handleSearch">
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
          <div class="search-suggestions">
            <span class="suggestion-label">热门搜索：</span>
            <button
              v-for="suggestion in hotSuggestions"
              :key="suggestion"
              class="suggestion-tag"
              @click="handleSuggestion(suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>
      </div>
      <div class="hero-visual apple-animate-fade-up" style="animation-delay: 0.5s">
        <div class="floating-card card-1">
          <div class="card-icon">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="card-info">
            <span class="card-label">文档处理</span>
            <span class="card-value">{{ stats.document_count }}+</span>
          </div>
        </div>
        <div class="floating-card card-2">
          <div class="card-icon blue">
            <el-icon :size="24"><ChatDotRound /></el-icon>
          </div>
          <div class="card-info">
            <span class="card-label">今日问答</span>
            <span class="card-value">{{ stats.today_queries }}</span>
          </div>
        </div>
        <div class="floating-card card-3">
          <div class="card-icon green">
            <el-icon :size="24"><User /></el-icon>
          </div>
          <div class="card-info">
            <span class="card-label">活跃用户</span>
            <span class="card-value">{{ stats.active_users }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section">
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-number">{{ stats.document_count }}</span>
          <span class="stat-label">文档总数</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-number">{{ stats.chunk_count }}</span>
          <span class="stat-label">知识片段</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-number">{{ stats.total_queries }}</span>
          <span class="stat-label">累计问答</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-number">99.9%</span>
          <span class="stat-label">服务可用性</span>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <h2>强大的知识管理能力</h2>
        <p>从文档管理到智能问答，一站式解决企业知识需求</p>
      </div>
      <div class="features-grid">
        <div class="feature-card" v-for="(feature, index) in features" :key="index">
          <div class="feature-icon" :class="feature.color">
            <el-icon :size="28">
              <component :is="feature.icon" />
            </el-icon>
          </div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </div>
      </div>
    </section>

    <!-- Content Section -->
    <section class="content-section">
      <div class="content-grid">
        <!-- Hot Questions -->
        <div class="content-block">
          <div class="block-header">
            <h3>热门问题</h3>
            <router-link to="/chat" class="block-link">
              查看全部 <el-icon><ArrowRight /></el-icon>
            </router-link>
          </div>
          <div class="question-list">
            <div
              v-for="(question, index) in hotQuestions"
              :key="question.id"
              class="question-item"
              @click="handleQuestionClick(question.question)"
            >
              <span class="question-rank" :class="{ 'top': index < 3 }">{{ index + 1 }}</span>
              <span class="question-text">{{ question.question }}</span>
              <span class="question-count">{{ question.count }} 次询问</span>
            </div>
          </div>
        </div>

        <!-- Recent Documents -->
        <div class="content-block">
          <div class="block-header">
            <h3>最近更新</h3>
            <router-link to="/documents" class="block-link">
              查看全部 <el-icon><ArrowRight /></el-icon>
            </router-link>
          </div>
          <div class="doc-list">
            <div
              v-for="doc in recentDocs"
              :key="doc.id"
              class="doc-item"
              @click="handleDocClick(doc.id)"
            >
              <div class="doc-icon" :class="getFileIconClass(doc.file_type)">
                <el-icon :size="20">
                  <component :is="getFileIcon(doc.file_type)" />
                </el-icon>
              </div>
              <div class="doc-info">
                <span class="doc-name">{{ doc.name }}</span>
                <span class="doc-meta">{{ doc.category }} · {{ formatDate(doc.updated_at) }}</span>
              </div>
              <el-icon class="doc-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Categories Section -->
    <section class="categories-section" v-if="categories.length > 0">
      <div class="section-header">
        <h2>文档分类</h2>
        <p>按类别浏览您的知识库</p>
      </div>
      <div class="categories-grid">
        <div
          v-for="category in categories"
          :key="category.name"
          class="category-card"
          @click="handleCategoryClick(category.name)"
        >
          <div class="category-icon">
            <el-icon :size="32"><Folder /></el-icon>
          </div>
          <div class="category-info">
            <span class="category-name">{{ category.name }}</span>
            <span class="category-count">{{ category.count }} 篇文档</span>
          </div>
          <div class="category-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="cta-content">
        <h2>准备好开始了吗？</h2>
        <p>立即体验智能知识库的强大功能</p>
        <div class="cta-buttons">
          <router-link to="/chat" class="cta-button primary">
            开始问答
            <el-icon><ArrowRight /></el-icon>
          </router-link>
          <router-link to="/documents" class="cta-button secondary">
            浏览文档
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  ArrowRight,
  Document,
  ChatDotRound,
  User,
  Folder,
  Cpu,
  DataLine,
  DocumentChecked,
  DocumentCopy,
  Lightning
} from '@element-plus/icons-vue'
import { getOverviewStatsApi, getHotQuestionsApi } from '@/api/stats'
import { getDocumentsApi } from '@/api/document'
import type { OverviewStats, HotQuestion } from '@/api/stats'
import type { Document as DocType } from '@/api/document'

const router = useRouter()

const searchKeyword = ref('')
const hotSuggestions = ['报销流程', '年假申请', '技术文档', '公司福利']

const stats = ref<OverviewStats>({
  document_count: 0,
  chunk_count: 0,
  today_queries: 0,
  total_queries: 0,
  active_users: 0,
  categories: []
})

const hotQuestions = ref<HotQuestion[]>([])
const recentDocs = ref<DocType[]>([])
const categories = ref<{ name: string; count: number }[]>([])

const features = [
  {
    icon: Lightning,
    title: '智能问答',
    description: '基于大语言模型，理解自然语言提问，提供精准答案',
    color: 'blue'
  },
  {
    icon: DocumentChecked,
    title: '文档管理',
    description: '支持多种格式，自动分类整理，版本控制无忧',
    color: 'purple'
  },
  {
    icon: Cpu,
    title: 'AI 解析',
    description: '自动提取文档关键信息，构建知识图谱',
    color: 'orange'
  },
  {
    icon: DataLine,
    title: '数据分析',
    description: '实时统计使用情况，洞察团队知识需求',
    color: 'green'
  }
]

const loadStats = async () => {
  try {
    const { data } = await getOverviewStatsApi()
    if (data.data) {
      stats.value = data.data
      categories.value = data.data.categories
    }
  } catch {
    stats.value = {
      document_count: 156,
      chunk_count: 3420,
      today_queries: 42,
      total_queries: 1250,
      active_users: 38,
      categories: [
        { name: '产品文档', count: 12 },
        { name: '技术文档', count: 23 },
        { name: '规章制度', count: 8 },
        { name: '培训资料', count: 15 }
      ]
    }
    categories.value = stats.value.categories
  }
}

const loadHotQuestions = async () => {
  try {
    const { data } = await getHotQuestionsApi(5)
    if (data.data) {
      hotQuestions.value = data.data
    }
  } catch {
    hotQuestions.value = [
      { id: '1', question: '报销流程是什么？', count: 128 },
      { id: '2', question: '如何申请年假？', count: 96 },
      { id: '3', question: '公司福利有哪些？', count: 84 },
      { id: '4', question: '考勤制度是怎样的？', count: 72 },
      { id: '5', question: '培训资料在哪里？', count: 65 }
    ]
  }
}

const loadRecentDocs = async () => {
  try {
    const { data } = await getDocumentsApi({ page: 1, page_size: 5 })
    if (data.data) {
      recentDocs.value = data.data.items
    }
  } catch {
    recentDocs.value = [
      { id: '1', name: '产品使用手册 v2.0.pdf', category: '产品文档', file_type: 'pdf', file_size: 2457600, chunk_count: 45, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '2', name: '技术架构设计文档.docx', category: '技术文档', file_type: 'docx', file_size: 1843200, chunk_count: 32, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '3', name: '员工手册 2024 版.pdf', category: '规章制度', file_type: 'pdf', file_size: 3174400, chunk_count: 58, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ]
  }
}

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/documents', query: { keyword: searchKeyword.value } })
  }
}

const handleSuggestion = (suggestion: string) => {
  router.push({ path: '/chat', query: { q: suggestion } })
}

const handleQuestionClick = (question: string) => {
  router.push({ path: '/chat', query: { q: question } })
}

const handleDocClick = (id: string) => {
  router.push({ path: `/documents/${id}` })
}

const handleCategoryClick = (category: string) => {
  router.push({ path: '/documents', query: { category } })
}

const getFileIcon = (type: string) => {
  const icons: Record<string, any> = {
    pdf: Document,
    docx: DocumentCopy,
    md: Document
  }
  return icons[type] || Document
}

const getFileIconClass = (type: string) => {
  const classes: Record<string, string> = {
    pdf: 'red',
    docx: 'blue',
    md: 'gray'
  }
  return classes[type] || 'gray'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(() => {
  loadStats()
  loadHotQuestions()
  loadRecentDocs()
})
</script>

<style scoped lang="scss">
.apple-home {
  background: var(--apple-bg-secondary);
}

/* Hero Section */
.hero-section {
  min-height: calc(100vh - 52px);
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
    text-align: center;
    padding: 60px 24px;
  }
}

.hero-content {
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: var(--apple-accent-light);
    border-radius: var(--apple-radius-full);
    font-size: 13px;
    font-weight: 500;
    color: var(--apple-accent);
    margin-bottom: 24px;

    .badge-new {
      background: var(--apple-accent);
      color: white;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 600;
    }
  }

  .hero-title {
    font-size: 64px;
    line-height: 1.05;
    letter-spacing: -0.015em;
    margin-bottom: 24px;

    @media (max-width: 768px) {
      font-size: 42px;
    }
  }

  .hero-subtitle {
    font-size: 21px;
    line-height: 1.4;
    color: var(--apple-text-secondary);
    margin-bottom: 40px;

    @media (max-width: 768px) {
      font-size: 18px;
    }
  }
}

.hero-search {
  .search-box {
    display: flex;
    align-items: center;
    background: var(--apple-bg-primary);
    border-radius: var(--apple-radius-full);
    padding: 4px;
    box-shadow: var(--apple-shadow-lg);
    transition: box-shadow var(--apple-transition-base);

    &:focus-within {
      box-shadow: 0 0 0 4px var(--apple-accent-light), var(--apple-shadow-lg);
    }

    .search-icon {
      margin-left: 20px;
      color: var(--apple-text-tertiary);
    }

    input {
      flex: 1;
      border: none;
      background: transparent;
      padding: 16px 16px;
      font-size: 17px;
      font-family: var(--apple-font-text);
      color: var(--apple-text-primary);
      outline: none;

      &::placeholder {
        color: var(--apple-text-tertiary);
      }
    }

    .search-button {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: var(--apple-accent);
      border: none;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all var(--apple-transition-fast);

      &:hover {
        background: var(--apple-accent-hover);
        transform: scale(1.05);
      }
    }
  }

  .search-suggestions {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
    flex-wrap: wrap;

    @media (max-width: 900px) {
      justify-content: center;
    }

    .suggestion-label {
      font-size: 13px;
      color: var(--apple-text-tertiary);
    }

    .suggestion-tag {
      padding: 6px 14px;
      background: var(--apple-bg-primary);
      border: 1px solid var(--apple-border);
      border-radius: var(--apple-radius-full);
      font-size: 13px;
      color: var(--apple-text-secondary);
      cursor: pointer;
      transition: all var(--apple-transition-fast);

      &:hover {
        background: var(--apple-accent-light);
        border-color: var(--apple-accent);
        color: var(--apple-accent);
      }
    }
  }
}

.hero-visual {
  position: relative;
  height: 400px;

  @media (max-width: 900px) {
    display: none;
  }

  .floating-card {
    position: absolute;
    background: var(--apple-bg-primary);
    border-radius: var(--apple-radius-lg);
    padding: 20px;
    box-shadow: var(--apple-shadow-lg);
    display: flex;
    align-items: center;
    gap: 16px;
    animation: float 6s ease-in-out infinite;

    &.card-1 {
      top: 20px;
      left: 0;
      animation-delay: 0s;
    }

    &.card-2 {
      top: 140px;
      right: 20px;
      animation-delay: 2s;
    }

    &.card-3 {
      bottom: 40px;
      left: 40px;
      animation-delay: 4s;
    }

    .card-icon {
      width: 48px;
      height: 48px;
      border-radius: var(--apple-radius-md);
      background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;

      &.blue {
        background: linear-gradient(135deg, var(--apple-accent), #5856d6);
      }

      &.green {
        background: linear-gradient(135deg, #34c759, #30d158);
      }
    }

    .card-info {
      display: flex;
      flex-direction: column;

      .card-label {
        font-size: 13px;
        color: var(--apple-text-secondary);
      }

      .card-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--apple-text-primary);
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* Stats Section */
.stats-section {
  background: var(--apple-bg-primary);
  padding: 48px 24px;
}

.stats-grid {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 32px;

  .stat-item {
    text-align: center;

    .stat-number {
      display: block;
      font-size: 48px;
      font-weight: 600;
      color: var(--apple-text-primary);
      letter-spacing: -0.015em;
    }

    .stat-label {
      font-size: 15px;
      color: var(--apple-text-secondary);
      margin-top: 4px;
    }
  }

  .stat-divider {
    width: 1px;
    height: 60px;
    background: var(--apple-border);

    @media (max-width: 768px) {
      display: none;
    }
  }
}

/* Features Section */
.features-section {
  padding: 100px 24px;
  max-width: 1200px;
  margin: 0 auto;

  .section-header {
    text-align: center;
    margin-bottom: 64px;

    h2 {
      font-size: 40px;
      margin-bottom: 12px;
    }

    p {
      font-size: 19px;
      color: var(--apple-text-secondary);
    }
  }
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.feature-card {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-xl);
  padding: 32px;
  text-align: center;
  transition: transform var(--apple-transition-base), box-shadow var(--apple-transition-base);

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--apple-shadow-lg);
  }

  .feature-icon {
    width: 64px;
    height: 64px;
    border-radius: var(--apple-radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
    color: white;

    &.blue {
      background: linear-gradient(135deg, var(--apple-accent), #5856d6);
    }

    &.purple {
      background: linear-gradient(135deg, #af52de, #bf5af2);
    }

    &.orange {
      background: linear-gradient(135deg, #ff9500, #ff9f0a);
    }

    &.green {
      background: linear-gradient(135deg, #34c759, #30d158);
    }
  }

  h3 {
    font-size: 19px;
    margin-bottom: 8px;
  }

  p {
    font-size: 15px;
    line-height: 1.5;
  }
}

/* Content Section */
.content-section {
  background: var(--apple-bg-primary);
  padding: 80px 24px;
}

.content-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.content-block {
  .block-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;

    h3 {
      font-size: 24px;
    }

    .block-link {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 14px;
      color: var(--apple-accent);
      font-weight: 500;

      .el-icon {
        transition: transform var(--apple-transition-fast);
      }

      &:hover .el-icon {
        transform: translateX(4px);
      }
    }
  }
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-item {
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
    transform: translateX(4px);
  }

  .question-rank {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 600;
    background: var(--apple-bg-tertiary);
    color: var(--apple-text-secondary);
    flex-shrink: 0;

    &.top {
      background: linear-gradient(135deg, var(--apple-accent), #5856d6);
      color: white;
    }
  }

  .question-text {
    flex: 1;
    font-size: 15px;
    color: var(--apple-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .question-count {
    font-size: 13px;
    color: var(--apple-text-tertiary);
    flex-shrink: 0;
  }
}

.doc-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.doc-item {
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

    .doc-arrow {
      opacity: 1;
      transform: translateX(4px);
    }
  }

  .doc-icon {
    width: 44px;
    height: 44px;
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

  .doc-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;

    .doc-name {
      font-size: 15px;
      color: var(--apple-text-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .doc-meta {
      font-size: 13px;
      color: var(--apple-text-tertiary);
      margin-top: 2px;
    }
  }

  .doc-arrow {
    opacity: 0;
    color: var(--apple-text-tertiary);
    transition: all var(--apple-transition-fast);
  }
}

/* Categories Section */
.categories-section {
  padding: 80px 24px;
  max-width: 1200px;
  margin: 0 auto;

  .section-header {
    text-align: center;
    margin-bottom: 48px;

    h2 {
      font-size: 40px;
      margin-bottom: 12px;
    }

    p {
      font-size: 19px;
      color: var(--apple-text-secondary);
    }
  }
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.category-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  cursor: pointer;
  transition: all var(--apple-transition-base);
  box-shadow: var(--apple-shadow-sm);

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--apple-shadow-md);

    .category-arrow {
      opacity: 1;
      transform: translateX(4px);
    }
  }

  .category-icon {
    width: 56px;
    height: 56px;
    border-radius: var(--apple-radius-md);
    background: linear-gradient(135deg, var(--apple-accent-light), rgba(88, 86, 214, 0.1));
    color: var(--apple-accent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .category-info {
    flex: 1;
    display: flex;
    flex-direction: column;

    .category-name {
      font-size: 17px;
      font-weight: 600;
      color: var(--apple-text-primary);
    }

    .category-count {
      font-size: 13px;
      color: var(--apple-text-secondary);
      margin-top: 2px;
    }
  }

  .category-arrow {
    opacity: 0;
    color: var(--apple-text-tertiary);
    transition: all var(--apple-transition-fast);
  }
}

/* CTA Section */
.cta-section {
  background: var(--apple-bg-primary);
  padding: 100px 24px;
  text-align: center;
}

.cta-content {
  max-width: 600px;
  margin: 0 auto;

  h2 {
    font-size: 48px;
    margin-bottom: 12px;

    @media (max-width: 768px) {
      font-size: 36px;
    }
  }

  p {
    font-size: 21px;
    color: var(--apple-text-secondary);
    margin-bottom: 40px;
  }
}

.cta-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;

  @media (max-width: 480px) {
    flex-direction: column;
    align-items: center;
  }
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 16px 32px;
  font-size: 17px;
  font-weight: 500;
  border-radius: var(--apple-radius-full);
  transition: all var(--apple-transition-fast);
  text-decoration: none;

  &.primary {
    background: var(--apple-accent);
    color: white;

    &:hover {
      background: var(--apple-accent-hover);
      transform: scale(1.02);
    }
  }

  &.secondary {
    background: var(--apple-bg-tertiary);
    color: var(--apple-text-primary);

    &:hover {
      background: var(--apple-border);
    }
  }
}
</style>
