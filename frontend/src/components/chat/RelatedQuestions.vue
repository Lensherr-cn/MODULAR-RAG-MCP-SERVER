<template>
  <div class="apple-related-questions">
    <div class="related-header">
      <el-icon :size="14"><Lightning /></el-icon>
      <span>相关问题</span>
    </div>
    <div class="related-list">
      <button
        v-for="(question, index) in questions"
        :key="index"
        class="related-item"
        @click="handleClick(question)"
      >
        <span>{{ question }}</span>
        <el-icon :size="12"><ArrowRight /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Lightning, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps<{
  questions: string[]
}>()

const emit = defineEmits<{
  select: [question: string]
}>()

const handleClick = (question: string) => {
  emit('select', question)
}
</script>

<style scoped lang="scss">
.apple-related-questions {
  .related-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--apple-text-secondary);
    margin-bottom: 10px;
  }

  .related-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .related-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    background: var(--apple-accent-light);
    border: 1px solid transparent;
    border-radius: var(--apple-radius-full);
    font-size: 13px;
    color: var(--apple-accent);
    cursor: pointer;
    transition: all var(--apple-transition-fast);

    .el-icon {
      opacity: 0;
      transform: translateX(-4px);
      transition: all var(--apple-transition-fast);
    }

    &:hover {
      background: var(--apple-accent);
      color: white;
      border-color: var(--apple-accent);

      .el-icon {
        opacity: 1;
        transform: translateX(0);
      }
    }
  }
}
</style>
