<template>
  <div class="av-skeleton-loading" :aria-label="ariaLabel" role="status">
    <template v-for="(row, i) in rows" :key="i">
      <div v-if="variant === 'card'" class="av-skeleton av-skeleton--card" :style="cardStyle"></div>
      <div v-else class="av-skeleton-row" :style="{ gap }">
        <div v-if="avatar" class="av-skeleton av-skeleton--avatar"></div>
        <div class="av-skeleton-lines" :style="{ flex: 1 }">
          <div class="av-skeleton av-skeleton--text" :style="{ width: titleWidth }"></div>
          <div
            v-for="l in lines"
            :key="l"
            class="av-skeleton av-skeleton--text"
            :style="{ width: lineWidths[(l - 1) % lineWidths.length], opacity: 1 - l * 0.15 }"
          ></div>
        </div>
      </div>
    </template>
    <span class="sr-only">加载中…</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// 轻量骨架屏: 支持列表行与卡片两种形态。
// 用法: <SkeletonLoader :rows="6" avatar lines="3" /> 或 <SkeletonLoader :rows="3" variant="card" />
const props = defineProps({
  rows: { type: Number, default: 4 },
  variant: { type: String, default: 'text' }, // text | card
  avatar: { type: Boolean, default: false },
  lines: { type: Number, default: 2 },
  gap: { type: String, default: '16px' },
  titleWidth: { type: String, default: '30%' },
  ariaLabel: { type: String, default: '正在加载数据' },
})

const lineWidths = ['100%', '92%', '85%', '78%', '70%']
const cardStyle = computed(() => ({ marginBottom: props.gap }))
</script>

<style scoped>
.skeleton-loading,
.av-skeleton-loading {
  width: 100%;
}
.av-skeleton-row {
  display: flex;
  align-items: flex-start;
}
.av-skeleton-lines {
  display: flex;
  flex-direction: column;
}
.av-skeleton--card {
  margin-bottom: 12px;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
</style>
