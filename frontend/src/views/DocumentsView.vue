<template>
  <div class="documents-page">
    <div class="documents-container">
      <!-- Sidebar -->
      <aside class="sidebar">
        <CategoryTree
          v-model="selectedCategory"
          :categories="categories"
          @select="handleCategorySelect"
        />
      </aside>

      <!-- Main Content -->
      <main class="main-content">
        <!-- Header Section -->
        <header class="page-header">
          <div class="header-content">
            <h1 class="page-title">文档中心</h1>
            <p class="page-subtitle">浏览和管理企业知识库中的所有文档</p>
          </div>
          <div class="header-actions">
            <button class="primary-button" :disabled="uploading" @click="openUploadDialog">
              <el-icon v-if="!uploading" :size="18"><Plus /></el-icon>
              <el-icon v-else class="rotating" :size="18"><Loading /></el-icon>
              <span>{{ uploading ? '上传中' : '上传文档' }}</span>
            </button>
          </div>
        </header>

        <!-- Search & Filter Bar -->
        <div class="control-bar">
          <div class="search-container">
            <div class="search-field">
              <el-icon class="search-icon" :size="16"><Search /></el-icon>
              <input
                v-model="searchKeyword"
                type="text"
                placeholder="搜索文档..."
                @keyup.enter="handleSearch"
              >
              <button v-if="searchKeyword" class="clear-button" @click="searchKeyword = ''; handleSearch()">
                <el-icon :size="12"><Close /></el-icon>
              </button>
            </div>
          </div>

          <div class="filter-container">
            <div class="filter-group">
              <label class="filter-label">类型</label>
              <div class="segmented-control">
                <button
                  v-for="option in fileTypeOptions"
                  :key="option.value"
                  :class="['segment-button', { active: selectedFileType === option.value }]"
                  @click="selectedFileType = option.value; handleFilterChange()"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Results Info -->
        <div class="results-bar">
          <span class="results-count">共 {{ total }} 个文档</span>
          <div v-if="selectedCategory || searchKeyword || selectedFileType" class="active-filters">
            <el-tag
              v-if="selectedCategory"
              closable
              type="primary"
              effect="light"
              @close="selectedCategory = ''; handleCategorySelect()"
            >
              {{ selectedCategory }}
            </el-tag>
            <el-tag
              v-if="searchKeyword"
              closable
              type="info"
              effect="light"
              @close="searchKeyword = ''; handleSearch()"
            >
              "{{ searchKeyword }}"
            </el-tag>
            <el-tag
              v-if="selectedFileType"
              closable
              type="success"
              effect="light"
              @close="selectedFileType = ''; handleFilterChange()"
            >
              {{ fileTypeOptions.find(o => o.value === selectedFileType)?.label }}
            </el-tag>
            <el-button
              link
              type="primary"
              size="small"
              class="clear-all-btn"
              @click="clearAllFilters"
            >
              清除全部
            </el-button>
          </div>
        </div>

        <!-- Document Grid -->
        <div class="content-area" v-loading="loading">
          <div v-if="documents.length === 0" class="empty-state">
            <div class="empty-illustration">
              <el-icon :size="40"><Document /></el-icon>
            </div>
            <h3 class="empty-title">暂无文档</h3>
            <p class="empty-description">该分类下还没有文档</p>
          </div>

          <div v-else class="documents-grid">
            <DocCard
              v-for="(doc, index) in documents"
              :key="doc.id"
              :document="doc"
              :style="{ animationDelay: `${index * 30}ms` }"
              class="doc-card-animate"
              @preview="handlePreview(doc)"
              @download="handleDownloadDocument"
              @delete="handleDeleteDocument"
            />
          </div>

          <!-- Pagination -->
          <div v-if="total > pageSize" class="pagination-container">
            <el-pagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[12, 24, 48]"
              layout="prev, pager, next, sizes"
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
      class="preview-drawer"
    >
      <div class="drawer-header">
        <h3 class="drawer-title">{{ selectedDocument?.name }}</h3>
        <div class="drawer-actions">
          <button class="icon-button" @click="toggleDrawerSize">
            <el-icon><FullScreen /></el-icon>
          </button>
          <button class="icon-button" @click="previewVisible = false">
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </div>
      <div class="drawer-body">
        <DocPreview :document="selectedDocument" />
      </div>
    </el-drawer>

    <!-- Upload Dialog -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传文档"
      width="480px"
      :close-on-click-modal="false"
      class="upload-dialog"
    >
      <div class="upload-dialog-content">
        <!-- Upload Area -->
        <div
          ref="uploadAreaRef"
          class="upload-area"
          :class="{ 'is-dragover': isDragover }"
          @click="triggerFileInput"
          @dragover.prevent="isDragover = true"
          @dragleave.prevent="isDragover = false"
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInputRef"
            type="file"
            accept=".pdf,.docx,.doc,.md,.markdown"
            style="display: none"
            @change="handleFileSelect"
          >
          <div class="upload-area-content">
            <el-icon class="upload-icon" :size="48"><Upload /></el-icon>
            <p class="upload-text">
              <span v-if="!selectedFile">点击或拖拽文件到此处上传</span>
              <span v-else class="selected-file">{{ selectedFile.name }}</span>
            </p>
            <p class="upload-hint">支持 PDF、Word、Markdown 格式，最大 50MB</p>
          </div>
        </div>

        <!-- Category Selection -->
        <div class="visibility-section">
          <label class="visibility-label">文档分类</label>
          <el-select v-model="selectedCategoryForUpload" placeholder="请选择分类" class="visibility-select">
            <el-option
              v-for="cat in categories"
              :key="cat.name"
              :label="cat.name"
              :value="cat.name"
            />
          </el-select>
        </div>

        <!-- Visibility Selection -->
        <div class="visibility-section">
          <label class="visibility-label">文档可见性</label>
          <el-select v-model="selectedVisibility" placeholder="请选择可见性" class="visibility-select">
            <el-option
              v-for="option in visibilityOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            >
              <div class="visibility-option">
                <el-icon class="visibility-icon" :size="16">
                  <component :is="option.icon" />
                </el-icon>
                <span>{{ option.label }}</span>
              </div>
            </el-option>
          </el-select>
          <p class="visibility-desc">{{ currentVisibilityDesc }}</p>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeUploadDialog">取消</el-button>
          <el-button
            type="primary"
            :disabled="!selectedFile || !selectedCategoryForUpload || uploading"
            :loading="uploading"
            @click="handleUploadSubmit"
          >
            {{ uploading ? '上传中' : '确认上传' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Close, Document, FullScreen, Plus, Loading, Upload, Lock, OfficeBuilding, View } from '@element-plus/icons-vue'
import CategoryTree from '@/components/document/CategoryTree.vue'
import DocCard from '@/components/document/DocCard.vue'
import DocPreview from '@/components/document/DocPreview.vue'
import { getDocumentsApi, getCategoriesApi, uploadDocumentApi, deleteDocumentApi, downloadDocumentApi } from '@/api/document'
import type { Document as DocType, Category } from '@/api/document'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()

const loading = ref(false)
const uploading = ref(false)
const fileInputRef = ref<HTMLInputElement>()
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

const fileTypeOptions = [
  { value: '', label: '全部' },
  { value: 'pdf', label: 'PDF' },
  { value: 'docx', label: 'Word' },
  { value: 'md', label: 'Markdown' },
]

// Upload dialog related
const uploadDialogVisible = ref(false)
const selectedFile = ref<File | null>(null)
const selectedVisibility = ref('public')
const selectedCategoryForUpload = ref('')
const isDragover = ref(false)

const visibilityOptions = [
  { value: 'public', label: '公共', icon: 'View', desc: '所有人可见' },
  { value: 'department', label: '部门', icon: 'OfficeBuilding', desc: '同部门用户可见' },
  { value: 'private', label: '仅自己', icon: 'Lock', desc: '仅自己可见' },
]

const currentVisibilityDesc = computed(() => {
  const option = visibilityOptions.find(o => o.value === selectedVisibility.value)
  return option?.desc || ''
})

const previewSize = computed(() => isWideDrawer.value ? '85%' : '65%')

const toggleDrawerSize = () => {
  isWideDrawer.value = !isWideDrawer.value
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      category: selectedCategory.value || undefined,
      keyword: searchKeyword.value || undefined,
      file_type: selectedFileType.value || undefined,
    }
    console.log('Loading documents with params:', params)
    const { data } = await getDocumentsApi(params)
    if (data.data) {
      documents.value = data.data.items
      total.value = data.data.total
    }
  } catch {
    // 模拟数据 - 支持筛选
    const mockDocuments = [
      { id: '1', name: '产品使用手册 v2.0.pdf', category: '产品文档', file_type: 'pdf', file_size: 2457600, chunk_count: 45, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '2', name: '技术架构设计文档.docx', category: '技术文档', file_type: 'docx', file_size: 1843200, chunk_count: 32, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '3', name: '员工手册 2024 版.pdf', category: '规章制度', file_type: 'pdf', file_size: 3174400, chunk_count: 58, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '4', name: '培训资料 - 新员工入职.md', category: '培训资料', file_type: 'md', file_size: 45000, chunk_count: 12, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '5', name: 'API 接口文档.pdf', category: '技术文档', file_type: 'pdf', file_size: 1200000, chunk_count: 28, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: '6', name: '产品路线图 2024.pdf', category: '产品文档', file_type: 'pdf', file_size: 3200000, chunk_count: 15, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ]

    // 应用筛选条件
    let filtered = mockDocuments
    if (selectedFileType.value) {
      filtered = filtered.filter(doc => doc.file_type === selectedFileType.value)
    }
    if (selectedCategory.value) {
      filtered = filtered.filter(doc => doc.category === selectedCategory.value)
    }
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      filtered = filtered.filter(doc => doc.name.toLowerCase().includes(keyword))
    }

    documents.value = filtered
    total.value = filtered.length
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const { data } = await getCategoriesApi()
    if (data.data?.categories) {
      categories.value = data.data.categories
    }
  } catch {
    categories.value = [
      { name: '产品文档', count: 0 },
      { name: '技术文档', count: 0 },
      { name: '规章制度', count: 0 },
      { name: '培训资料', count: 0 },
      { name: '流程规范', count: 0 },
      { name: '其他', count: 0 },
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

const clearAllFilters = () => {
  selectedCategory.value = ''
  searchKeyword.value = ''
  selectedFileType.value = ''
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

const handleDownloadDocument = (doc: DocType) => {
  const downloadUrl = downloadDocumentApi(doc.id)
  // Create a temporary link and trigger download
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = doc.name
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('开始下载')
}

const handleDeleteDocument = async (doc: DocType) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${doc.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteDocumentApi(doc.id)
    ElMessage.success('文档删除成功')

    // Refresh document list
    await loadDocuments()
    // Refresh categories count
    await loadCategories()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

// Upload dialog methods
const openUploadDialog = () => {
  uploadDialogVisible.value = true
  selectedFile.value = null
  selectedVisibility.value = 'public'
  selectedCategoryForUpload.value = categories.value.length > 0 ? categories.value[0].name : ''
}

const closeUploadDialog = () => {
  uploadDialogVisible.value = false
  selectedFile.value = null
  selectedVisibility.value = 'public'
  selectedCategoryForUpload.value = ''
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  // Validate file type
  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/markdown',
    'text/x-markdown',
    'text/plain'
  ]
  const allowedExtensions = ['.pdf', '.docx', '.doc', '.md', '.markdown']
  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()

  if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
    ElMessage.error('不支持的文件类型，请上传 PDF、Word 或 Markdown 文件')
    target.value = ''
    return
  }

  // Validate file size (max 50MB)
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小超过 50MB 限制')
    target.value = ''
    return
  }

  selectedFile.value = file
  target.value = '' // Reset input so same file can be selected again
}

const handleDrop = (event: DragEvent) => {
  isDragover.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    const file = files[0]

    // Validate file type
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.md', '.markdown']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()

    if (!allowedExtensions.includes(fileExtension)) {
      ElMessage.error('不支持的文件类型，请上传 PDF、Word 或 Markdown 文件')
      return
    }

    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      ElMessage.error('文件大小超过 50MB 限制')
      return
    }

    selectedFile.value = file
  }
}

