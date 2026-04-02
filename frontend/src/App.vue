<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/common/AppHeader.vue'

const route = useRoute()
const showHeader = computed(() => !route.meta.public)
</script>

<template>
  <div class="apple-app">
    <AppHeader v-if="showHeader" />
    <main class="apple-main" :class="{ 'no-header': !showHeader }">
      <router-view v-slot="{ Component }">
        <transition name="apple-page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped lang="scss">
.apple-app {
  min-height: 100vh;
  background: var(--apple-bg-secondary);
  display: flex;
  flex-direction: column;
}

.apple-main {
  flex: 1;
  padding-top: 52px; /* Header height */
}

.apple-main.no-header {
  padding-top: 0;
}

/* Page Transition Animation */
.apple-page-enter-active,
.apple-page-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.apple-page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.apple-page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
