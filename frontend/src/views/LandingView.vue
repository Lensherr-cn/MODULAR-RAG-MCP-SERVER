<template>
  <div class="landing-page">
    <!-- 玻璃拟态导航栏 -->
    <nav class="landing-nav" :class="{ 'scrolled': isScrolled }">
      <div class="nav-content">
        <div class="nav-brand" @click="scrollToTop">
          <svg class="brand-icon" viewBox="0 0 32 32" fill="none">
            <rect x="4" y="4" width="24" height="24" rx="6" fill="currentColor"/>
            <path d="M12 16L15 19L21 13" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="brand-text">Knowledge Hub</span>
        </div>
        <div class="nav-actions">
          <button class="nav-cta" @click="goToLogin">开始使用</button>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section" ref="heroSection">
      <div class="hero-background">
        <div class="gradient-orb orb-1" :style="orb1Style"></div>
        <div class="gradient-orb orb-2" :style="orb2Style"></div>
        <div class="gradient-orb orb-3" :style="orb3Style"></div>
      </div>
      <div class="hero-content" :style="heroContentStyle">
        <h1 class="hero-title" ref="heroTitle">
          <span class="title-line">企业知识库</span>
          <span class="title-line">重新想象</span>
        </h1>
        <p class="hero-subtitle" ref="heroSubtitle">
          智能问答、文档管理、团队协作，<br>一站式知识管理解决方案。
        </p>
        <div class="hero-cta" ref="heroCta">
          <button class="cta-primary" @click="goToLogin">
            <span>立即体验</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </button>
          <button class="cta-secondary" @click="scrollToFeatures">
            <span>了解更多</span>
          </button>
        </div>
      </div>
      <div class="hero-scroll-indicator" @click="scrollToFeatures" :style="scrollIndicatorStyle">
        <div class="scroll-mouse">
          <div class="scroll-wheel"></div>
        </div>
        <span>向下滚动</span>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section" id="features" ref="featuresSection">
      <div class="section-header" ref="sectionHeader" :class="{ 'visible': sectionHeaderVisible }">
        <span class="section-label">核心功能</span>
        <h2 class="section-title">为团队打造的知识引擎</h2>
        <p class="section-desc">从文档管理到智能问答，让知识流动起来</p>
      </div>
      <div class="features-grid">
        <div
          class="feature-card"
          v-for="(feature, index) in features"
          :key="index"
          :ref="el => setFeatureRef(el, index)"
          :class="{ 'visible': featureVisible[index] }"
          :style="getFeatureStyle(index)"
        >
          <div class="feature-icon-wrapper" :class="feature.icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path v-if="feature.icon === 'chat'" d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7A8.38 8.38 0 0 1 4 11.5a8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
              <path v-if="feature.icon === 'document'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline v-if="feature.icon === 'document'" points="14 2 14 8 20 8"/>
              <path v-if="feature.icon === 'search'" d="M11 19A8 8 0 1 0 11 3a8 8 0 0 0 0 16z"/>
              <line v-if="feature.icon === 'search'" x1="21" y1="21" x2="16.65" y2="16.65"/>
              <path v-if="feature.icon === 'shield'" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-desc">{{ feature.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Showcase Section -->
    <section class="showcase-section" ref="showcaseSection">
      <div class="showcase-content">
        <div class="showcase-text" ref="showcaseText" :class="{ 'visible': showcaseTextVisible }">
          <span class="showcase-label">智能问答</span>
          <h2 class="showcase-title">像对话一样获取知识</h2>
          <p class="showcase-desc">
            基于大语言模型的智能问答系统，能够理解自然语言查询，
            从企业文档中精准提取答案，并标注信息来源。
          </p>
          <ul class="showcase-list">
            <li
              v-for="(item, index) in showcaseList"
              :key="index"
              :ref="el => setShowcaseItemRef(el, index)"
              :class="{ 'visible': showcaseItemsVisible[index] }"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span>{{ item }}</span>
            </li>
          </ul>
        </div>
        <div class="showcase-visual" ref="showcaseVisual" :class="{ 'visible': showcaseVisualVisible }">
          <div class="visual-card">
            <div class="chat-bubble">
              <p>如何申请年假？</p>
            </div>
            <div class="chat-bubble response">
              <p>根据《员工手册》第12章，年假申请流程如下：</p>
              <ol>
                <li>登录HR系统</li>
                <li>填写请假申请表</li>
                <li>提交直属领导审批</li>
              </ol>
              <span class="source">来源：员工手册 v2.1</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section" ref="statsSection">
      <div class="stats-grid">
        <div
          class="stat-item"
          v-for="(stat, index) in stats"
          :key="index"
          :ref="el => setStatRef(el, index)"
          :class="{ 'visible': statItemsVisible[index] }"
        >
          <span class="stat-number">{{ stat.number }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section" ref="ctaSection">
      <div class="cta-content" :class="{ 'visible': ctaVisible }">
        <h2 class="cta-title">准备好开始了吗？</h2>
        <p class="cta-desc">立即体验新一代企业知识管理平台</p>
        <button class="cta-button" @click="goToLogin">
          <span>立即开始</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="footer-content">
        <div class="footer-brand">
          <svg class="brand-icon" viewBox="0 0 32 32" fill="none">
            <rect x="4" y="4" width="24" height="24" rx="6" fill="currentColor"/>
            <path d="M12 16L15 19L21 13" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Knowledge Hub</span>
        </div>
        <p class="footer-copy">© 2026 Knowledge Hub. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ===== Scroll Progress Tracking =====
const scrollY = ref(0)
const viewportHeight = ref(window.innerHeight)

// Navigation scroll state
const isScrolled = ref(false)
const handleScroll = () => {
  scrollY.value = window.scrollY
  isScrolled.value = scrollY.value > 50
}

// Hero parallax and fade effects
const heroSection = ref<HTMLElement | null>(null)
const heroProgress = computed(() => {
  if (!heroSection.value) return 0
  const rect = heroSection.value.getBoundingClientRect()
  const progress = Math.max(0, Math.min(1, -rect.top / rect.height))
  return progress
})

const heroContentStyle = computed(() => {
  const progress = heroProgress.value
  return {
    opacity: 1 - progress * 1.5,
    transform: `translateY(${progress * 50}px) scale(${1 - progress * 0.1})`
  }
})

const scrollIndicatorStyle = computed(() => ({
  opacity: Math.max(0, 1 - heroProgress.value * 3)
}))

// Orb parallax effects
const orb1Style = computed(() => ({
  transform: `translate(${scrollY.value * 0.05}px, ${scrollY.value * -0.08}px) scale(${1 + scrollY.value * 0.0002})`
}))
const orb2Style = computed(() => ({
  transform: `translate(${scrollY.value * -0.03}px, ${scrollY.value * 0.05}px) scale(${1 + scrollY.value * 0.0001})`
}))
const orb3Style = computed(() => ({
  transform: `translate(-50%, calc(-50% + ${scrollY.value * 0.04}px)) scale(${1 + scrollY.value * 0.00015})`
}))

// ===== Section Refs & Visibility State =====
const featuresSection = ref<HTMLElement | null>(null)
const featureCards = ref<(HTMLElement | null)[]>([])
const showcaseItems = ref<(HTMLElement | null)[]>([])
const statItems = ref<(HTMLElement | null)[]>([])
const ctaSection = ref<HTMLElement | null>(null)
const sectionHeader = ref<HTMLElement | null>(null)
const showcaseText = ref<HTMLElement | null>(null)
const showcaseVisual = ref<HTMLElement | null>(null)

// Visibility states (for two-way fade in/out)
const sectionHeaderVisible = ref(false)
const featureVisible = ref<boolean[]>([false, false, false, false])
const showcaseItemsVisible = ref<boolean[]>([false, false, false, false])
const showcaseTextVisible = ref(false)
const showcaseVisualVisible = ref(false)
const statItemsVisible = ref<boolean[]>([false, false, false, false])
const ctaVisible = ref(false)

// Intersection ratios for hierarchical sizing effect
const featureRatios = ref<number[]>([0, 0, 0, 0])

const setFeatureRef = (el: any, index: number) => {
  if (el) featureCards.value[index] = el
}
const setShowcaseItemRef = (el: any, index: number) => {
  if (el) showcaseItems.value[index] = el
}
const setStatRef = (el: any, index: number) => {
  if (el) statItems.value[index] = el
}

// Dynamic feature card style based on intersection ratio
const getFeatureStyle = (index: number) => {
  const ratio = featureRatios.value[index] || 0
  // Scale from 0.85 to 1 based on visibility
  const scale = 0.85 + ratio * 0.15
  return {
    transform: `scale(${scale})`
  }
}

// Data
const features = [
  { icon: 'chat', title: '智能问答', desc: '基于 AI 的自然语言问答，快速获取精准答案' },
  { icon: 'document', title: '文档管理', desc: '支持多种格式，自动解析和智能分块' },
  { icon: 'search', title: '全文检索', desc: '强大的搜索引擎，秒级返回相关结果' },
  { icon: 'shield', title: '权限控制', desc: '多级权限管理，确保数据安全隔离' },
]

const showcaseList = [
  '自然语言理解',
  '多文档源支持',
  '答案溯源标注',
  '持续学习优化',
]

const stats = [
  { number: '10k+', label: '文档数量' },
  { number: '50k+', label: '问答次数' },
  { number: '99%', label: '满意度' },
  { number: '24/7', label: '全天候服务' },
]

// Navigation
const goToLogin = () => router.push('/login')
const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' })
const scrollToFeatures = () => {
  featuresSection.value?.scrollIntoView({ behavior: 'smooth' })
}

// ===== Intersection Observers for Scroll Animations =====
let observers: IntersectionObserver[] = []

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  window.addEventListener('resize', () => { viewportHeight.value = window.innerHeight })

  // Section header observer
  const headerObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      sectionHeaderVisible.value = entry.isIntersecting
    })
  }, { threshold: [0, 0.2, 0.5, 0.8, 1] })

  if (sectionHeader.value) headerObserver.observe(sectionHeader.value)
  observers.push(headerObserver)

  // Feature cards observer with ratio tracking for hierarchical effect
  featureCards.value.forEach((el, index) => {
    if (!el) return
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        featureVisible.value[index] = entry.isIntersecting
        featureRatios.value[index] = entry.intersectionRatio
      })
    }, {
      threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
      rootMargin: '-10% 0px -10% 0px'
    })
    observer.observe(el)
    observers.push(observer)
  })

  // Showcase text observer
  const showcaseTextObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      showcaseTextVisible.value = entry.isIntersecting
    })
  }, { threshold: [0, 0.25, 0.5, 0.75, 1] })

  if (showcaseText.value) showcaseTextObserver.observe(showcaseText.value)
  observers.push(showcaseTextObserver)

  // Showcase visual observer
  const showcaseVisualObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      showcaseVisualVisible.value = entry.isIntersecting
    })
  }, { threshold: [0, 0.25, 0.5, 0.75, 1] })

  if (showcaseVisual.value) showcaseVisualObserver.observe(showcaseVisual.value)
  observers.push(showcaseVisualObserver)

  // Showcase list items observer
  showcaseItems.value.forEach((el, index) => {
    if (!el) return
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        showcaseItemsVisible.value[index] = entry.isIntersecting
      })
    }, { threshold: [0, 0.5, 1] })
    observer.observe(el)
    observers.push(observer)
  })

  // Stats observer
  statItems.value.forEach((el, index) => {
    if (!el) return
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        statItemsVisible.value[index] = entry.isIntersecting
      })
    }, { threshold: [0, 0.5, 1] })
    observer.observe(el)
    observers.push(observer)
  })

  // CTA section observer
  const ctaObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      ctaVisible.value = entry.isIntersecting
    })
  }, { threshold: [0, 0.25, 0.5, 0.75, 1] })

  if (ctaSection.value) ctaObserver.observe(ctaSection.value)
  observers.push(ctaObserver)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  observers.forEach(obs => obs.disconnect())
})
</script>

