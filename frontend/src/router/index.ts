import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
      meta: { public: true }
    },
    {
      path: '/home',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true }
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('@/views/DocumentsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/documents/:id',
      name: 'document-detail',
      component: () => import('@/views/DocumentDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guestOnly: true }
    },
    {
      path: '/admin-register',
      name: 'admin-register',
      component: () => import('@/views/AdminRegisterView.vue'),
      meta: { guestOnly: true }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()

  // 公开页面无需认证
  if (to.meta.public) {
    next()
    return
  }

  // 初始化用户状态（如果尚未初始化）
  if (!userStore.userProfile) {
    await userStore.initUserState()
  }

  const isLoggedIn = userStore.isLoggedIn

  // 需要登录的页面，未登录则跳转到登录页
  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login')
    return
  }

  // 仅限游客访问的页面（如登录页），已登录则跳转到工作台
  if (to.meta.guestOnly && isLoggedIn) {
    next('/home')
    return
  }

  next()
})

export default router
