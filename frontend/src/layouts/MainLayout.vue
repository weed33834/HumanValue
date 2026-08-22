<template>
  <el-container class="main-layout">
    <!-- 安全合规：所有页面水印防截图（老板视角，全部数据敏感） -->
    <Watermark />
    <!-- 无障碍：跳转到主内容，键盘用户可快速跳过导航 -->
    <a href="#main-content" class="skip-link">跳转到主内容</a>

    <!-- 移动端遮罩层 -->
    <transition name="fade">
      <div v-if="mobileSidebarVisible" class="sidebar-overlay" @click="closeMobileSidebar"></div>
    </transition>

    <!-- 侧边栏 -->
    <el-aside
      :width="asideWidth"
      class="sidebar"
      :class="{ 'sidebar--mobile-open': mobileSidebarVisible }"
    >
      <div class="logo" role="heading" aria-level="1">
        <BrandLogo :size="26" :text-size="17" wordmark="HumanValue" />
      </div>
      <el-menu
        :default-active="activeMenu"
        class="menu"
        router
        aria-label="主导航"
        background-color="transparent"
        text-color="#e5e7eb"
        active-text-color="#60a5fa"
        @select="handleMenuSelect"
      >
        <template v-for="item in visibleMenuItems" :key="item.index">
          <el-menu-item :index="item.index">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ $t('menu.' + item.labelKey) }}</span>
          </el-menu-item>
        </template>
      </el-menu>
      <!-- 退出登录按钮（独立于 el-menu，避免 router 模式冲突） -->
      <div class="logout-section">
        <el-button text class="logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </el-button>
      </div>
    </el-aside>

    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header" role="banner">
        <div class="header-left">
          <!-- 移动端汉堡菜单 -->
          <el-button
            class="hamburger-btn av-hide-desktop"
            text
            :aria-label="mobileSidebarVisible ? '关闭菜单' : '打开菜单'"
            @click="toggleMobileSidebar"
          >
            <el-icon :size="22">
              <Close v-if="mobileSidebarVisible" />
              <Menu v-else />
            </el-icon>
          </el-button>
          <div class="breadcrumb">
            <span class="breadcrumb-root">HumanValue</span>
            <el-icon class="breadcrumb-sep"><ArrowRight /></el-icon>
            <span class="breadcrumb-current">{{ currentSection }}</span>
          </div>
        </div>
        <div class="header-right">
          <!-- 语言切换 EN / 中文 / 日本語 -->
          <el-dropdown trigger="click" @command="onChangeLocale">
            <button class="lang-btn" :aria-label="'Language / 语言'">
              <el-icon><Flag /></el-icon>
              <span class="lang-code">{{ localeCode }}</span>
              <el-icon class="lang-caret"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="en" :class="{ active: locale === 'en' }"
                  >English</el-dropdown-item
                >
                <el-dropdown-item command="zh" :class="{ active: locale === 'zh' }"
                  >中文</el-dropdown-item
                >
                <el-dropdown-item command="ja" :class="{ active: locale === 'ja' }"
                  >日本語</el-dropdown-item
                >
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-tooltip
            :content="theme.isDark ? $t('header.lightMode') : $t('header.darkMode')"
            placement="bottom"
          >
            <el-button
              class="theme-toggle"
              circle
              size="small"
              :aria-label="theme.isDark ? $t('header.lightMode') : $t('header.darkMode')"
              @click="theme.toggle"
            >
              <el-icon v-if="theme.isDark"><Sunny /></el-icon>
              <el-icon v-else><Moon /></el-icon>
            </el-button>
          </el-tooltip>
          <el-badge
            :value="notification.pendingCount + notification.unreadCount"
            :max="99"
            class="approval-badge"
          >
            <el-icon class="bell-icon" @click="handleBellClick"><Bell /></el-icon>
          </el-badge>
          <span class="header-role av-hide-mobile" aria-live="polite"
            >{{ $t('header.roleLabel') }}：{{ roleLabel }}</span
          >
        </div>
      </el-header>

      <!-- 页面内容区 -->
      <el-main id="main-content" class="main-content" tabindex="-1">
        <!-- 自动统一页头 (读路由 meta, 沉浸页可 hidePageHeader 关闭) -->
        <PageHeader
          v-if="!route.meta.hidePageHeader"
          :title="pageTitle"
          :subtitle="route.meta.subtitle"
          class="av-auto-page-header"
        />
        <router-view v-slot="{ Component, route: slotRoute }">
          <transition name="fade-slide" mode="out-in" appear>
            <component :is="Component" :key="slotRoute.path" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- 通知抽屉 -->
    <el-drawer
      v-model="notification.notificationDrawerVisible"
      title="站内通知"
      :size="drawerSize"
      direction="rtl"
    >
      <div class="notification-drawer">
        <div class="notification-actions">
          <el-button
            size="small"
            @click="notification.markAllAsRead"
            :disabled="notification.unreadCount === 0"
          >
            全部标记已读
          </el-button>
          <el-button
            size="small"
            @click="notification.fetchNotifications({ page: 1, page_size: 20 })"
          >
            刷新
          </el-button>
        </div>
        <el-empty v-if="notification.notifications.length === 0" description="暂无通知" />
        <div
          v-for="item in notification.notifications"
          :key="item.notification_id"
          class="notification-item"
          :class="{ unread: !item.is_read }"
          @click="notification.markAsRead(item.notification_id)"
        >
          <div class="notification-title">{{ item.title }}</div>
          <div class="notification-content">{{ item.content }}</div>
          <div class="notification-time">{{ item.created_at }}</div>
        </div>
      </div>
    </el-drawer>
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useThemeStore } from '@/stores/theme'
import Watermark from '@/components/Watermark.vue'
import BrandLogo from '@/components/BrandLogo.vue'
import PageHeader from '@/components/PageHeader.vue'
import {
  Aim,
  List,
  Reading,
  ChatLineSquare,
  DataLine,
  Trophy,
  Connection,
  WarningFilled,
  Grid,
  Money,
  Position,
  FirstAidKit,
  TrendCharts,
  Odometer,
  User,
  Warning,
  ChatDotRound,
  DataAnalysis,
  ArrowRight,
  ArrowDown,
  Flag,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const notification = useNotificationStore()
const theme = useThemeStore()

// i18n 语言切换
import { setLocale, getLocale } from '@/i18n'
const locale = ref(getLocale())
const localeCode = computed(() =>
  locale.value === 'zh' ? '中' : locale.value === 'ja' ? '日' : 'EN',
)
function onChangeLocale(l) {
  locale.value = setLocale(l)
}

// 菜单配置：每项标注可访问的角色白名单（空数组 = 全部登录角色可见）
const MENU_ITEMS = [
  {
    index: '/boss',
    label: '人才看板',
    labelKey: 'talentDashboard',
    icon: Odometer,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/team',
    label: '团队分析',
    labelKey: 'teamAnalytics',
    icon: User,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/roi',
    label: '团队ROI',
    labelKey: 'teamRoi',
    icon: TrendCharts,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/attrition-risk',
    label: '离职风险',
    labelKey: 'attritionRisk',
    icon: Warning,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/talent-matrix',
    label: '人才九宫格',
    labelKey: 'talentMatrix',
    icon: Grid,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/assistant',
    label: 'AI助手',
    labelKey: 'aiAssistant',
    icon: ChatDotRound,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/goals',
    label: '目标管理',
    labelKey: 'goals',
    icon: Aim,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/action-items',
    label: '行动追踪',
    labelKey: 'actionItems',
    icon: List,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/idps',
    label: '发展计划',
    labelKey: 'developmentPlans',
    icon: Reading,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/one-on-ones',
    label: '1:1会议',
    labelKey: 'oneOnOnes',
    icon: ChatLineSquare,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/pulse',
    label: '脉搏调研',
    labelKey: 'pulseSurvey',
    icon: DataLine,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/recognition',
    label: '认可奖励',
    labelKey: 'recognition',
    icon: Trophy,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/succession',
    label: '继任规划',
    labelKey: 'succession',
    icon: Connection,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/pip',
    label: '绩效改进',
    labelKey: 'pip',
    icon: WarningFilled,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/skills',
    label: '技能矩阵',
    labelKey: 'skills',
    icon: Grid,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/compensation',
    label: '薪酬洞察',
    labelKey: 'compensation',
    icon: Money,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/mobility',
    label: '内部流动',
    labelKey: 'mobility',
    icon: Position,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/team-health',
    label: '团队健康度',
    labelKey: 'teamHealth',
    icon: FirstAidKit,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/trends',
    label: '人才趋势',
    labelKey: 'trends',
    icon: TrendCharts,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  // 系统指标为 ADMIN 运维专属
  {
    index: '/boss/talent-value',
    label: '人才价值优化',
    labelKey: 'talentValue',
    icon: TrendCharts,
    roles: ['boss', 'manager', 'hr', 'admin'],
  },
  {
    index: '/boss/metrics',
    label: '系统指标',
    labelKey: 'metrics',
    icon: DataAnalysis,
    roles: ['admin'],
  },
]

// 按当前角色过滤菜单
const visibleMenuItems = computed(() => {
  const r = auth.role || ''
  return MENU_ITEMS.filter((item) => item.roles.length === 0 || item.roles.includes(r))
})

// 角色标签用 i18n: $t('roles.'+role)
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const roleLabel = computed(() => t('roles.' + (auth.role || 'employee')))

const activeMenu = computed(() => route.path)
const mobileSidebarVisible = ref(false)
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1200)

const asideWidth = computed(() => {
  if (windowWidth.value <= 768) {
    return mobileSidebarVisible.value ? '240px' : '0px'
  }
  return '220px'
})

const drawerSize = computed(() => {
  return windowWidth.value <= 768 ? '85%' : '400px'
})

const pageTitle = computed(() => route.meta.title || 'HumanValue')
// 面包屑当前项: 优先取当前菜单项的 label
const currentSection = computed(() => {
  const item = MENU_ITEMS.find((m) => m.index === activeMenu.value)
  return item ? item.label : pageTitle.value
})

function toggleMobileSidebar() {
  mobileSidebarVisible.value = !mobileSidebarVisible.value
}

function closeMobileSidebar() {
  mobileSidebarVisible.value = false
}

function handleMenuSelect() {
  // 移动端选择菜单后自动关闭侧边栏
  if (windowWidth.value <= 768) {
    mobileSidebarVisible.value = false
  }
}

// 路由变化时关闭移动端侧边栏
watch(
  () => route.path,
  () => {
    if (windowWidth.value <= 768) {
      mobileSidebarVisible.value = false
    }
  },
)

function handleResize() {
  windowWidth.value = window.innerWidth
  // 大屏幕时自动关闭移动端侧边栏
  if (windowWidth.value > 768) {
    mobileSidebarVisible.value = false
  }
}

// 铃铛点击:有未读通知则打开通知抽屉,否则跳转看板
function handleBellClick() {
  if (notification.unreadCount > 0 || notification.notifications.length > 0) {
    notification.openNotificationDrawer()
  } else {
    router.push('/boss')
  }
}

async function handleLogout() {
  notification.stopPolling()
  await auth.logout()
  router.push('/login')
}

onMounted(() => {
  notification.startPolling(auth.role)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  notification.stopPolling()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

/* 无障碍：跳转链接默认隐藏，键盘聚焦时显现 */
.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  z-index: 1000;
  padding: 8px 16px;
  background: #2563eb;
  color: #fff;
  border-radius: 0 0 4px 0;
  text-decoration: none;
  font-size: 14px;
  transition: left var(--av-transition-fast);
}
.skip-link:focus {
  left: 0;
}
#main-content:focus {
  outline: none;
}

/* ==================== 侧边栏 ==================== */
.sidebar {
  background: linear-gradient(180deg, #141824 0%, #1b2031 60%, #232a40 100%);
  color: #fff;
  transition:
    width var(--av-transition-base) var(--av-ease-out),
    transform var(--av-transition-base) var(--av-ease-out);
  overflow: hidden;
  position: relative;
  z-index: 1001;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}
/* 侧边栏顶部品牌氛围光 */
.sidebar::before {
  content: '';
  position: absolute;
  top: -120px;
  left: -60px;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.28), transparent 70%);
  pointer-events: none;
  filter: blur(20px);
}

