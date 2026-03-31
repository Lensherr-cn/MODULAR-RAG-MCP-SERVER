<template>
  <header class="apple-header" :class="{ 'scrolled': isScrolled }">
    <div class="header-content">
      <!-- Logo -->
      <div class="header-brand" @click="router.push('/')">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="brand-text">Knowledge</span>
      </div>

      <!-- Navigation -->
      <nav class="header-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ 'active': route.path === item.path }"
        >
          <el-icon :size="18">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- User Actions -->
      <div class="header-actions">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown trigger="click" placement="bottom-end" :offset="8">
            <button class="user-button">
              <div class="user-avatar">
                <img
                  v-if="userStore.userProfile?.avatar"
                  :src="userStore.userProfile.avatar"
                  alt="Avatar"
                >
                <span v-else class="avatar-initials">
                  {{ getInitials(userStore.userProfile?.username) }}
                </span>
              </div>
              <span class="user-name">{{ userStore.userProfile?.username || '用户' }}</span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu class="apple-dropdown">
                <div class="dropdown-header">
                  <span class="dropdown-title">{{ userStore.userProfile?.username }}</span>
                  <span class="dropdown-subtitle">{{ userStore.userProfile?.email }}</span>
                </div>
                <el-dropdown-item @click="router.push('/profile')">
                  <el-icon><User /></el-icon>
                  <span>个人中心</span>
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <button class="auth-button" @click="handleLogin">
            登录
          </button>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  HomeFilled,
  ChatDotRound,
  Document,
  User,
  ArrowDown,
  SwitchButton
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isScrolled = ref(false)

const navItems = [
  { path: '/', label: '首页', icon: HomeFilled },
  { path: '/chat', label: '问答', icon: ChatDotRound },
  { path: '/documents', label: '文档', icon: Document },
]

const handleScroll = () => {
  isScrolled.value = window.scrollY > 10
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const getInitials = (name?: string) => {
  if (!name) return 'U'
  return name.slice(0, 2).toUpperCase()
}

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/')
}

const handleLogin = () => {
  // 这里可以实现登录逻辑
  ElMessage.info('登录功能开发中')
}
</script>

<style scoped lang="scss">
.apple-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: 52px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid transparent;
  transition: all var(--apple-transition-base);

  &.scrolled {
    background: rgba(255, 255, 255, 0.85);
    border-bottom-color: var(--apple-border);
  }

  @media (prefers-color-scheme: dark) {
    background: rgba(0, 0, 0, 0.72);

    &.scrolled {
      background: rgba(0, 0, 0, 0.85);
    }
  }
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

/* Brand */
.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 0;
  transition: opacity var(--apple-transition-fast);

  &:hover {
    opacity: 0.8;
  }

  .brand-icon {
    width: 28px;
    height: 28px;
    color: var(--apple-accent);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .brand-text {
    font-family: var(--apple-font-display);
    font-size: 18px;
    font-weight: 600;
    letter-spacing: -0.021em;
    color: var(--apple-text-primary);
  }
}

/* Navigation */
.header-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--apple-radius-full);
  font-size: 14px;
  font-weight: 500;
  color: var(--apple-text-secondary);
  text-decoration: none;
  transition: all var(--apple-transition-fast);

  &:hover {
    background: var(--apple-border-light);
    color: var(--apple-text-primary);
  }

  &.active {
    background: var(--apple-accent-light);
    color: var(--apple-accent);
  }

  .el-icon {
    transition: transform var(--apple-transition-fast);
  }

  &:hover .el-icon {
    transform: scale(1.1);
  }
}

/* User Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-button {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 4px 4px 4px;
  padding-right: 12px;
  background: var(--apple-bg-tertiary);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-full);
  cursor: pointer;
  transition: all var(--apple-transition-fast);

  &:hover {
    background: var(--apple-border);
    border-color: var(--apple-text-tertiary);
  }

  .user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    overflow: hidden;
    background: linear-gradient(135deg, var(--apple-accent), #5856d6);
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .avatar-initials {
      font-size: 12px;
      font-weight: 600;
      color: white;
    }
  }

  .user-name {
    font-size: 14px;
    font-weight: 500;
    color: var(--apple-text-primary);
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .dropdown-icon {
    font-size: 12px;
    color: var(--apple-text-tertiary);
    transition: transform var(--apple-transition-fast);
  }

  &:hover .dropdown-icon {
    transform: translateY(2px);
  }
}

.auth-button {
  padding: 8px 20px;
  background: var(--apple-accent);
  color: white;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: var(--apple-radius-full);
  cursor: pointer;
  transition: all var(--apple-transition-fast);

  &:hover {
    background: var(--apple-accent-hover);
    transform: scale(1.02);
  }
}

/* Dropdown Customization */
:deep(.apple-dropdown) {
  padding: 8px !important;
  min-width: 200px;

  .dropdown-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--apple-border);
    margin-bottom: 4px;

    .dropdown-title {
      display: block;
      font-size: 14px;
      font-weight: 600;
      color: var(--apple-text-primary);
    }

    .dropdown-subtitle {
      display: block;
      font-size: 12px;
      color: var(--apple-text-secondary);
      margin-top: 2px;
    }
  }

  .el-dropdown-menu__item {
    padding: 10px 14px !important;
    font-size: 14px !important;
    border-radius: 8px !important;
    display: flex;
    align-items: center;
    gap: 10px;

    .el-icon {
      font-size: 16px;
      color: var(--apple-text-secondary);
    }

    &:hover {
      background: var(--apple-bg-tertiary) !important;
    }

    &.is-divided {
      margin-top: 4px;
      padding-top: 10px;
      border-top: 1px solid var(--apple-border);
    }
  }
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }

  .brand-text {
    display: none;
  }

  .header-nav {
    position: static;
    transform: none;
  }

  .nav-link span {
    display: none;
  }

  .user-name {
    display: none;
  }
}
</style>