const handleUploadSubmit = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('visibility', selectedVisibility.value)
  formData.append('category', selectedCategoryForUpload.value || '其他')

  try {
    const { data } = await uploadDocumentApi(formData)
    if (data.data?.id) {
      ElMessage.success('文档上传成功')
      closeUploadDialog()
      // Refresh document list and categories count
      await loadDocuments()
      await loadCategories()
    } else {
      ElMessage.error(data.message || '上传失败')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '上传失败，请稍后重试')
  } finally {
    uploading.value = false
  }
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
// Apple Design System Variables
:root {
  --system-blue: #007AFF;
  --system-blue-hover: #0056CC;
  --system-gray: #8E8E93;
  --system-gray2: #AEAEB2;
  --system-gray3: #C7C7CC;
  --system-gray4: #D1D1D6;
  --system-gray5: #E5E5EA;
  --system-gray6: #F2F2F7;
  --system-background: #FFFFFF;
  --secondary-background: #F5F5F7;
  --tertiary-background: #FFFFFF;
  --separator: #E5E5EA;
  --text-primary: #000000;
  --text-secondary: #6E6E73;
  --text-tertiary: #8E8E93;
}

// Page Layout
.documents-page {
  min-height: 100vh;
  background: var(--secondary-background);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.documents-container {
  display: flex;
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px 40px 40px;
  gap: 32px;

  @media (max-width: 1024px) {
    padding: 20px 24px 32px;
    gap: 24px;
  }

  @media (max-width: 768px) {
    flex-direction: column;
    padding: 16px;
  }
}

// Sidebar
.sidebar {
  width: 240px;
  flex-shrink: 0;

  @media (max-width: 768px) {
    width: 100%;
  }
}

// Main Content
.main-content {
  flex: 1;
  min-width: 0;
}

// Page Header
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 0.5px solid var(--separator);

  @media (max-width: 640px) {
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;
    padding-bottom: 20px;
  }
}

