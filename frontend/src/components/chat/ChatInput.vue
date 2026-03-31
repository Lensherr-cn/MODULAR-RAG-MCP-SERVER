<template>
  <div class="apple-chat-input">
    <div class="input-wrapper">
      <div class="input-field">
        <textarea
          v-model="inputValue"
          :placeholder="placeholder"
          :disabled="disabled"
          rows="1"
          maxlength="2000"
          @keydown="handleKeydown"
          @input="autoResize"
          ref="textareaRef"
        ></textarea>
        <span v-if="inputValue.length > 0" class="char-count">{{ inputValue.length }}</span>
      </div>
      <button
        class="send-button"
        :class="{ 'active': canSend, 'loading': disabled }"
        :disabled="!canSend"
        @click="handleSend"
      >
        <el-icon v-if="!disabled" :size="18"><Promotion /></el-icon>
        <el-icon v-else class="is-loading"><Loading /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Promotion, Loading } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue?: string
  disabled?: boolean
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: [value: string]
}>()

const inputValue = ref(props.modelValue || '')
const textareaRef = ref<HTMLTextAreaElement>()

const canSend = computed(() => inputValue.value.trim().length > 0 && !props.disabled)

watch(() => props.modelValue, (val) => {
  if (val !== undefined) {
    inputValue.value = val
    nextTick(autoResize)
  }
})

watch(inputValue, (val) => {
  emit('update:modelValue', val)
})

const autoResize = () => {
  const textarea = textareaRef.value
  if (!textarea) return

  textarea.style.height = 'auto'
  const newHeight = Math.min(Math.max(textarea.scrollHeight, 52), 200)
  textarea.style.height = `${newHeight}px`
}

const handleSend = () => {
  const trimmed = inputValue.value.trim()
  if (!trimmed || props.disabled) return
  emit('send', trimmed)
  inputValue.value = ''
  nextTick(autoResize)
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<style scoped lang="scss">
.apple-chat-input {
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-xl);
  box-shadow: var(--apple-shadow-md);
  border: 1px solid var(--apple-border);
  transition: box-shadow var(--apple-transition-base);

  &:focus-within {
    box-shadow: 0 0 0 4px var(--apple-accent-light), var(--apple-shadow-md);
    border-color: var(--apple-accent);
  }
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 12px;
}

.input-field {
  flex: 1;
  position: relative;

  textarea {
    width: 100%;
    min-height: 52px;
    max-height: 200px;
    padding: 14px 16px;
    padding-right: 50px;
    border: none;
    background: transparent;
    font-family: var(--apple-font-text);
    font-size: 16px;
    line-height: 1.5;
    color: var(--apple-text-primary);
    resize: none;
    outline: none;
    overflow-y: auto;

    &::placeholder {
      color: var(--apple-text-tertiary);
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  .char-count {
    position: absolute;
    right: 12px;
    bottom: 14px;
    font-size: 12px;
    color: var(--apple-text-tertiary);
  }
}

.send-button {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: var(--apple-bg-tertiary);
  color: var(--apple-text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
  flex-shrink: 0;

  &.active {
    background: var(--apple-accent);
    color: white;

    &:hover {
      background: var(--apple-accent-hover);
      transform: scale(1.05);
    }
  }

  &.loading {
    background: var(--apple-bg-tertiary);
    color: var(--apple-text-tertiary);
    cursor: not-allowed;
  }

  &:disabled {
    cursor: not-allowed;
  }

  .el-icon.is-loading {
    animation: rotating 1s linear infinite;
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