<style scoped>
/* ===== Apple Design System ===== */
.landing-page {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
  color: #1d1d1f;
  background: #fafafa;
  overflow-x: hidden;
}

/* ===== Navigation ===== */
.landing-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  padding: 16px 0;
  transition: all 0.3s ease;
}

.landing-nav.scrolled {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-icon {
  width: 28px;
  height: 28px;
  color: #007aff;
}

.brand-text {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.nav-cta {
  padding: 10px 24px;
  background: #007aff;
  color: white;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-cta:hover {
  background: #0051d5;
  transform: scale(1.02);
}

/* ===== Hero Section ===== */
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 120px 24px 80px;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.5;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #e8e4f3, #d4e5f7);
  top: -200px;
  right: -100px;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #d4e5f7, #e8e4f3);
  bottom: -150px;
  left: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #f2e4e8, #e4d4f2);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
}

.hero-title {
  font-size: clamp(40px, 8vw, 72px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin-bottom: 24px;
}

.title-line {
  display: block;
  background: linear-gradient(135deg, #1d1d1f 0%, #434344 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: clamp(18px, 3vw, 24px);
  color: #6e6e73;
  line-height: 1.5;
  margin-bottom: 40px;
}

.hero-cta {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.cta-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 32px;
  background: #007aff;
  color: white;
  font-size: 17px;
  font-weight: 600;
  border: none;
  border-radius: 980px;
  cursor: pointer;
  transition: all 0.2s;
}

.cta-primary:hover {
  background: #0051d5;
  transform: scale(1.02);
}

.cta-primary svg {
  width: 20px;
  height: 20px;
}

.cta-secondary {
  padding: 16px 32px;
  background: transparent;
  color: #007aff;
  font-size: 17px;
  font-weight: 600;
  border: 2px solid #007aff;
  border-radius: 980px;
  cursor: pointer;
  transition: all 0.2s;
}

.cta-secondary:hover {
  background: rgba(0, 122, 255, 0.1);
}

.hero-scroll-indicator {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #86868b;
  font-size: 12px;
}

.scroll-mouse {
  width: 26px;
  height: 40px;
  border: 2px solid #86868b;
  border-radius: 13px;
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

.scroll-wheel {
  width: 4px;
  height: 8px;
  background: #86868b;
  border-radius: 2px;
  animation: scroll 1.5s ease-in-out infinite;
}

@keyframes scroll {
  0%, 100% { transform: translateY(0); opacity: 1; }
  50% { transform: translateY(8px); opacity: 0; }
}

/* ===== Features Section ===== */
.features-section {
  padding: 120px 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 80px;
  opacity: 0;
  transform: translateY(30px) scale(0.95);
  transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform, opacity;
}

.section-header.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.section-label {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(0, 122, 255, 0.1);
  color: #007aff;
  font-size: 13px;
  font-weight: 600;
  border-radius: 20px;
  margin-bottom: 16px;
}

.section-title {
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #1d1d1f 0%, #007aff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-desc {
  font-size: 20px;
  color: #6e6e73;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 32px;
}

.feature-card {
  padding: 48px 32px;
  background: white;
  border-radius: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04);
  text-align: center;
  opacity: 0;
  transform: translateY(40px) scale(0.95);
  transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.8s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.3s ease;
  will-change: transform, opacity;
}

.feature-card.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* Staggered delays for cascade effect */
.feature-card:nth-child(1) { transition-delay: 0s; }
.feature-card:nth-child(2) { transition-delay: 0.1s; }
.feature-card:nth-child(3) { transition-delay: 0.2s; }
.feature-card:nth-child(4) { transition-delay: 0.3s; }

.feature-card:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1), 0 4px 12px rgba(0, 0, 0, 0.05);
  transform: translateY(-4px) scale(1.02);
}

/* Feature Icon with gradient backgrounds for better visibility */
.feature-icon-wrapper {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.feature-icon-wrapper svg {
  width: 36px;
  height: 36px;
}

/* Each feature has a distinct gradient background */
.feature-icon-wrapper.chat {
  background: linear-gradient(135deg, #007aff 0%, #5856d6 100%);
  color: white;
  box-shadow: 0 8px 24px rgba(0, 122, 255, 0.3);
}

.feature-icon-wrapper.document {
  background: linear-gradient(135deg, #34c759 0%, #30d158 100%);
  color: white;
  box-shadow: 0 8px 24px rgba(52, 199, 89, 0.3);
}

.feature-icon-wrapper.search {
  background: linear-gradient(135deg, #ff9500 0%, #ff6b00 100%);
  color: white;
  box-shadow: 0 8px 24px rgba(255, 149, 0, 0.3);
}

.feature-icon-wrapper.shield {
  background: linear-gradient(135deg, #af52de 0%, #8944ab 100%);
  color: white;
  box-shadow: 0 8px 24px rgba(175, 82, 222, 0.3);
}

.feature-card:hover .feature-icon-wrapper {
  transform: scale(1.1) rotate(2deg);
}

/* Explicit dark colors for text visibility */
.feature-title {
  font-size: 21px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #1d1d1f;
  letter-spacing: -0.01em;
}

.feature-desc {
  font-size: 15px;
  color: #6e6e73;
  line-height: 1.6;
}

/* ===== Showcase Section ===== */
.showcase-section {
  padding: 120px 24px;
  background: linear-gradient(180deg, #f5f5f7 0%, #fafafa 100%);
}

.showcase-content {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  align-items: center;
}

@media (max-width: 900px) {
  .showcase-content {
    grid-template-columns: 1fr;
    gap: 48px;
  }
}

.showcase-text {
  opacity: 0;
  transform: translateX(-40px) scale(0.95);
  transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform, opacity;
}

.showcase-text.visible {
  opacity: 1;
  transform: translateX(0) scale(1);
}

.showcase-label {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(0, 122, 255, 0.1);
  color: #007aff;
  font-size: 13px;
  font-weight: 600;
  border-radius: 20px;
  margin-bottom: 16px;
}

.showcase-title {
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 20px;
}

.showcase-desc {
  font-size: 17px;
  color: #6e6e73;
  line-height: 1.6;
  margin-bottom: 32px;
}

.showcase-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.showcase-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  opacity: 0;
  transform: translateX(-30px) scale(0.95);
  transition: opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform, opacity;
}

.showcase-list li.visible {
  opacity: 1;
  transform: translateX(0) scale(1);
}

.showcase-list li:nth-child(1) { transition-delay: 0.1s; }
.showcase-list li:nth-child(2) { transition-delay: 0.2s; }
.showcase-list li:nth-child(3) { transition-delay: 0.3s; }
.showcase-list li:nth-child(4) { transition-delay: 0.4s; }

.showcase-list svg {
  width: 20px;
  height: 20px;
  color: #34c759;
  flex-shrink: 0;
}

.showcase-visual {
  opacity: 0;
  transform: translateX(40px) scale(0.95);
  transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.1s,
              transform 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.1s;
  will-change: transform, opacity;
}

.showcase-visual.visible {
  opacity: 1;
  transform: translateX(0) scale(1);
}

.visual-card {
  background: white;
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.08);
}

.chat-bubble {
  background: #f5f5f7;
  padding: 16px 20px;
  border-radius: 18px;
  border-bottom-left-radius: 4px;
  margin-bottom: 16px;
}

.chat-bubble p {
  font-size: 15px;
  color: #1d1d1f;
}

.chat-bubble.response {
  background: #007aff;
  color: white;
  border-radius: 18px;
  border-bottom-right-radius: 4px;
  margin-left: 20%;
}

.chat-bubble.response p,
.chat-bubble.response ol {
  color: white;
}

.chat-bubble ol {
  margin-top: 8px;
  padding-left: 20px;
  font-size: 14px;
}

.chat-bubble li {
  margin-bottom: 4px;
}

.source {
  display: block;
  margin-top: 12px;
  font-size: 12px;
  opacity: 0.8;
}

/* ===== Stats Section ===== */
.stats-section {
  padding: 80px 24px;
  background: #1d1d1f;
  color: white;
}

.stats-grid {
  max-width: 1000px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 48px;
  text-align: center;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat-item {
  opacity: 0;
  transform: translateY(30px) scale(0.9);
  transition: opacity 0.7s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.7s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform, opacity;
}

.stat-item.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* Staggered delays for stats */
.stat-item:nth-child(1) { transition-delay: 0s; }
.stat-item:nth-child(2) { transition-delay: 0.1s; }
.stat-item:nth-child(3) { transition-delay: 0.2s; }
.stat-item:nth-child(4) { transition-delay: 0.3s; }

.stat-number {
  display: block;
  font-size: clamp(36px, 5vw, 56px);
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #fff 0%, #86868b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 15px;
  color: #86868b;
}

/* ===== CTA Section ===== */
.cta-section {
  padding: 120px 24px;
  text-align: center;
}

.cta-content {
  max-width: 600px;
  margin: 0 auto;
  opacity: 0;
  transform: scale(0.9) translateY(20px);
  transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform, opacity;
}

.cta-content.visible {
  opacity: 1;
  transform: scale(1) translateY(0);
}

.cta-title {
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #1d1d1f;
  margin-bottom: 16px;
}

.cta-desc {
  font-size: 20px;
  color: #434344;
  margin-bottom: 32px;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 18px 36px;
  background: #007aff;
  color: white;
  font-size: 17px;
  font-weight: 600;
  border: none;
  border-radius: 980px;
  cursor: pointer;
  transition: all 0.2s;
}

.cta-button:hover {
  background: #0051d5;
  transform: scale(1.02);
}

.cta-button svg {
  width: 20px;
  height: 20px;
}

/* ===== Footer ===== */
.landing-footer {
  padding: 40px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.footer-brand .brand-icon {
  width: 24px;
  height: 24px;
  color: #1d1d1f;
}

.footer-copy {
  font-size: 13px;
  color: #86868b;
}

@media (max-width: 600px) {
  .footer-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .hero-cta {
    flex-direction: column;
    align-items: center;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .showcase-content {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 32px;
  }
}

/* ===== Reduced Motion ===== */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>