.header-content {
  .page-title {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.021em;
    color: var(--text-primary);
    margin: 0 0 6px;
    line-height: 1.2;
  }

  .page-subtitle {
    font-size: 15px;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.4;
  }
}

.header-actions {
  flex-shrink: 0;
}

.primary-button {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 28px;
  background: linear-gradient(135deg, #007AFF 0%, #0056CC 100%);
  color: white;
  border: none;
  border-radius: 980px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 4px 12px rgba(0, 122, 255, 0.4),
    0 8px 24px rgba(0, 122, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);

  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #007AFF 0%, #004499 100%);
    transform: translateY(-3px) scale(1.02);
    box-shadow:
      0 8px 20px rgba(0, 122, 255, 0.5),
      0 16px 32px rgba(0, 122, 255, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.25);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
    box-shadow:
      0 1px 4px rgba(0, 122, 255, 0.3),
      inset 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: none;
  }

  .el-icon {
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.1));
  }
}

// Control Bar
.control-bar {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 20px;
}

// Search Container
.search-container {
  max-width: 480px;
}

.search-field {
  position: relative;
  display: flex;
  align-items: center;
  background: #FAFAFA;
  border: 1px solid #D1D1D6;
  border-radius: 10px;
  padding: 0 12px;
  height: 40px;
  transition: all 0.2s ease;
  box-shadow:
    inset 0 1px 2px rgba(0, 0, 0, 0.06),
    0 1px 0 rgba(255, 255, 255, 0.8);

  &:hover {
    background: #F8F8F8;
    border-color: #BDBDBD;
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.08),
      0 1px 0 rgba(255, 255, 255, 0.8);
  }

  &:focus-within {
    background: #FFFFFF;
    border-color: var(--system-blue);
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.04),
      0 0 0 3px rgba(0, 122, 255, 0.12);
  }

  .search-icon {
    color: #6E6E73;
    margin-right: 10px;
    flex-shrink: 0;
    transition: color 0.2s ease;
  }

  &:focus-within .search-icon {
    color: #0071E3;
  }

  &:hover .search-icon {
    color: #48484F;
  }

  input {
    flex: 1;
    border: none;
    background: transparent;
    font-size: 15px;
    color: #1D1D1F;
    outline: none;
    padding: 0;
    height: 100%;

    &::placeholder {
      color: #9E9EA6;
    }
  }

  .clear-button {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: none;
    background: var(--system-gray5);
    color: var(--text-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.15s ease;

    &:hover {
      background: var(--system-gray4);
      color: var(--text-secondary);
    }
  }
}

