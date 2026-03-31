import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserProfile } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  // 用户信息
  const userProfile = ref<UserProfile | null>(null)

  // 登录状态
  const isLoggedIn = ref(false)

  // Token
  const token = ref<string | null>(null)

  // 设置用户信息
  function setUserProfile(profile: UserProfile) {
    userProfile.value = profile
    isLoggedIn.value = true
  }

  // 设置 Token
  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  // 登出
  function logout() {
    userProfile.value = null
    isLoggedIn.value = false
    token.value = null
    localStorage.removeItem('token')
  }

  // 初始化用户状态
  function initUserState() {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      token.value = storedToken
      // 这里可以调用 API 获取用户信息
      // 暂时设置一个默认用户
      userProfile.value = {
        id: '1',
        username: 'User',
        created_at: new Date().toISOString()
      }
      isLoggedIn.value = true
    }
  }

  return {
    userProfile,
    isLoggedIn,
    token,
    setUserProfile,
    setToken,
    logout,
    initUserState
  }
})
