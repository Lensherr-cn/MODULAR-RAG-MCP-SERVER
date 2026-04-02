import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // 用户信息
  const userProfile = ref<UserInfo | null>(null)

  // 登录状态
  const isLoggedIn = computed(() => !!userProfile.value)

  // 用户角色
  const isAdmin = computed(() => userProfile.value?.role === 'admin')

  // 用户部门
  const userDepartment = computed(() => userProfile.value?.department)

  /**
   * 用户登录
   */
  async function login(credentials: { username: string; password: string; rememberMe?: boolean }) {
    try {
      const response = await authApi.login({
        username: credentials.username,
        password: credentials.password,
        rememberMe: credentials.rememberMe
      })

      if (response.data.code === 200) {
        userProfile.value = response.data.data.user
        return { success: true, user: response.data.data.user }
      }

      return { success: false, message: response.data.message || 'Login failed' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.message || 'Network error. Please try again.'
      }
    }
  }

  /**
   * 获取当前用户信息
   */
  async function fetchUserInfo() {
    try {
      const response = await authApi.getCurrentUser()
      if (response.data.code === 200) {
        userProfile.value = response.data.data
        return { success: true, user: response.data.data }
      }
      return { success: false }
    } catch (error) {
      userProfile.value = null
      return { success: false }
    }
  }

  /**
   * 登出
   */
  async function logout() {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      userProfile.value = null
    }
  }

  /**
   * 初始化用户状态
   * 在应用启动时调用，检查用户是否已登录
   */
  async function initUserState() {
    const result = await fetchUserInfo()
    return result.success
  }

  return {
    userProfile,
    isLoggedIn,
    isAdmin,
    userDepartment,
    login,
    logout,
    fetchUserInfo,
    initUserState
  }
})
