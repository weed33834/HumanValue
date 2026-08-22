/**
 * 移动端导航配置（支持四端角色：admin / employee / hr / manager / boss）
 *
 * MOBILE_TABS: 每端移动端底部 Tab（均含 AI 助手入口）
 * desktopToMobilePath: 桌面路径 → /m 移动路径映射（login / 角色路由 / 深层路由）
 * tabsForRole: 按角色取 Tab，未知角色返回空数组
 */

export const MOBILE_TABS = {
  admin: [
    { label: '看板', icon: '◧', path: '/m/admin' },
    { label: 'AI助手', icon: '◆', path: '/m/admin/assistant' },
    { label: '我的', icon: '◉', path: '/m/admin/me' },
  ],
  employee: [
    { label: '看板', icon: '◧', path: '/m/employee' },
    { label: '工作输入', icon: '✎', path: '/m/employee/input' },
    { label: '历史', icon: '▤', path: '/m/employee/history' },
    { label: 'AI助手', icon: '◆', path: '/m/employee/assistant' },
  ],
  hr: [
    { label: '看板', icon: '◧', path: '/m/hr' },
    { label: 'AI助手', icon: '◆', path: '/m/hr/assistant' },
    { label: '我的', icon: '◉', path: '/m/hr/me' },
  ],
  manager: [
    { label: '看板', icon: '◧', path: '/m/manager' },
    { label: '团队', icon: '◈', path: '/m/manager/team' },
    { label: 'AI助手', icon: '◆', path: '/m/manager/assistant' },
  ],
}

// boss 复用 manager 的移动端导航（老板视角 = 管理看板）
const BOSS_TABS = MOBILE_TABS.manager

const ROLE_PREFIX = {
  boss: '/boss',
  manager: '/manager',
  hr: '/hr',
  admin: '/admin',
  employee: '/employee',
}

export function desktopToMobilePath(path) {
  if (path === '/login') return '/m/login'
  // 已是 /m 前缀则原样返回（避免重复加前缀）
  if (path.startsWith('/m/')) return path
  for (const role of Object.keys(ROLE_PREFIX)) {
    const prefix = ROLE_PREFIX[role]
    if (path === prefix || path.startsWith(prefix + '/')) {
      return '/m' + path
    }
  }
  return path
}

export function tabsForRole(role) {
  if (role === 'boss') return BOSS_TABS
  return MOBILE_TABS[role] || []
}
