<template>
  <div class="register-container">
    <AuthBackground />

    <!-- 导航栏 -->
    <nav class="nav-bar">
      <div class="nav-content">
        <div class="logo">
          <svg class="logo-icon" viewBox="0 0 32 32" fill="none">
            <rect x="4" y="4" width="24" height="24" rx="6" fill="currentColor"/>
            <path d="M12 16L15 19L21 13" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="logo-text">知识库</span>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="register-card" :class="{ 'shake': shakeCard }">
        <!-- 卡片玻璃效果 -->
        <div class="glass-layer"></div>

        <div class="card-content">
          <!-- 标题 -->
          <div class="header">
            <h1 class="title">创建账户</h1>
            <p class="subtitle">加入我们，开始探索知识</p>
          </div>

          <!-- 注册表单 -->
          <form class="register-form" @submit.prevent="handleRegister" v-if="!isSuccess">
            <!-- 用户名输入 -->
            <div class="input-wrapper">
              <div class="input-field" :class="{ 'focused': usernameFocused, 'filled': username }">
                <label class="input-label">用户名</label>
                <input
                  v-model="username"
                  type="text"
                  required
                  autocomplete="username"
                  @focus="usernameFocused = true"
                  @blur="usernameFocused = false"
                />
                <div class="input-underline">
                  <div class="underline-fill"></div>
                </div>
              </div>
            </div>

            <!-- 邮箱输入 -->
            <div class="input-wrapper">
              <div class="input-field" :class="{ 'focused': emailFocused, 'filled': email }">
                <label class="input-label">邮箱</label>
                <input
                  v-model="email"
                  type="email"
                  required
                  autocomplete="email"
                  @focus="emailFocused = true"
                  @blur="emailFocused = false"
                />
                <div class="input-underline">
                  <div class="underline-fill"></div>
                </div>
              </div>
            </div>

            <!-- 部门输入 -->
            <div class="input-wrapper">
              <div class="input-field" :class="{ 'focused': departmentFocused, 'filled': department }">
                <label class="input-label">部门</label>
                <input
                  v-model="department"
                  type="text"
                  required
                  autocomplete="organization"
                  @focus="departmentFocused = true"
                  @blur="departmentFocused = false"
                />
                <div class="input-underline">
                  <div class="underline-fill"></div>
                </div>
              </div>
            </div>

            <!-- 密码输入 -->
            <div class="input-wrapper">
              <div class="input-field" :class="{ 'focused': passwordFocused, 'filled': password }">
                <label class="input-label">密码</label>
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  autocomplete="new-password"
                  @focus="passwordFocused = true"
                  @blur="passwordFocused = false"
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showPassword = !showPassword"
                >
                  <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                </button>
                <div class="input-underline">
                  <div class="underline-fill"></div>
                </div>
              </div>
            </div>

            <!-- 确认密码输入 -->
            <div class="input-wrapper">
              <div class="input-field" :class="{ 'focused': confirmPasswordFocused, 'filled': confirmPassword }">
                <label class="input-label">确认密码</label>
                <input
                  v-model="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  required
                  autocomplete="new-password"
                  @focus="confirmPasswordFocused = true"
                  @blur="confirmPasswordFocused = false"
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <svg v-if="showConfirmPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                </button>
                <div class="input-underline">
                  <div class="underline-fill"></div>
                </div>
              </div>
            </div>

            <!-- 注册按钮 -->
            <button type="submit" class="submit-button" :disabled="isLoading">
              <span class="button-text" :class="{ 'hidden': isLoading }">创建账户</span>
              <span class="button-loader" :class="{ 'visible': isLoading }">
                <svg viewBox="0 0 44 44">
                  <circle cx="22" cy="22" r="20" fill="none" stroke="currentColor" stroke-width="4"/>
                </svg>
              </span>
            </button>
          </form>

          <!-- 成功提示 -->
          <div v-else class="success-state">
            <div class="success-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <h2 class="success-title">注册成功</h2>
            <p class="success-message">账户已创建，正在跳转到登录页...</p>
          </div>

          <!-- 错误提示 -->
          <Transition name="slide-fade">
            <div v-if="errorMessage && !isSuccess" class="error-banner">
              <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <span>{{ errorMessage }}</span>
            </div>
          </Transition>
        </div>
      </div>

      <!-- 底部链接 -->
      <div class="footer">
        <p>已有账户？<router-link to="/login" class="login-link">立即登录</router-link></p>
        <p class="admin-register-line">
          <router-link to="/admin-register" class="admin-link">管理员/领导注册</router-link>
        </p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth'
