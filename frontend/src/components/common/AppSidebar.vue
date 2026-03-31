<template>
  <aside class="app-sidebar">
    <el-menu
      :default-active="activeMenu"
      class="sidebar-menu"
      router
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
    >
      <el-menu-item index="/">
        <el-icon><HomeFilled /></el-icon>
        <span>首页</span>
      </el-menu-item>
      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <span>智能问答</span>
      </el-menu-item>
      <el-menu-item index="/documents">
        <el-icon><Document /></el-icon>
        <span>文档中心</span>
      </el-menu-item>
      <el-menu-item index="/profile">
        <el-icon><User /></el-icon>
        <span>个人中心</span>
      </el-menu-item>
    </el-menu>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, ChatDotRound, Document, User } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped lang="scss">
.app-sidebar {
  width: 200px;
  height: 100%;
  background: #304156;

  .sidebar-menu {
    border-right: none;
    height: 100%;

    :deep(.el-menu-item) {
      &:hover {
        background-color: #263445;
      }

      &.is-active {
        background-color: #409eff;
      }
    }
  }
}
</style>