/* 侧边栏顶部 Logo */
.logo {
  height: var(--av-header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #ffffff;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.02);
}

/* 菜单样式 */
.menu {
  border-right: none;
  height: calc(100vh - var(--av-header-height) - 60px);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px 0;
  background: transparent !important;
}
.menu :deep(.el-menu-item) {
  transition: all var(--av-transition-fast) var(--av-ease-smooth);
  border-radius: 12px;
  margin: 3px 12px;
  width: calc(100% - 24px);
  height: 44px;
  line-height: 44px;
  color: rgba(229, 231, 235, 0.78) !important;
  font-weight: 500;
  position: relative;
}
.menu :deep(.el-menu-item .el-icon) {
  color: rgba(229, 231, 235, 0.6);
  transition: color var(--av-transition-fast) var(--av-ease-smooth);
}
.menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.06) !important;
  color: #fff !important;
}
.menu :deep(.el-menu-item:hover .el-icon) {
  color: #c7d2fe;
}
.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(
    135deg,
    rgba(99, 102, 241, 0.35),
    rgba(124, 58, 237, 0.22)
  ) !important;
  color: #fff !important;
  font-weight: 600;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.08),
    0 4px 12px rgba(79, 70, 229, 0.25);
}
.menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 24px;
  border-radius: 0 4px 4px 0;
  background: linear-gradient(180deg, #818cf8, #a78bfa);
  box-shadow: 0 0 10px rgba(129, 140, 248, 0.6);
}
.menu :deep(.el-menu-item.is-active .el-icon) {
  color: #e0e7ff;
}

