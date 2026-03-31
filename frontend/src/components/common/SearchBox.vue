<template>
  <div class="search-box">
    <el-input
      v-model="keyword"
      :placeholder="placeholder"
      :prefix-icon="Search"
      :size="size"
      clearable
      @keyup.enter="handleSearch"
    >
      <template #append>
        <el-button :icon="Search" @click="handleSearch">搜索</el-button>
      </template>
    </el-input>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps<{
  placeholder?: string
  size?: 'default' | 'small' | 'large'
  modelValue?: string
}>()

const emit = defineEmits<{
  search: [keyword: string]
}>()

const keyword = ref(props.modelValue || '')

const handleSearch = () => {
  emit('search', keyword.value)
}
</script>

<style scoped lang="scss">
.search-box {
  width: 100%;

  :deep(.el-input) {
    .el-input__wrapper {
      border-radius: 20px 0 0 20px;
    }

    .el-input-group__append {
      border-radius: 0 20px 20px 0;
      background: #409eff;
      color: #fff;

      &:hover {
        background: #66b1ff;
      }
    }
  }
}
</style>
