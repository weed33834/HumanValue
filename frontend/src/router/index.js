import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { isTokenExpired } from '@/utils/auth'
import { isMobile } from '@/utils/device'
import mobileRoutes from './mobile'

const MainLayout = () => import('@/layouts/MainLayout.vue')

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('@/views/LandingView.vue'),
    meta: { title: 'HumanValue' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/boss',
    name: 'BossLayout',
    component: MainLayout,
    meta: { role: ['boss'], title: 'HumanValue' },
    children: [
      {
        path: '',
        name: 'BossDashboard',
        component: () => import('@/views/manager/ManagerDashboard.vue'),
        meta: { title: '人才看板', subtitle: '团队价值 · 成长 · 风险一览' },
      },
      {
        path: 'team',
        name: 'TeamAnalytics',
        component: () => import('@/views/manager/TeamAnalytics.vue'),
        meta: { title: '团队分析', subtitle: '按部门聚合的产出与构成' },
      },
      {
        path: 'roi',
        name: 'TeamROI',
        component: () => import('@/views/manager/TeamROI.vue'),
        meta: { title: '团队ROI', subtitle: '投入产出比与人才价值' },
      },
      {
        path: 'attrition-risk',
        name: 'AttritionRisk',
        component: () => import('@/views/manager/AttritionRisk.vue'),
        meta: { title: '离职风险', subtitle: '高/中/低风险员工识别' },
      },
      {
        path: 'talent-matrix',
        name: 'TalentMatrix',
        component: () => import('@/views/admin/AdminTalentMatrix.vue'),
        meta: { title: '人才九宫格', subtitle: '价值 × 成长矩阵' },
      },
      {
        path: 'evaluation/:id',
        name: 'EvaluationDetail',
        component: () => import('@/views/manager/ApprovalDetail.vue'),
        meta: { title: '评估详情', hidePageHeader: true },
      },
      {
        path: 'assistant',
        name: 'BossAssistant',
        component: () => import('@/views/admin/ChatView.vue'),
        meta: { title: '智能助手', hidePageHeader: true },
      },
      {
        path: 'metrics',
        name: 'SystemMetrics',
        component: () => import('@/views/admin/AdminMetrics.vue'),
        meta: { title: '系统指标', subtitle: '平台运行与模型指标' },
      },
      {
        path: 'talent-value',
        name: 'TalentValue',
        component: () => import('@/views/manager/TalentValueDashboard.vue'),
        meta: {
          title: '人才价值优化',
          subtitle: '九宫格 · 关键人 · 二八 · 人效 · 激励',
          roles: ['boss', 'manager', 'hr', 'admin'],
        },
      },
      {
        path: 'goals',
        name: 'GoalManagement',
        component: () => import('@/views/talent/GoalManagement.vue'),
        meta: { title: '目标管理' },
      },
      {
        path: 'action-items',
        name: 'ActionItems',
        component: () => import('@/views/talent/ActionItems.vue'),
        meta: { title: '行动追踪' },
      },
      {
        path: 'idps',
        name: 'DevelopmentPlans',
        component: () => import('@/views/talent/DevelopmentPlans.vue'),
        meta: { title: '发展计划' },
      },
      {
        path: 'one-on-ones',
        name: 'OneOnOnes',
        component: () => import('@/views/talent/OneOnOnes.vue'),
        meta: { title: '1:1会议' },
      },
      {
        path: 'pulse',
        name: 'PulseSurvey',
        component: () => import('@/views/talent/PulseSurvey.vue'),
        meta: { title: '脉搏调研' },
      },
      {
        path: 'recognition',
        name: 'Recognition',
        component: () => import('@/views/talent/Recognition.vue'),
        meta: { title: '认可奖励' },
      },
      {
        path: 'succession',
        name: 'SuccessionPlanning',
        component: () => import('@/views/talent/SuccessionPlanning.vue'),
        meta: { title: '继任规划' },
      },
      {
        path: 'pip',
        name: 'PIPManagement',
        component: () => import('@/views/talent/PIPManagement.vue'),
        meta: { title: '绩效改进' },
      },
      {
        path: 'skills',
        name: 'SkillMatrix',
        component: () => import('@/views/talent/SkillMatrix.vue'),
        meta: { title: '技能矩阵' },
      },
      {
        path: 'compensation',
        name: 'CompensationInsights',
        component: () => import('@/views/talent/CompensationInsights.vue'),
        meta: { title: '薪酬洞察' },
      },
      {
        path: 'mobility',
        name: 'InternalMobility',
        component: () => import('@/views/talent/InternalMobility.vue'),
        meta: { title: '内部流动' },
      },
      {
        path: 'team-health',
        name: 'TeamHealth',
        component: () => import('@/views/talent/TeamHealth.vue'),
        meta: { title: '团队健康度' },
      },
      {
        path: 'trends',
        name: 'TalentTrends',
        component: () => import('@/views/talent/TalentTrends.vue'),
        meta: { title: '人才趋势' },
      },
      // ===== 管理后台（admin 专属）=====
      {
        path: 'admin/model',
        name: 'AdminModel',
        component: () => import('@/views/admin/AdminModel.vue'),
        meta: { title: '模型管理', role: ['admin'] },
      },
      {
        path: 'admin/llm-config',
        name: 'AdminLLMConfig',
        component: () => import('@/views/admin/AdminLLMConfig.vue'),
        meta: { title: 'LLM配置', role: ['admin'] },
      },
      {
        path: 'admin/providers',
        name: 'AdminProviders',
        component: () => import('@/views/admin/AdminProviders.vue'),
        meta: { title: '模型提供商', role: ['admin'] },
      },
      {
        path: 'admin/prompts',
        name: 'AdminPrompts',
        component: () => import('@/views/admin/AdminPrompts.vue'),
        meta: { title: '提示词管理', role: ['admin'] },
      },
      {
        path: 'admin/skills',
        name: 'AdminSkills',
        component: () => import('@/views/admin/AdminSkills.vue'),
        meta: { title: '技能管理', role: ['admin'] },
      },
      {
        path: 'admin/tools',
        name: 'AdminTools',
        component: () => import('@/views/admin/AdminTools.vue'),
        meta: { title: '工具管理', role: ['admin'] },
      },
      {
        path: 'admin/multi-agent',
        name: 'AdminMultiAgent',
        component: () => import('@/views/admin/AdminMultiAgent.vue'),
        meta: { title: '多智能体', role: ['admin'] },
      },
      {
        path: 'admin/workflows',
        name: 'AdminWorkflows',
        component: () => import('@/views/admin/AdminWorkflows.vue'),
        meta: { title: '工作流编排', role: ['admin'] },
      },
      {
        path: 'admin/knowledge-base',
        name: 'AdminKnowledgeBase',
        component: () => import('@/views/admin/AdminKnowledgeBase.vue'),
        meta: { title: '知识库', role: ['admin'] },
      },
      {
        path: 'admin/knowledge-ops',
        name: 'AdminKnowledgeOps',
        component: () => import('@/views/admin/AdminKnowledgeOps.vue'),
        meta: { title: '知识运维', role: ['admin'] },
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/AdminUsers.vue'),
        meta: { title: '用户管理', role: ['admin'] },
      },
      {
        path: 'admin/api-keys',
        name: 'AdminApiKeys',
        component: () => import('@/views/admin/AdminApiKeys.vue'),
        meta: { title: 'API密钥', role: ['admin'] },
      },
      {
        path: 'admin/audit-logs',
        name: 'AdminAuditLogs',
        component: () => import('@/views/admin/AdminAuditLogs.vue'),
        meta: { title: '审计日志', role: ['admin'] },
      },
      {
        path: 'admin/security',
        name: 'AdminSecurity',
        component: () => import('@/views/admin/AdminSecurity.vue'),
        meta: { title: '安全治理', role: ['admin'] },
      },
      {
        path: 'admin/billing',
        name: 'AdminBilling',
        component: () => import('@/views/admin/AdminBilling.vue'),
        meta: { title: '计费管理', role: ['admin'] },
      },
      {
        path: 'admin/quota-budget',
        name: 'AdminQuotaBudget',
        component: () => import('@/views/admin/AdminQuotaBudget.vue'),
        meta: { title: '配额预算', role: ['admin'] },
      },
      {
        path: 'admin/playground',
        name: 'AdminPlayground',
        component: () => import('@/views/admin/AdminPlayground.vue'),
        meta: { title: '提示词调试', role: ['admin'] },
      },
      {
        path: 'admin/eval-center',
        name: 'AdminEvalCenter',
        component: () => import('@/views/admin/AdminEvalCenter.vue'),
        meta: { title: '评测中心', role: ['admin'] },
      },
      {
        path: 'admin/debug',
        name: 'AdminDebug',
        component: () => import('@/views/admin/AdminDebug.vue'),
        meta: { title: '调试追踪', role: ['admin'] },
      },
      {
        path: 'admin/trace',
        name: 'AdminTrace',
        component: () => import('@/views/admin/AdminTrace.vue'),
        meta: { title: '链路追踪', role: ['admin'] },
      },
      {
        path: 'admin/feature-flags',
        name: 'AdminFeatureFlags',
        component: () => import('@/views/admin/AdminFeatureFlags.vue'),
        meta: { title: '功能开关', role: ['admin'] },
      },
      {
        path: 'admin/scheduler',
        name: 'AdminScheduler',
        component: () => import('@/views/admin/AdminScheduler.vue'),
        meta: { title: '定时任务', role: ['admin'] },
      },
      {
        path: 'admin/webhooks',
        name: 'AdminWebhooks',
        component: () => import('@/views/admin/AdminWebhooks.vue'),
        meta: { title: 'Webhook', role: ['admin'] },
      },
      {
        path: 'admin/alerts',
        name: 'AdminAlerts',
        component: () => import('@/views/admin/AdminAlerts.vue'),
        meta: { title: '告警管理', role: ['admin'] },
      },
      {
        path: 'admin/release-ops',
        name: 'AdminReleaseOps',
        component: () => import('@/views/admin/AdminReleaseOps.vue'),
        meta: { title: '发布运维', role: ['admin'] },
      },
      {
        path: 'admin/model-ops',
        name: 'AdminModelOps',
        component: () => import('@/views/admin/AdminModelOps.vue'),
        meta: { title: '模型运维', role: ['admin'] },
      },
      {
        path: 'admin/rlhf',
        name: 'AdminRLHF',
        component: () => import('@/views/admin/AdminRLHF.vue'),
        meta: { title: 'RLHF', role: ['admin'] },
      },
      {
        path: 'admin/export',
        name: 'AdminExport',
        component: () => import('@/views/admin/AdminExport.vue'),
        meta: { title: '数据导出', role: ['admin'] },
      },
      {
        path: 'admin/agent-templates',
        name: 'AdminAgentTemplates',
        component: () => import('@/views/admin/AdminAgentTemplates.vue'),
        meta: { title: 'Agent模板', role: ['admin'] },
      },
    ],
  },
  // 移动端路由
  ...mobileRoutes,
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在', public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // 公开页面白名单：入口落地页 + 登录页 未登录也放行
  const PUBLIC_PATHS = ['/', '/login', '/m/login']
  if (PUBLIC_PATHS.includes(to.path)) {
    return next()
  }

  // 移动端路由单独处理
  if (to.path.startsWith('/m/')) {
    if (!auth.isLoggedIn) {
      return next('/m/login')
    }
    return next()
  }

  // 未登录跳登录
  if (!auth.isLoggedIn) {
    return next('/login')
  }

  // JWT 过期检查
  if (auth.useJwt && isTokenExpired(auth.token)) {
    await auth.logout()
    return next('/login')
  }

  // 设备感知：移动端访问桌面路由自动跳 /m
  if (isMobile(navigator.userAgent) && !to.query.desktop) {
    return next('/m/boss')
  }

  return next()
})

// 设置页面标题
router.afterEach((to) => {
  const title = to.meta?.title
  document.title = title ? `${title} · HumanValue` : 'HumanValue'
})

export default router