/* 菜单滚动条 */
.menu::-webkit-scrollbar {
  width: 4px;
}
.menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
.menu::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 退出登录按钮 */
.logout-section {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}
.logout-btn {
  width: 100%;
  justify-content: flex-start;
  color: rgba(229, 231, 235, 0.8);
  height: 42px;
  border-radius: 12px;
  padding: 0 12px !important;
  transition: all var(--av-transition-fast) var(--av-ease-smooth);
}
.logout-btn:hover {
  background-color: rgba(244, 63, 94, 0.12) !important;
  color: #fda4af !important;
}
html.dark .logout-btn {
  color: var(--el-text-color-regular);
}

/* ==================== 移动端遮罩 ==================== */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  z-index: 1000;
}

/* ==================== 主容器 ==================== */
.main-container {
  height: 100vh;
  overflow: hidden;
}

/* ==================== 头部 ==================== */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--av-header-height) !important;
  padding: 0 24px;
  background-color: color-mix(in srgb, var(--el-bg-color) 82%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 1px 0 var(--el-border-color-lighter);
  z-index: 10;
  transition: box-shadow var(--av-transition-base);
}
html.dark .header {
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.breadcrumb-root {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}
.breadcrumb-sep {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}
.breadcrumb-current {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.lang-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: transparent;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.lang-btn:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}
.lang-code {
  font-size: 12px;
  font-weight: 600;
}
.lang-caret {
  font-size: 12px;
}

/* 汉堡菜单按钮 */
.hamburger-btn {
  padding: 8px !important;
  color: var(--el-text-color-primary) !important;
}

/* 主题切换按钮 */
.theme-toggle {
  border: 1px solid var(--el-border-color);
  color: var(--el-text-color-regular);
  transition: all var(--av-transition-fast) var(--av-ease-smooth) !important;
}
.theme-toggle:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  transform: rotate(15deg);
}

