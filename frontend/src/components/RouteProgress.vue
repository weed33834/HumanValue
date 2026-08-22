<template>
  <div class="route-progress" :class="{ active: loading }">
    <div class="route-progress__bar"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

// 顶部路由加载进度条 (nprogress 风格, 全局路由切换反馈)
const router = useRouter()
const loading = ref(false)
let timer = null

router.beforeEach(() => {
  loading.value = true
  clearTimeout(timer)
})
router.afterEach(() => {
  clearTimeout(timer)
  timer = setTimeout(() => {
    loading.value = false
  }, 250)
})
router.onError(() => {
  clearTimeout(timer)
  loading.value = false
})
</script>

<style scoped>
.route-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 4000;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s;
}
.route-progress.active {
  opacity: 1;
}
.route-progress__bar {
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, var(--el-color-primary), #7c3aed);
  border-radius: 0 3px 3px 0;
  animation: rp-slide 1.1s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}
@keyframes rp-slide {
  0% {
    margin-left: -40%;
  }
  100% {
    margin-left: 100%;
  }
}
</style>