// Filter Container
.filter-container {
  display: flex;
  align-items: center;
  gap: 24px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

// Segmented Control (Apple Style)
.segmented-control {
  display: inline-flex;
  background: var(--system-gray6);
  border-radius: 8px;
  padding: 2px;
  gap: 2px;
}

.segment-button {
  padding: 6px 14px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(.active) {
    color: var(--text-primary);
  }

  &.active {
    background: var(--system-background);
    color: var(--text-primary);
    box-shadow: 0 0.5px 2px rgba(0, 0, 0, 0.08);
  }
}

// Results Bar
.results-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 0 4px;

  @media (max-width: 640px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

.results-count {
  font-size: 13px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.active-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;

  .el-tag {
    border-radius: 6px;
    font-size: 13px;
    height: 28px;
    padding: 0 10px;
    font-weight: 500;

    :deep(.el-tag__close) {
      font-size: 12px;
      color: inherit;
      opacity: 0.7;
      transition: opacity 0.2s;

      &:hover {
        opacity: 1;
        background: transparent;
        color: inherit;
      }
    }
  }

  .clear-all-btn {
    margin-left: 4px;
    font-size: 13px;
    font-weight: 500;

    &:hover {
      opacity: 0.8;
    }
  }
}

// Content Area
.content-area {
  min-height: 400px;
}

// Empty State
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 24px;
  text-align: center;
}

.empty-illustration {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  background: var(--system-gray6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--system-gray);
  margin-bottom: 20px;
}

.empty-title {
  font-size: 19px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
}

.empty-description {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0;
}

// Documents Grid
.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.doc-card-animate {
  animation: fadeInUp 0.4s ease-out forwards;
  opacity: 0;
  transform: translateY(12px);
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// Pagination
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 48px;
  padding-top: 24px;
  border-top: 0.5px solid var(--separator);
}

// Rotating Animation
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// Preview Drawer
.preview-drawer {
  :deep(.el-drawer__body) {
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
  border-bottom: 0.5px solid var(--separator);
  background: var(--secondary-background);
}

.drawer-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 16px;
}

.drawer-actions {
  display: flex;
  gap: 8px;
}

.icon-button {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--system-gray5);
    color: var(--text-primary);
  }
}

