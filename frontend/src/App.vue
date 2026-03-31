<script setup lang="ts">
import AppHeader from './components/common/AppHeader.vue'
</script>

<template>
  <div class="app-wrapper">
    <AppHeader />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped lang="scss">
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.app-main {
  flex: 1;
  padding: 0;
}
</style>
