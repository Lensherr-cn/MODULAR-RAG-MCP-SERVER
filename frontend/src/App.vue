<script setup lang="ts">
import AppHeader from './components/common/AppHeader.vue'
</script>

<template>
  <div class="apple-app">
    <AppHeader />
    <main class="apple-main">
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