import AuthBackground from '@/components/auth/AuthBackground.vue'

const router = useRouter()

const username = ref('')
const email = ref('')
const department = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const usernameFocused = ref(false)
const emailFocused = ref(false)
const departmentFocused = ref(false)
const passwordFocused = ref(false)
const confirmPasswordFocused = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const shakeCard = ref(false)
const isSuccess = ref(false)

const handleRegister = async () => {
  if (!username.value || !email.value || !department.value || !password.value || !confirmPassword.value) {
    errorMessage.value = '请填写所有字段'
    triggerShake()
    return
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致'
    triggerShake()
    return
  }

  if (password.value.length < 6) {
    errorMessage.value = '密码长度至少为6位'
    triggerShake()
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await authApi.register({
      username: username.value.trim(),
      email: email.value.trim(),
      department: department.value.trim(),
      password: password.value,
      role: 'user'
    })

    if (response.data.code === 200) {
      isSuccess.value = true
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } else {
      errorMessage.value = response.data.message || '注册失败'
      triggerShake()
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '网络错误，请重试'
    triggerShake()
  } finally {
    isLoading.value = false
  }
}

const triggerShake = () => {
  shakeCard.value = true
  setTimeout(() => {
    shakeCard.value = false
  }, 500)
}
</script>

<style scoped>
/* ===== Apple Design System ===== */
:root {
  --apple-blue: #007AFF;
  --apple-blue-hover: #0051D5;
  --apple-gray: #8E8E93;
  --apple-light-gray: #F5F5F7;
  --apple-dark: #1D1D1F;
  --apple-red: #FF3B30;
  --apple-green: #34C759;
  --glass-bg: rgba(255, 255, 255, 0.72);
  --glass-border: rgba(255, 255, 255, 0.5);
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 24px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 12px 48px rgba(0, 0, 0, 0.12);
}

/* ===== Container ===== */
.register-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #FAFAFA 0%, #F5F5F7 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
  position: relative;
  overflow: hidden;
}

/* ===== Navigation ===== */
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 20px 40px;
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: var(--apple-dark);
}

.logo-text {
  font-size: 21px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--apple-dark);
}

/* ===== Main Content ===== */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px 40px;
  position: relative;
  z-index: 10;
}

/* ===== Register Card (Glassmorphism) ===== */
.register-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  background: var(--glass-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-radius: 24px;
  border: 1px solid var(--glass-border);
  box-shadow:
    var(--shadow-lg),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  overflow: hidden;
  animation: cardEnter 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.register-card.shake {
  animation: shake 0.5s cubic-bezier(0.36, 0, 0.66, -0.56);
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-8px); }
  40% { transform: translateX(8px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}

.glass-layer {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.4) 0%,
    rgba(255, 255, 255, 0.1) 100%
  );
  pointer-events: none;
}

.card-content {
  position: relative;
  padding: 48px 40px;
}

/* ===== Header ===== */
.header {
  text-align: center;
  margin-bottom: 32px;
}

.title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--apple-dark);
  margin-bottom: 8px;
}

.subtitle {
  font-size: 15px;
  font-weight: 400;
  color: var(--apple-gray);
  line-height: 1.4;
}

/* ===== Form ===== */
.register-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-wrapper {
  position: relative;
}

.input-field {
  position: relative;
  display: flex;
  align-items: center;
}

