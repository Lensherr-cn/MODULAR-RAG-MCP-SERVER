<template>
  <div class="auth-background" ref="bgRef">
    <!--  subtle dot grid texture -->
    <div class="dot-grid"></div>

    <!--  aurora orbs with parallax -->
    <div class="orb orb-1" :style="orbStyle(1)"></div>
    <div class="orb orb-2" :style="orbStyle(2)"></div>
    <div class="orb orb-3" :style="orbStyle(3)"></div>
    <div class="orb orb-4" :style="orbStyle(4)"></div>

    <!--  floating rings with parallax -->
    <div class="ring ring-1" :style="ringStyle(1)"></div>
    <div class="ring ring-2" :style="ringStyle(2)"></div>
    <div class="ring ring-3" :style="ringStyle(3)"></div>

    <!--  bottom flowing ribbon -->
    <div class="flowing-ribbon"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const mouseX = ref(0)
const mouseY = ref(0)

const handleMouseMove = (e: MouseEvent) => {
  mouseX.value = (e.clientX / window.innerWidth - 0.5) * 2 // -1 to 1
  mouseY.value = (e.clientY / window.innerHeight - 0.5) * 2 // -1 to 1
}

onMounted(() => {
  window.addEventListener('mousemove', handleMouseMove, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
})

const orbStyle = (index: number) => {
  const intensity = 20 + index * 8
  return {
    transform: `translate(
      calc(var(--base-x, 0px) + ${mouseX.value * intensity}px),
      calc(var(--base-y, 0px) + ${mouseY.value * intensity}px)
    )`
  }
}

const ringStyle = (index: number) => {
  const intensity = 12 + index * 6
  return {
    transform: `translate(
      calc(var(--base-x, 0px) + ${mouseX.value * intensity}px),
      calc(var(--base-y, 0px) + ${mouseY.value * intensity}px)
    ) rotate(var(--rotate, 0deg))`
  }
}
</script>

<style scoped>
.auth-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

/* ===== Dot Grid Texture ===== */
.dot-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.06) 1px, transparent 1px);
  background-size: 28px 28px;
  opacity: 0.6;
  mask-image: radial-gradient(ellipse at center, black 0%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 0%, transparent 75%);
}

/* ===== Aurora Orbs ===== */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  will-change: transform;
  transition: transform 0.2s ease-out;
}

.orb-1 {
  width: 55vw;
  height: 55vw;
  max-width: 700px;
  max-height: 700px;
  background: radial-gradient(circle at 30% 30%, rgba(167, 139, 250, 0.45), rgba(167, 139, 250, 0.1) 60%, transparent 70%);
  top: -10%;
  right: -10%;
  --base-x: 0px;
  --base-y: 0px;
  animation: driftOrb1 22s ease-in-out infinite;
}

.orb-2 {
  width: 45vw;
  height: 45vw;
  max-width: 580px;
  max-height: 580px;
  background: radial-gradient(circle at 40% 40%, rgba(96, 165, 250, 0.4), rgba(96, 165, 250, 0.08) 60%, transparent 70%);
  bottom: -8%;
  left: -8%;
  --base-x: 0px;
  --base-y: 0px;
  animation: driftOrb2 18s ease-in-out infinite;
}

.orb-3 {
  width: 32vw;
  height: 32vw;
  max-width: 420px;
  max-height: 420px;
  background: radial-gradient(circle at 50% 50%, rgba(244, 114, 182, 0.35), rgba(244, 114, 182, 0.06) 55%, transparent 70%);
  top: 45%;
  left: 55%;
  --base-x: 0px;
  --base-y: 0px;
  animation: driftOrb3 26s ease-in-out infinite;
}

.orb-4 {
  width: 24vw;
  height: 24vw;
  max-width: 320px;
  max-height: 320px;
  background: radial-gradient(circle at 50% 50%, rgba(52, 211, 153, 0.25), rgba(52, 211, 153, 0.04) 55%, transparent 70%);
  top: 20%;
  left: 15%;
  --base-x: 0px;
  --base-y: 0px;
  animation: driftOrb4 30s ease-in-out infinite;
}

