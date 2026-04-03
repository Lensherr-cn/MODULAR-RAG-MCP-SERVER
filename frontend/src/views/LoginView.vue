<template>
  <div class="login-container">
    <!-- 动态渐变背景 -->
    <div class="ambient-bg">
      <div class="gradient-blob blob-1"></div>
      <div class="gradient-blob blob-2"></div>
      <div class="gradient-blob blob-3"></div>
    </div>

    <!-- 导航栏 -->
    <nav class="nav-bar">
      <div class="nav-content">
        <div class="logo">
          <svg class="logo-icon" viewBox="0 0 32 32" fill="none">
            <rect x="4" y="4" width="24" height="24" rx="6" fill="currentColor"/>
            <path d="M12 16L15 19L21 13" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="logo-text">Knowledge Hub</span>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="login-card" :class="{ 'shake': shakeCard }">
        <!-- 卡片玻璃效果 -->
        <div class="glass-layer"></div>

        <div class="card-content">
          <!-- 标题 -->
          <div class="header">
            <h1 class="title">Sign In</h1>
            <p class="subtitle">Enter your credentials to access your account</p>
          </div>

          <!-- 登录表单 -->
          <form class="login-form" @submit.prevent="handleLogin">
            <!-- 用户名输入 -->
            <div class="input-wrapper">
              <div class="input-field" :class="{ 'focused': usernameFocused, 'filled': username }">
                <label class="input-label">Username</label>
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

            <!-- 密码输入 -->
            <div class="input-wrapper">
              <div class="input-field" :class="{ 'focused': passwordFocused, 'filled': password }">
                <label class="input-label">Password</label>
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  autocomplete="current-password"
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

            <!-- 记住我 -->
            <div class="options">
              <label class="checkbox-wrapper">
                <input type="checkbox" v-model="rememberMe" />
                <span class="checkbox">
                  <svg viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </span>
                <span class="checkbox-label">Remember me</span>
              </label>
              <a href="#" class="forgot-link">Forgot password?</a>
            </div>

            <!-- 登录按钮 -->
            <button type="submit" class="signin-button" :disabled="isLoading">
              <span class="button-text" :class="{ 'hidden': isLoading }">Sign In</span>
              <span class="button-loader" :class="{ 'visible': isLoading }">
                <svg viewBox="0 0 44 44">
                  <circle cx="22" cy="22" r="20" fill="none" stroke="currentColor" stroke-width="4"/>
                </svg>
              </span>
            </button>
          </form>

          <!-- 错误提示 -->
          <Transition name="slide-fade">
            <div v-if="errorMessage" class="error-banner">
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
        <p>Don't have an account? <a href="#" class="signup-link">Sign up</a></p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)
const usernameFocused = ref(false)
const passwordFocused = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const shakeCard = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    triggerShake()
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const result = await userStore.login({
      username: username.value,
      password: password.value,
      rememberMe: rememberMe.value
    })

    if (result.success) {
      router.push('/')
    } else {
      errorMessage.value = result.message || 'Authentication failed'
      triggerShake()
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'Network error. Please try again.'
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
  --glass-bg: rgba(255, 255, 255, 0.72);
  --glass-border: rgba(255, 255, 255, 0.5);
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 24px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 12px 48px rgba(0, 0, 0, 0.12);
}

/* ===== Container ===== */
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #FAFAFA 0%, #F5F5F7 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
  position: relative;
  overflow: hidden;
}

/* ===== Ambient Background ===== */
.ambient-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.gradient-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.blob-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #E8E4F3 0%, transparent 70%);
  top: -200px;
  right: -100px;
  animation-delay: 0s;
}

.blob-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #D4E5F7 0%, transparent 70%);
  bottom: -150px;
  left: -100px;
  animation-delay: -7s;
}

.blob-3 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #F2E4E8 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
  opacity: 0.3;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
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

/* ===== Login Card (Glassmorphism) ===== */
.login-card {
  position: relative;
  width: 100%;
  max-width: 380px;
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

.login-card.shake {
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
  margin-bottom: 40px;
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
.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
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

/* ===== Options ===== */
.options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.checkbox-wrapper input {
  display: none;
}

.checkbox {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  border: 1.5px solid rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.checkbox svg {
  width: 10px;
  height: 10px;
  color: white;
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.2s;
}

.checkbox-wrapper input:checked + .checkbox {
  background: var(--apple-blue);
  border-color: var(--apple-blue);
}

.checkbox-wrapper input:checked + .checkbox svg {
  opacity: 1;
  transform: scale(1);
}

.checkbox-label {
  font-size: 14px;
  font-weight: 400;
  color: var(--apple-dark);
}

.forgot-link {
  font-size: 14px;
  font-weight: 400;
  color: var(--apple-blue);
  text-decoration: none;
  transition: opacity 0.2s;
}

.forgot-link:hover {
  opacity: 0.8;
}

/* ===== Sign In Button ===== */
.signin-button {
  position: relative;
  height: 52px;
  margin-top: 16px;
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

.signin-button:hover:not(:disabled) {
  background: #000;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.signin-button:active:not(:disabled) {
  transform: translateY(0);
}

.signin-button:disabled {
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

.signup-link {
  color: var(--apple-blue);
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.2s;
}

.signup-link:hover {
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
  .login-container {
    background: linear-gradient(180deg, #000 0%, #1C1C1E 100%);
  }

  .gradient-blob {
    opacity: 0.2;
  }

  .blob-1 {
    background: radial-gradient(circle, #4A3F6B 0%, transparent 70%);
  }

  .blob-2 {
    background: radial-gradient(circle, #1E3A5F 0%, transparent 70%);
  }

  .blob-3 {
    background: radial-gradient(circle, #5B2838 0%, transparent 70%);
  }

  .logo-text,
  .title,
  .input-field input,
  .checkbox-label {
    color: #fff;
  }

  .subtitle,
  .footer p {
    color: #8E8E93;
  }

  .input-label {
    color: #8E8E93;
  }

  .input-underline {
    background: rgba(255, 255, 255, 0.1);
  }

  .login-card {
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

  .checkbox {
    border-color: rgba(255, 255, 255, 0.3);
  }

  .signin-button {
    background: #fff;
    color: #000;
  }

  .signin-button:hover:not(:disabled) {
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
