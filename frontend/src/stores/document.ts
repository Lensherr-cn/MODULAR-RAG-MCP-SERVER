import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Document, Category } from '@/api/document'

export const useDocumentStore = defineStore('document', () => {
  // 文档列表
  const documents = ref<Document[]>([])
  const total = ref(0)

  // 分类列表
  const categories = ref<Category[]>([])

  // 当前选中的分类
  const selectedCategory = ref<string>('')

  // 搜索关键词
  const searchKeyword = ref('')

  // 加载状态
  const isLoading = ref(false)

  // 设置分类
  function setCategory(category: string) {
    selectedCategory.value = category
  }

  // 设置搜索关键词
  function setSearchKeyword(keyword: string) {
    searchKeyword.value = keyword
  }

  // 更新文档列表
  function setDocuments(docs: Document[], totalCount: number) {
    documents.value = docs
    total.value = totalCount
  }

  // 设置分类列表
  function setCategories(cats: Category[]) {
    categories.value = cats
  }

  // 清除文档列表
  function clearDocuments() {
    documents.value = []
    total.value = 0
  }

  return {
    documents,
    total,
    categories,
    selectedCategory,
    searchKeyword,
    isLoading,
    setCategory,
    setSearchKeyword,
    setDocuments,
    setCategories,
    clearDocuments
  }
})
