<template>
  <div class="apple-documents">
    <div class="documents-layout">
      <!-- Sidebar -->
      <aside class="documents-sidebar">
        <CategoryTree
          v-model="selectedCategory"
          :categories="categories"
          @select="handleCategorySelect"
        />
      </aside>

      <!-- Main Content -->
      <main class="documents-main">
        <!-- Header -->
        <div class="documents-header">
          <h1>文档中心</h1>
          <p>浏览和管理企业知识库中的所有文档</p>
        </div>

        <!-- Toolbar -->
        <div class="documents-toolbar">
          <div class="search-box">
            <el-icon class="search-icon" :size="18"><Search /></el-icon>
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索文档..."
              @keyup.enter="handleSearch"
            >
            <button v-if="searchKeyword" class="clear-btn" @click="searchKeyword = ''; handleSearch()">
              <el-icon :size="14"><Close /></el-icon>
            </button>
          </div>

          <div class="toolbar-actions">
            <select v-model="selectedFileType" class="filter-select" @change="handleFilterChange">
              <option value="">全部类型</option>
              <option value="pdf">PDF</option>
              <option value="docx">Word</option>
              <option value="md">Markdown</option>
            </select>
          </div>
        </div>

        <!-- Document Grid -->
        <div class="documents-content" v-loading="loading">
          <div v-if="documents.length === 0" class="empty-state">
            <div class="empty-icon">
              <el-icon :size="48"><Document /></el-icon>
            </div>
            <h3>暂无文档</h3>
            <p>该分类下还没有文档</p>
          </div>

          <div v-else class="documents-grid">
            <DocCard
              v-for="doc in documents"
              :key="doc.id"
              :document="doc"
              @preview="handlePreview(doc)"
              @click="handlePreview(doc)"
            />
          </div>

          <!-- Pagination -->
          <div v-if="total > pageSize" class="documents-pagination">
            <el-pagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[12, 24, 48]"
              layout="prev, pager, next, sizes, total"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </main>
    </div>

    <!-- Preview Drawer -->
    <el-drawer
      v-model="previewVisible"
      :size="previewSize"
      :with-header="false"
      class="apple-preview-drawer"
    >
      <div class="drawer-header">
        <h3>{{ selectedDocument?.name }}</h3>
        <div class="drawer-actions">
          <button class="icon-btn" @click="toggleDrawerSize">
            <el-icon><FullScreen /></el-icon>
          </button>
          <button class="icon-btn" @click="previewVisible = false">
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </div>
      <div class="drawer-body">
        <DocPreview :document="selectedDocument" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Close, Document, FullScreen } from '@element-plus/icons-vue'
import CategoryTree from '@/components/document/CategoryTree.vue'
import DocCard from '@/components/document/DocCard.vue'
import DocPreview from '@/components/document/DocPreview.vue'
import { getDocumentsApi, getCategoriesApi } from '@/api/document'
import type { Document as DocType, Category } from '@/api/document'

const route = useRoute()

const loading = ref(false)
const documents = ref<DocType[]>([])
const categories = ref<Category[]>([])
const selectedCategory = ref('')
const searchKeyword = ref('')
const selectedFileType = ref('')
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)

const previewVisible = ref(false)
const selectedDocument = ref<DocType | null>(null)
const isWideDrawer = ref(false)

const previewSize = computed(() => isWideDrawer.value ? '80%' : '60%')

const toggleDrawerSize = () => {
  isWideDrawer.value = !isWideDrawer.value
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const { data } = await getDocumentsApi({
      page: page.value,
      page_size: pageSize.value,
      category: selectedCategory.value || undefined,
      keyword: searchKeyword.value || undefined,
      file_type: selectedFileType.value || undefined,
    })
    if (data.data) {
      documents.value = data.data.items
      total.value = data.data.total
    }
  } catch {
    documents.value = [
      { id: '1', name: '产品使用手册 v2.0.pdf', category: '产品文档', file_type: 'pdf', file_size: 2457600, chunk_count: 45, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '2', name: '技术架构设计文档.docx', category: '技术文档', file_type: 'docx', file_size: 1843200, chunk_count: 32, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '3', name: '员工手册 2024 版.pdf', category: '规章制度', file_type: 'pdf', file_size: 3174400, chunk_count: 58, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '4', name: '培训资料 - 新员工入职.md', category: '培训资料', file_type: 'md', file_size: 45000, chunk_count: 12, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '5', name: 'API 接口文档.pdf', category: '技术文档', file_type: 'pdf', file_size: 1200000, chunk_count: 28, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '6', name: '产品路线图 2024.pdf', category: '产品文档', file_type: 'pdf', file_size: 3200000, chunk_count: 15, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ]
    total.value = documents.value.length
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const { data } = await getCategoriesApi()
    if (data.data) {
      categories.value = data.data
    }
  } catch {
    categories.value = [
      { name: '产品文档', count: 12 },
      { name: '技术文档', count: 23 },
      { name: '规章制度', count: 8 },
      { name: '培训资料', count: 15 },
      { name: '流程规范', count: 10 },
      { name: '其他', count: 5 },
    ]
  }
}