@keyframes driftOrb1 {
  0%, 100% { --base-x: 0px; --base-y: 0px; }
  25% { --base-x: 40px; --base-y: -30px; }
  50% { --base-x: -20px; --base-y: 40px; }
  75% { --base-x: 30px; --base-y: 20px; }
}

@keyframes driftOrb2 {
  0%, 100% { --base-x: 0px; --base-y: 0px; }
  33% { --base-x: -30px; --base-y: -40px; }
  66% { --base-x: 20px; --base-y: 30px; }
}

@keyframes driftOrb3 {
  0%, 100% { --base-x: 0px; --base-y: 0px; }
  50% { --base-x: -50px; --base-y: -20px; }
}

@keyframes driftOrb4 {
  0%, 100% { --base-x: 0px; --base-y: 0px; }
  25% { --base-x: 20px; --base-y: 30px; }
  50% { --base-x: -30px; --base-y: -10px; }
  75% { --base-x: 10px; --base-y: -25px; }
}

/* ===== Floating Rings ===== */
.ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.08);
  will-change: transform;
  transition: transform 0.25s ease-out;
}

.ring-1 {
  width: 380px;
  height: 380px;
  top: 10%;
  right: 15%;
  --rotate: 0deg;
  animation: rotateRing1 60s linear infinite;
}

.ring-2 {
  width: 280px;
  height: 280px;
  bottom: 20%;
  left: 10%;
  --rotate: 0deg;
  animation: rotateRing2 45s linear infinite reverse;
}

.ring-3 {
  width: 180px;
  height: 180px;
  top: 55%;
  left: 60%;
  --rotate: 0deg;
  animation: rotateRing3 35s linear infinite;
}

@keyframes rotateRing1 {
  from { --rotate: 0deg; }
  to { --rotate: 360deg; }
}

@keyframes rotateRing2 {
  from { --rotate: 0deg; }
  to { --rotate: 360deg; }
}

@keyframes rotateRing3 {
  from { --rotate: 0deg; }
  to { --rotate: -360deg; }
}

/* ===== Flowing Ribbon ===== */
.flowing-ribbon {
  position: absolute;
  bottom: -80px;
  left: -10%;
  width: 120%;
  height: 220px;
  background: linear-gradient(
    90deg,
    rgba(167, 139, 250, 0.15) 0%,
    rgba(96, 165, 250, 0.15) 35%,
    rgba(244, 114, 182, 0.15) 70%,
    rgba(167, 139, 250, 0.15) 100%
  );
  filter: blur(60px);
  border-radius: 50%;
  animation: ribbonFlow 16s ease-in-out infinite;
  opacity: 0.8;
}

@keyframes ribbonFlow {
  0%, 100% {
    transform: translateX(0) scaleY(1);
    opacity: 0.7;
  }
  50% {
    transform: translateX(-5%) scaleY(1.15);
    opacity: 0.95;
  }
}

/* ===== Dark Mode Adaptation ===== */
@media (prefers-color-scheme: dark) {
  .dot-grid {
    background-image: radial-gradient(circle at center, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
    opacity: 0.35;
  }

  .orb-1 {
    background: radial-gradient(circle at 30% 30%, rgba(124, 58, 237, 0.35), rgba(124, 58, 237, 0.05) 60%, transparent 70%);
  }

  .orb-2 {
    background: radial-gradient(circle at 40% 40%, rgba(37, 99, 235, 0.3), rgba(37, 99, 235, 0.04) 60%, transparent 70%);
  }

  .orb-3 {
    background: radial-gradient(circle at 50% 50%, rgba(219, 39, 119, 0.25), rgba(219, 39, 119, 0.03) 55%, transparent 70%);
  }

  .orb-4 {
    background: radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.02) 55%, transparent 70%);
  }

  .ring {
    border-color: rgba(255, 255, 255, 0.06);
  }

  .flowing-ribbon {
    background: linear-gradient(
      90deg,
      rgba(124, 58, 237, 0.12) 0%,
      rgba(37, 99, 235, 0.12) 35%,
      rgba(219, 39, 119, 0.12) 70%,
      rgba(124, 58, 237, 0.12) 100%
    );
    opacity: 0.6;
  }
}

/* ===== Reduced Motion ===== */
@media (prefers-reduced-motion: reduce) {
  .orb,
  .ring,
  .flowing-ribbon {
    animation: none !important;
  }
}
</style>
