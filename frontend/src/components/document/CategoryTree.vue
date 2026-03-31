<template>
  <div class="apple-category-tree">
    <div class="tree-header">
      <el-icon :size="20"><FolderOpened /></el-icon>
      <span>文档分类</span>
    </div>
    <div class="tree-list">
      <button
        v-for="cat in categories"
        :key="cat.name"
        class="tree-item"
        :class="{ active: modelValue === cat.name }"
        @click="handleSelect(cat.name)"
      >
        <div class="item-icon">
          <el-icon :size="16"><Folder /></el-icon>
        </div>
        <span class="item-label">{{ cat.name }}</span>
        <span class="item-count">{{ cat.count }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FolderOpened, Folder } from '@element-plus/icons-vue'
import type { Category } from '@/api/document'

const props = defineProps<{
  categories: Category[]
  modelValue?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  select: [value: string]
}>()

const handleSelect = (name: string) => {
  const newValue = props.modelValue === name ? '' : name
  emit('update:modelValue', newValue)
  emit('select', newValue)
}
</script>

<style scoped lang="scss">
.apple-category-tree {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  padding: 20px;
  box-shadow: var(--apple-shadow-sm);
}

.tree-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--apple-text-primary);
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--apple-border);

  .el-icon {
    color: var(--apple-accent);
  }
}

.tree-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tree-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: var(--apple-radius-md);
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
  text-align: left;

  &:hover {
    background: var(--apple-bg-tertiary);
  }

  &.active {
    background: var(--apple-accent-light);

    .item-icon {
      color: var(--apple-accent);
    }

    .item-label {
      color: var(--apple-accent);
      font-weight: 600;
    }

    .item-count {
      background: var(--apple-accent);
      color: white;
    }
  }

  .item-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: var(--apple-bg-tertiary);
    color: var(--apple-text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .item-label {
    flex: 1;
    font-size: 14px;
    color: var(--apple-text-primary);
  }

  .item-count {
    font-size: 12px;
    font-weight: 600;
    color: var(--apple-text-secondary);
    background: var(--apple-bg-tertiary);
    padding: 4px 10px;
    border-radius: 10px;
    transition: all var(--apple-transition-fast);
  }
}
</style>