.input-label {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  font-weight: 400;
  color: var(--apple-gray);
  pointer-events: none;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: left top;
}

.input-field.focused .input-label,
.input-field.filled .input-label {
  top: -8px;
  transform: translateY(0) scale(0.75);
  color: var(--apple-blue);
}

.input-field input {
  width: 100%;
  height: 48px;
  padding: 12px 0;
  background: transparent;
  border: none;
  font-size: 16px;
  font-weight: 400;
  color: var(--apple-dark);
  outline: none;
}

.input-underline {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.underline-fill {
  height: 100%;
  width: 0;
  background: var(--apple-blue);
  transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.input-field.focused .underline-fill {
  width: 100%;
}

.toggle-password {
  position: absolute;
  right: 0;
  width: 24px;
  height: 24px;
  padding: 0;
  background: none;
  border: none;
  color: var(--apple-gray);
  cursor: pointer;
  transition: color 0.2s;
}

.toggle-password:hover {
  color: var(--apple-dark);
}

/* ===== Submit Button ===== */
.submit-button {
  position: relative;
  height: 52px;
  margin-top: 8px;
  background: var(--apple-dark);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.2s;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.submit-button:hover:not(:disabled) {
  background: #000;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-text {
  display: block;
  transition: opacity 0.2s;
}

.button-text.hidden {
  opacity: 0;
}

.button-loader {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.button-loader.visible {
  opacity: 1;
}

.button-loader svg {
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

.button-loader circle {
  stroke-dasharray: 80;
  stroke-dashoffset: 60;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== Success State ===== */
.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 24px 0;
  animation: scaleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.success-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(52, 199, 89, 0.12);
  color: var(--apple-green);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.success-icon svg {
  width: 32px;
  height: 32px;
}

.success-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--apple-dark);
  margin-bottom: 8px;
}

.success-message {
  font-size: 15px;
  color: var(--apple-gray);
  line-height: 1.4;
}

/* ===== Error Banner ===== */
.error-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding: 16px;
  background: rgba(255, 59, 48, 0.08);
  border-radius: 12px;
  color: var(--apple-red);
  font-size: 14px;
  font-weight: 500;
}

.error-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* ===== Transitions ===== */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* ===== Footer ===== */
.footer {
  margin-top: 32px;
  text-align: center;
}

.footer p {
  font-size: 14px;
  font-weight: 400;
  color: var(--apple-gray);
}

.admin-register-line {
  margin-top: 8px;
}

.login-link,
.admin-link {
  color: var(--apple-blue);
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.2s;
}

.login-link:hover,
.admin-link:hover {
  opacity: 0.8;
}

/* ===== Responsive ===== */
@media (max-width: 480px) {
  .nav-bar {
    padding: 16px 20px;
  }

  .main-content {
    padding: 80px 16px 32px;
  }

  .card-content {
    padding: 36px 28px;
  }

  .title {
    font-size: 24px;
  }
}

/* ===== Dark Mode Support ===== */
@media (prefers-color-scheme: dark) {
  .register-container {
    background: linear-gradient(180deg, #000 0%, #1C1C1E 100%);
  }

  .logo-text,
  .title,
  .input-field input,
  .success-title {
    color: #fff;
  }

  .subtitle,
  .footer p,
  .success-message {
    color: #8E8E93;
  }

  .input-label {
    color: #8E8E93;
  }

  .input-underline {
    background: rgba(255, 255, 255, 0.1);
  }

  .register-card {
    background: rgba(30, 30, 30, 0.72);
    border-color: rgba(255, 255, 255, 0.1);
    box-shadow:
      0 12px 48px rgba(0, 0, 0, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .glass-layer {
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.1) 0%,
      rgba(255, 255, 255, 0.02) 100%
    );
  }

  .submit-button {
    background: #fff;
    color: #000;
  }

  .submit-button:hover:not(:disabled) {
    background: #f0f0f0;
  }
}

/* ===== Reduced Motion ===== */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
