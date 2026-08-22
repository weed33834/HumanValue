<template>
  <ErrorBoundary>
    <router-view v-slot="{ Component, route }">
      <transition name="fade-slide" mode="out-in" appear>
        <component :is="Component" :key="route.matched[0]?.path || route.path" />
      </transition>
    </router-view>
  </ErrorBoundary>

  <!-- 全局快捷键说明弹窗 (Ctrl+/) -->
  <ShortcutsDialog v-model="shortcutsVisible" />

  <!-- 全局命令面板 (Ctrl+K 搜索导航) -->
  <CommandPalette v-model="commandPaletteVisible" />

  <!-- 路由加载进度条 -->
  <RouteProgress />

  <!-- 快捷键帮助触发器 -->
  <el-tooltip content="快捷键说明 (Ctrl+/)" placement="left">
    <button class="shortcuts-fab" :aria-label="'快捷键说明'" @click="shortcutsVisible = true">
      <el-icon><Operation /></el-icon>
    </button>
  </el-tooltip>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { Operation } from '@element-plus/icons-vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import ShortcutsDialog from '@/components/ShortcutsDialog.vue'
import CommandPalette from '@/components/CommandPalette.vue'
import RouteProgress from '@/components/RouteProgress.vue'
import { useThemeStore } from '@/stores/theme'

const shortcutsVisible = ref(false)
const commandPaletteVisible = ref(false)
const theme = useThemeStore()

function onKeydown(e) {
  // Ctrl+/ 或 Cmd+/ 打开快捷键说明
  if ((e.ctrlKey || e.metaKey) && e.key === '/') {
    e.preventDefault()
    shortcutsVisible.value = true
    return
  }
  // Ctrl+Shift+D 切换暗色模式
  if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'd') {
    e.preventDefault()
    theme.toggle()
    return
  }
  // Esc 关闭弹窗
  if (e.key === 'Escape' && shortcutsVisible.value) {
    shortcutsVisible.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style>
html,
body,
#app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family:
    'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial,
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* 快捷键浮动触发按钮 (右下角, 登录/公开页隐藏) */
.shortcuts-fab {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 950;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--av-shadow-md);
  transition:
    transform 0.2s cubic-bezier(0.34, 1.4, 0.5, 1),
    box-shadow 0.2s,
    color 0.2s;
}
.shortcuts-fab:hover {
  transform: translateY(-2px) scale(1.05);
  color: var(--el-color-primary);
  box-shadow: var(--av-shadow-lg);
}
.shortcuts-fab:active {
  transform: scale(0.96);
}
</style>