.drawer-body {
  flex: 1;
  overflow: hidden;
  background: var(--system-background);
}

// Upload Dialog Styles
.upload-dialog {
  :deep(.el-dialog) {
    border-radius: 28px !important;
    overflow: hidden;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  }

  :deep(.el-overlay-dialog) {
    border-radius: 28px;
  }

  :deep(.el-dialog__header) {
    padding: 24px 24px 16px;
    margin: 0;
  }

  :deep(.el-dialog__title) {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
  }

  :deep(.el-dialog__body) {
    padding: 16px 24px 24px;
  }

  :deep(.el-dialog__footer) {
    padding: 16px 24px 24px;
  }

  .upload-dialog-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
}

.upload-area {
  border: 2px dashed var(--system-gray4);
  border-radius: 16px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--system-gray6);

  &:hover,
  &.is-dragover {
    border-color: var(--system-blue);
    background: rgba(0, 122, 255, 0.05);
  }
}

.upload-area-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.upload-icon {
  color: var(--system-gray2);
  transition: color 0.2s ease;
}

.upload-area:hover .upload-icon,
.upload-area.is-dragover .upload-icon {
  color: var(--system-blue);
}

.upload-text {
  margin: 0;
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 500;

  .selected-file {
    color: var(--system-blue);
  }
}

.upload-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-tertiary);
}

// Visibility Section
.visibility-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.visibility-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.visibility-select {
  width: 100%;

  :deep(.el-input__wrapper) {
    border-radius: 8px;
  }
}

.visibility-option {
  display: flex;
  align-items: center;
  gap: 8px;

  .visibility-icon {
    color: var(--text-secondary);
  }
}

.visibility-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--text-tertiary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