const handleSearch = () => {
  page.value = 1
  loadDocuments()
}

const handleCategorySelect = () => {
  page.value = 1
  loadDocuments()
}

const handleFilterChange = () => {
  page.value = 1
  loadDocuments()
}

const handlePageChange = () => {
  loadDocuments()
}

const handleSizeChange = () => {
  page.value = 1
  loadDocuments()
}

const handlePreview = (doc: DocType) => {
  selectedDocument.value = doc
  previewVisible.value = true
}

watch(() => route.query, (query) => {
  if (query.category) {
    selectedCategory.value = query.category as string
  }
  if (query.keyword) {
    searchKeyword.value = query.keyword as string
  }
  loadDocuments()
}, { immediate: true })

onMounted(() => {
  loadCategories()
})
</script>

<style scoped lang="scss">
.apple-documents {
  min-height: calc(100vh - 52px);
  background: var(--apple-bg-secondary);
  padding: 24px;

  @media (max-width: 768px) {
    padding: 16px;
  }
}

.documents-layout {
  display: flex;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;

  @media (max-width: 900px) {
    flex-direction: column;
  }
}

/* Sidebar */
.documents-sidebar {
  width: 260px;
  flex-shrink: 0;

  @media (max-width: 900px) {
    width: 100%;
  }
}

/* Main Content */
.documents-main {
  flex: 1;
  min-width: 0;
}

.documents-header {
  margin-bottom: 24px;

  h1 {
    font-size: 32px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  p {
    font-size: 15px;
    color: var(--apple-text-secondary);
  }
}

/* Toolbar */
.documents-toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;

  @media (max-width: 640px) {
    flex-direction: column;
  }
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-full);
  padding: 4px 4px 4px 16px;
  border: 1px solid var(--apple-border);
  transition: all var(--apple-transition-base);

  &:focus-within {
    border-color: var(--apple-accent);
    box-shadow: 0 0 0 4px var(--apple-accent-light);
  }

  .search-icon {
    color: var(--apple-text-tertiary);
    margin-right: 10px;
  }

  input {
    flex: 1;
    border: none;
    background: transparent;
    font-size: 15px;
    color: var(--apple-text-primary);
    outline: none;
    padding: 10px 0;

    &::placeholder {
      color: var(--apple-text-tertiary);
    }
  }

  .clear-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: var(--apple-bg-tertiary);
    color: var(--apple-text-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--apple-transition-fast);

    &:hover {
      background: var(--apple-border);
      color: var(--apple-text-secondary);
    }
  }
}

.filter-select {
  padding: 12px 16px;
  border-radius: var(--apple-radius-full);
  border: 1px solid var(--apple-border);
  background: var(--apple-bg-primary);
  font-size: 15px;
  color: var(--apple-text-primary);
  outline: none;
  cursor: pointer;
  min-width: 140px;

  &:focus {
    border-color: var(--apple-accent);
  }
}

/* Content */
.documents-content {
  min-height: 400px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
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

  h3 {
    font-size: 19px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  p {
    font-size: 15px;
    color: var(--apple-text-secondary);
  }
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

/* Pagination */
.documents-pagination {
  display: flex;
  justify-content: center;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--apple-border);
}

/* Drawer Customization */
:deep(.apple-preview-drawer) {
  .el-drawer__body {
    padding: 0;
    display: flex;
    flex-direction: column;
  }
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--apple-border);

  h3 {
    font-size: 17px;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-right: 16px;
  }

  .drawer-actions {
    display: flex;
    gap: 8px;
  }

  .icon-btn {
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
    }
  }
}

.drawer-body {
  flex: 1;
  overflow: hidden;
}
</style>