/* 铃铛图标 */
.approval-badge {
  display: inline-flex;
  align-items: center;
}
.bell-icon {
  font-size: 20px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all var(--av-transition-fast) var(--av-ease-spring);
}
.bell-icon:hover {
  color: var(--el-color-primary);
  transform: scale(1.1) rotate(10deg);
}

/* 角色标签 */
.header-role {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  padding: 4px 12px;
  border-radius: 20px;
  background: var(--el-fill-color-light);
}

/* ==================== 主内容区 ==================== */
.main-content {
  background-color: var(--el-bg-color-page);
  background-image: radial-gradient(circle at 1px 1px, rgba(17, 24, 39, 0.025) 1px, transparent 0);
  background-size: 24px 24px;
  overflow-y: auto;
  padding: 24px 28px;
  transition: background-color var(--av-transition-base);
}
html.dark .main-content {
  background-color: var(--el-bg-color-page);
  background-image: radial-gradient(
    circle at 1px 1px,
    rgba(255, 255, 255, 0.02) 1px,
    transparent 0
  );
}

/* 主内容内部统一收敛宽度 */
.main-content > :deep(*) {
  max-width: var(--av-content-max-width);
  margin-left: auto;
  margin-right: auto;
}

/* ==================== 通知抽屉 ==================== */
.notification-drawer {
  padding: 0 8px;
}
.notification-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.notification-item {
  padding: 12px 16px;
  border-radius: var(--av-radius-md);
  margin-bottom: 8px;
  cursor: pointer;
  transition: all var(--av-transition-fast) var(--av-ease-smooth);
  border: 1px solid var(--el-border-color-lighter);
  animation: fadeInUp var(--av-transition-base) var(--av-ease-out) both;
}
.notification-item:hover {
  background-color: var(--el-fill-color-light);
  transform: translateX(-4px);
  box-shadow: var(--av-shadow-sm);
}
.notification-item.unread {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}
.notification-item:nth-child(1) {
  animation-delay: 0.02s;
}
.notification-item:nth-child(2) {
  animation-delay: 0.06s;
}
.notification-item:nth-child(3) {
  animation-delay: 0.1s;
}
.notification-item:nth-child(4) {
  animation-delay: 0.14s;
}
.notification-item:nth-child(5) {
  animation-delay: 0.18s;
}
.notification-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}
.notification-content {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
  word-break: break-all;
}
.notification-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* ==================== 过渡动画 ==================== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--av-transition-base) var(--av-ease-out);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ==================== 移动端样式 ==================== */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 240px !important;
    transform: translateX(-100%);
    z-index: 1001;
    box-shadow: var(--av-shadow-xl);
  }
  .sidebar--mobile-open {
    transform: translateX(0);
  }

  .header {
    padding: 0 12px;
  }
  .breadcrumb-root {
    font-size: 13px;
  }
  .breadcrumb-current {
    font-size: 13px;
    max-width: 120px;
  }
  .header-right {
    gap: 8px;
  }
  .header-role {
    display: none;
  }

  .main-content {
    padding: 12px;
  }

  .notification-drawer {
    padding: 0 4px;
  }
  .notification-item {
    padding: 10px 12px;
  }
}

/* ==================== 平板端样式 ==================== */
@media (min-width: 769px) and (max-width: 1024px) {
  .main-content {
    padding: 16px;
  }
}

/* ==================== 大屏样式 ==================== */
@media (min-width: 1920px) {
  .main-content {
    padding: 32px;
  }
}
</style>
