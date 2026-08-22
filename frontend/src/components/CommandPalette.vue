<template>
  <Teleport to="body">
    <Transition name="cmdk-fade">
      <div v-if="visible" class="cmdk-overlay" @click.self="close">
        <div ref="panelEl" class="cmdk" role="dialog" aria-modal="true" aria-label="命令面板">
          <div class="cmdk-input-wrap">
            <el-icon class="cmdk-search-icon"><Search /></el-icon>
            <input
              ref="inputEl"
              v-model="query"
              class="cmdk-input"
              :placeholder="t('palette.placeholder')"
              @keydown="onInputKeydown"
            />
            <kbd class="av-kbd">Esc</kbd>
          </div>

          <div v-if="filtered.length === 0" class="cmdk-empty">
            <p>{{ t('palette.empty', { query }) }}</p>
          </div>

          <div v-else class="cmdk-list">
            <div
              v-for="(item, i) in filtered"
              :key="item.id"
              class="cmdk-item"
              :class="{ active: i === activeIndex }"
              :data-index="i"
              @mouseenter="activeIndex = i"
              @click="run(item)"
            >
              <el-icon class="cmdk-item-icon"><component :is="item.icon" /></el-icon>
              <span class="cmdk-item-label">{{ $t(item.labelKey) }}</span>
              <span v-if="item.groupKey" class="cmdk-item-group">{{ $t(item.groupKey) }}</span>
              <kbd v-if="item.key" class="av-kbd cmdk-item-key">{{ item.key }}</kbd>
            </div>
          </div>

          <div class="cmdk-footer">
            <span><kbd class="av-kbd">↑</kbd><kbd class="av-kbd">↓</kbd> 导航</span>
            <span><kbd class="av-kbd">Enter</kbd> 打开</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import {
  Odometer,
  User,
  TrendCharts,
  ChatDotRound,
  Grid,
  Warning,
  DataAnalysis,
  Moon,
  Sunny,
  HomeFilled,
} from '@element-plus/icons-vue'
import { useThemeStore } from '@/stores/theme'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const { t } = useI18n()

const router = useRouter()
const theme = useThemeStore()
const visible = ref(false)
const query = ref('')
const activeIndex = ref(0)
const inputEl = ref(null)
const panelEl = ref(null)

// 可搜索条目：导航目的地 + 快捷操作
const ITEMS = [
  {
    id: 'boss',
    labelKey: 'menu.talentDashboard',
    groupKey: 'palette.groupBoard',
    icon: Odometer,
    run: () => router.push('/boss'),
  },
  {
    id: 'team',
    labelKey: 'menu.teamAnalytics',
    groupKey: 'palette.groupBoard',
    icon: User,
    run: () => router.push('/boss/team'),
  },
  {
    id: 'roi',
    labelKey: 'menu.teamRoi',
    groupKey: 'palette.groupBoard',
    icon: TrendCharts,
    run: () => router.push('/boss/roi'),
  },
  {
    id: 'risk',
    labelKey: 'menu.attritionRisk',
    groupKey: 'palette.groupBoard',
    icon: Warning,
    run: () => router.push('/boss/attrition-risk'),
  },
  {
    id: 'matrix',
    labelKey: 'menu.talentMatrix',
    groupKey: 'palette.groupBoard',
    icon: Grid,
    run: () => router.push('/boss/talent-matrix'),
  },
  {
    id: 'talent-value',
    labelKey: 'menu.talentValue',
    groupKey: 'palette.groupBoard',
    icon: TrendCharts,
    run: () => router.push('/boss/talent-value'),
  },
  {
    id: 'assistant',
    labelKey: 'menu.aiAssistant',
    groupKey: 'palette.groupChat',
    icon: ChatDotRound,
    run: () => router.push('/boss/assistant'),
  },
  {
    id: 'metrics',
    labelKey: 'menu.metrics',
    groupKey: 'palette.groupAdmin',
    icon: DataAnalysis,
    run: () => router.push('/boss/metrics'),
  },
  {
    id: 'home',
    labelKey: 'palette.home',
    groupKey: 'palette.groupAction',
    icon: HomeFilled,
    run: () => router.push('/'),
  },
  {
    id: 'theme',
    labelKey: theme.isDark ? 'palette.themeLight' : 'palette.themeDark',
    groupKey: 'palette.groupAction',
    icon: theme.isDark ? Sunny : Moon,
    key: 'Ctrl⇧D',
    run: () => theme.toggle(),
  },
]

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return ITEMS
  return ITEMS.filter((it) => (t(it.labelKey) + ' ' + t(it.groupKey)).toLowerCase().includes(q))
})

watch(
  () => props.modelValue,
  async (v) => {
    visible.value = v
    if (v) {
      query.value = ''
      activeIndex.value = 0
      await nextTick()
      inputEl.value?.focus()
    }
  },
)

function close() {
  visible.value = false
  emit('update:modelValue', false)
}

function run(item) {
  item.run()
  close()
}

function onInputKeydown(e) {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = (activeIndex.value + 1) % filtered.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = (activeIndex.value - 1 + filtered.value.length) % filtered.value.length
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const item = filtered.value[activeIndex.value]
    if (item) run(item)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    close()
  }
}

onMounted(() => {
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault()
      if (visible.value) close()
      else emit('update:modelValue', true)
    }
  })
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', () => {})
})
</script>

<style scoped>
.cmdk-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  background: rgba(15, 20, 25, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 12vh;
}
.cmdk {
  width: 560px;
  max-width: 92vw;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 16px;
  box-shadow: var(--av-shadow-xl);
  overflow: hidden;
  animation: cmdk-in 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes cmdk-in {
  from {
    opacity: 0;
    transform: translateY(-10px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
.cmdk-input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.cmdk-search-icon {
  font-size: 18px;
  color: var(--el-text-color-placeholder);
}
.cmdk-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  color: var(--el-text-color-primary);
}
.cmdk-list {
  max-height: 340px;
  overflow-y: auto;
  padding: 8px;
}
.cmdk-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.12s;
}
.cmdk-item.active {
  background: var(--el-color-primary-light-9);
}
.cmdk-item:hover {
  background: var(--el-fill-color-light);
}
.cmdk-item-icon {
  color: var(--el-text-color-secondary);
  font-size: 16px;
  flex-shrink: 0;
}
.cmdk-item.active .cmdk-item-icon {
  color: var(--el-color-primary);
}
.cmdk-item-label {
  font-size: 14px;
  color: var(--el-text-color-primary);
  flex: 1;
}
.cmdk-item-group {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}
.cmdk-item-key {
  opacity: 0.6;
}
.cmdk-empty {
  padding: 32px;
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.cmdk-footer {
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.cmdk-footer .av-kbd {
  margin-right: 4px;
}
</style>
