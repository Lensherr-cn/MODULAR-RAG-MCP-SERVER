<template>
  <div class="loading" v-if="loading">
    <el-icon class="is-loading" :size="size">
      <Loading />
    </el-icon>
    <span v-if="text" class="loading-text">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'

defineProps<{
  loading?: boolean
  text?: string
  size?: number
}>()
</script>

<style scoped lang="scss">
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #909399;

  .loading-text {
    font-size: 14px;
  }
}
</style>
