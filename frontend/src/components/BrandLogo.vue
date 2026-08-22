<template>
  <span class="brand-logo" :class="{ 'is-dark': dark }" role="img" :aria-label="wordmark">
    <span class="brand-logo__mark" :style="markStyle" aria-hidden="true">
      <svg viewBox="0 0 48 48" :width="size" :height="size" focusable="false" aria-hidden="true">
        <defs>
          <linearGradient id="avg-mark" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#4F7CFF" />
            <stop offset="0.5" stop-color="#7C5CFF" />
            <stop offset="1" stop-color="#B44CFF" />
          </linearGradient>
          <linearGradient id="avg-orbit" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stop-color="#4F7CFF" stop-opacity="0" />
            <stop offset="0.5" stop-color="#7C5CFF" stop-opacity="0.9" />
            <stop offset="1" stop-color="#B44CFF" stop-opacity="0" />
          </linearGradient>
        </defs>
        <!-- 外圈轨道：象征人才评估的全面覆盖 -->
        <circle
          cx="24"
          cy="24"
          r="20"
          fill="none"
          stroke="url(#avg-orbit)"
          stroke-width="1.6"
          opacity="0.55"
        />
        <!-- 轨道星点：象征被评估的人才节点 -->
        <circle cx="24" cy="4" r="1.8" fill="#B44CFF" />
        <circle cx="39" cy="17" r="1.4" fill="#7C5CFF" opacity="0.8" />
        <circle cx="8.5" cy="14" r="1.2" fill="#4F7CFF" opacity="0.7" />
        <!-- 中心主体：A形 + 渐变核心，象征 Agent 与价值坐标 -->
        <path
          d="M24 8 L35 40 H30.4 L28.2 33 H19.8 L17.6 40 H13 Z M22 29.5 H26 L24 17 Z"
          fill="url(#avg-mark)"
        />
        <!-- 上升箭头：象征价值增长 -->
        <path
          d="M13.5 33 L19.5 27 L23 30.5 L31 22"
          fill="none"
          stroke="#fff"
          stroke-width="2.4"
          stroke-linecap="round"
          stroke-linejoin="round"
          opacity="0.92"
        />
        <path
          d="M31 22 H26.5 M31 22 V26.5"
          fill="none"
          stroke="#fff"
          stroke-width="2.4"
          stroke-linecap="round"
          stroke-linejoin="round"
          opacity="0.92"
        />
      </svg>
    </span>
    <span v-if="showText" class="brand-logo__text" :style="textStyle">
      {{ wordmark }}
      <span v-if="showTag" class="brand-logo__tag">Talent Intelligence</span>
    </span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: { type: Number, default: 28 },
  showText: { type: Boolean, default: true },
  showTag: { type: Boolean, default: false },
  textSize: { type: Number, default: 16 },
  wordmark: { type: String, default: 'HumanValue' },
  dark: { type: Boolean, default: false },
})

const markStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
}))

const textStyle = computed(() => ({
  fontSize: `${props.textSize}px`,
}))
</script>

<style scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  line-height: 1.1;
  color: inherit;
}
.brand-logo__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 16px rgba(90, 90, 255, 0.18);
  flex-shrink: 0;
}
.brand-logo__text {
  font-weight: 700;
  letter-spacing: 0.4px;
  color: currentColor;
  white-space: nowrap;
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
}
.brand-logo__tag {
  font-size: 0.55em;
  font-weight: 500;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: rgba(140, 140, 255, 0.9);
}
</style>
