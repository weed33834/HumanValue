const MobileLayout = () => import('@/layouts/MobileLayout.vue')

// 四端角色移动端首页（Dashboard）
const roleHome = {
  admin: () => import('@/views/mobile/admin/Dashboard.vue'),
  employee: () => import('@/views/mobile/employee/Dashboard.vue'),
  hr: () => import('@/views/mobile/hr/Dashboard.vue'),
  manager: () => import('@/views/mobile/manager/Dashboard.vue'),
  boss: () => import('@/views/mobile/manager/Dashboard.vue'),
}

// 四端角色移动端 AI 助手（Chat）
const roleChat = {
  admin: () => import('@/views/mobile/admin/Chat.vue'),
  employee: () => import('@/views/mobile/employee/Chat.vue'),
  hr: () => import('@/views/mobile/hr/Chat.vue'),
  manager: () => import('@/views/mobile/manager/Chat.vue'),
  boss: () => import('@/views/mobile/manager/Chat.vue'),
}

// 按角色生成命名空间路由（登录 + 各角色 Layout + 首页 + AI 助手 + 根路由重定向）
function buildRoleRoutes() {
  const routes = []
  // 登录
  routes.push({
    path: '/m/login',
    name: 'MobileLogin',
    component: () => import('@/views/mobile/LoginView.vue'),
    meta: { title: '登录' },
  })

  // 各角色命名空间
  for (const role of Object.keys(roleHome)) {
    const children = [
      {
        path: '',
        name: `Mobile${capitalize(role)}Dashboard`,
        component: roleHome[role],
        meta: { title: '移动看板' },
      },
      {
        path: 'assistant',
        name: `Mobile${capitalize(role)}Chat`,
        component: roleChat[role],
        meta: { title: '智能助手' },
      },
    ]
    // boss/manager 额外团队分析
    if (role === 'boss' || role === 'manager') {
      children.push({
        path: 'team',
        name: `Mobile${capitalize(role)}Team`,
        component: () => import('@/views/mobile/manager/Team.vue'),
        meta: { title: '团队分析' },
      })
    }
    // employee 额外工作输入/历史/成长/反馈
    if (role === 'employee') {
      children.push(
        {
          path: 'input',
          name: 'MobileEmployeeInput',
          component: () => import('@/views/mobile/employee/Input.vue'),
          meta: { title: '工作输入' },
        },
        {
          path: 'history',
          name: 'MobileEmployeeHistory',
          component: () => import('@/views/mobile/employee/History.vue'),
          meta: { title: '历史记录' },
        },
        {
          path: 'growth',
          name: 'MobileEmployeeGrowth',
          component: () => import('@/views/mobile/employee/Growth.vue'),
          meta: { title: '成长轨迹' },
        },
        {
          path: 'feedback',
          name: 'MobileEmployeeFeedback',
          component: () => import('@/views/mobile/employee/Feedback.vue'),
          meta: { title: '反馈申诉' },
        },
      )
    }
    routes.push({
      path: `/m/${role}`,
      name: `Mobile${capitalize(role)}Layout`,
      component: MobileLayout,
      meta: { role: [role], title: 'HumanValue' },
      children,
    })
  }

  // /m 根路由：按登录态与角色重定向
  routes.push({
    path: '/m',
    redirect: () => {
      // 惰性读取，避免循环依赖
      try {
        // 从 localStorage 读取角色（避免引入 pinia 循环依赖）
        const role = localStorage.getItem('humanvalue_role')
        if (role && roleHome[role]) {
          return `/m/${role}`
        }
      } catch {
        // ignore
      }
      return '/m/login'
    },
  })

  return routes
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const mobileRoutes = buildRoleRoutes()

export { mobileRoutes }
export default mobileRoutes
