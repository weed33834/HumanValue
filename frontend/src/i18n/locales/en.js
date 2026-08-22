export default {
  common: {
    appName: 'HumanValue',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    refresh: 'Refresh',
    search: 'Search',
    confirm: 'Confirm',
    create: 'Create',
    edit: 'Edit',
    close: 'Close',
    yes: 'Yes',
    no: 'No',
    retry: 'Retry',
    back: 'Back',
    logout: 'Logout',
    loading: 'Loading…',
    noData: 'No data',
    ok: 'OK',
    detail: 'Detail',
    action: 'Action',
    status: 'Status',
    name: 'Name',
    role: 'Role',
    department: 'Department',
    send: 'Send',
    stop: 'Stop',
  },
  header: {
    roleLabel: 'Current role',
    notifications: 'Notifications',
    lightMode: 'Switch to light mode',
    darkMode: 'Switch to dark mode',
    shortcuts: 'Shortcuts (Ctrl+/)',
    logout: 'Logout',
  },
  menu: {
    talentDashboard: 'Talent Dashboard',
    teamAnalytics: 'Team Analytics',
    teamRoi: 'Team ROI',
    attritionRisk: 'Attrition Risk',
    talentMatrix: 'Talent Matrix',
    aiAssistant: 'AI Assistant',
    goals: 'Goals',
    actionItems: 'Action Items',
    developmentPlans: 'Development Plans',
    oneOnOnes: '1:1 Meetings',
    pulseSurvey: 'Pulse Survey',
    recognition: 'Recognition',
    succession: 'Succession',
    pip: 'PIP',
    skills: 'Skill Matrix',
    compensation: 'Compensation',
    mobility: 'Internal Mobility',
    teamHealth: 'Team Health',
    trends: 'Talent Trends',
    metrics: 'System Metrics',
    talentValue: 'Talent Value',
  },
  roles: {
    boss: 'Boss',
    manager: 'Manager',
    hr: 'HR',
    admin: 'Admin',
    employee: 'Employee',
  },
  page: {
    talentValue: 'Talent Value Optimization',
    talentValueSub:
      '9-box · Key Person · Pareto · Efficiency · Incentive · Compensation · Succession · Burnout · Skills · Review',
    dashboard: 'Dashboard',
    assistant: 'AI Assistant',
  },
  shortcut: {
    title: 'Keyboard Shortcuts',
    general: 'General',
    chat: 'Chat',
    nav: 'Navigation',
    openShortcuts: 'Open / close shortcuts',
    openPalette: 'Open command palette',
    closeDialog: 'Close dialog',
    toggleTheme: 'Toggle dark / light mode',
    sendMsg: 'Send message',
    newline: 'New line',
    stopGen: 'Stop generation',
    backPage: 'Go back',
    forwardPage: 'Forward',
  },
  palette: {
    placeholder: 'Search pages, actions… (↑↓ select, Enter open, Esc close)',
    empty: 'No results for "{{query}}"',
    groupBoard: 'Board',
    groupChat: 'Chat',
    groupAdmin: 'Admin',
    groupAction: 'Action',
    nav: 'Navigate',
    home: 'Home',
    theme: 'Switch theme',
    themeLight: 'Switch to light mode',
    themeDark: 'Switch to dark mode',
  },
  notification: {
    title: 'Notifications',
    markAllRead: 'Mark all as read',
    empty: 'No notifications',
    unread: 'unread',
  },
  welcome: {
    title: 'HumanValue Assistant',
    subtitle: 'Your intelligent talent value analysis assistant · also the system chat console',
    hint: 'You can operate directly in chat. Try the examples below:',
    more: 'Or ask "what can you do" to see all capabilities',
  },

  pages: {
    tv: {
      systemCurrent: 'System: {label} — {context}',
      coreQuestion: 'Core question',
      keyMetrics: 'Key metrics',
      theory: 'Theory',
      kpiTotal: 'Total Talent',
      kpiStar: 'Stars/Key',
      kpiPotential: 'Potential',
      kpiUnder: 'Underperformers',
      tabGrid: '9-Box Grid',
      tabCritical: 'Key Person / Single Point',
      tabPareto: 'Pareto',
      tabEfficiency: 'Efficiency',
      tabIncentive: 'Incentive',
      tabMarket: 'Compensation',
      tabSuccession: 'Succession',
      tabBurnout: 'Burnout',
      tabSkill: 'Skill Fit',
      tabReview: 'Quarterly Review',
      gridAlert:
        '9-box: Performance(x) × Potential(y) → action categories (Boston Matrix + Expectancy Theory)',
      strategyHeader: 'Disposition strategy (by value)',
      colEmployee: 'Employee',
      colDept: 'Department',
      colPerf: 'Performance',
      colPot: 'Potential',
      colCat: 'Category',
      colRisk: 'Risk',
      colStrategy: 'Strategy',
      colValue: 'Value',
      colAdjust: 'Adjustment',
      colReason: 'Reason',
      criticalFallback: 'High value & high risk = organizational fragility',
      criticalEmpty: 'No high-value high-risk key persons',
      paretoShare: 'Top {n} contribute {pct}%',
      paretoTop: 'Top contributors',
      effAvg: 'Avg Performance',
      effMax: 'Max',
      effMin: 'Min',
      effStd: 'Std Dev (σ)',
      effGap: 'Gap',
      people: 'people',
    },
  },

  pages2: {
    dashboard: {
      pending: 'Pending Evaluations ({n})',
      refresh: 'Refresh',
      inProgress: 'Evaluations in Progress',
      riskDist: 'Team Risk Distribution',
      high: 'High',
      medium: 'Medium',
      low: 'Low',
      view: 'View',
      colEmp: 'Employee ID',
      colPeriod: 'Period',
      colScore: 'Score',
      colStatus: 'Status',
      colOp: 'Action',
      empty: 'No pending evaluations',
      loading: 'Loading…',
    },
    chat: {
      welcomeTitle: 'HumanValue Assistant',
      welcomeSub: 'Your intelligent talent value analysis assistant · also the system chat console',
      hint: 'You can operate directly in chat. Try the examples below:',
      more: 'Or ask "what can you do" to see all capabilities',
    },
  },

  'v.LandingView': {
    'v.LandingView.0': '主导航',
    'v.LandingView.1':
      'HumanValue 以 Agent 为核心，融合多维度数据与真实 LLM，\n          为团队提供精准、可追溯、可行动的人才评估与成长指引。',
    'v.LandingView.2': '以代码作舟，让人才价值被看见。',
    'v.LandingView.3': 'AI 驱动的人才价值量化平台',
    'v.LandingView.4': '让每一次人才评估',
    'v.LandingView.5': '支持私有化部署',
    'v.LandingView.6': '30 秒开始',
    'v.LandingView.7': '真实场景案例',
    'v.LandingView.8': '无需信用卡',
    'v.LandingView.9': '游客体验',
    'v.LandingView.10': '免费开始',
    'v.LandingView.11': '免费注册',
    'v.LandingView.12': '有据可依',
    'v.LandingView.13': '核心能力',
    'v.LandingView.14': '案例',
    'v.LandingView.15': '功能',
    'v.LandingView.16': '登录',
    'v.LandingView.17': '关于',
  },

  'v.LoginView': {
    'v.LoginView.0': '人才价值分析与评估平台',
  },

  'v.NotFound': {
    'v.NotFound.0': '你访问的页面不存在或已被移动，请检查地址或返回首页。',
    'v.NotFound.1': '&nbsp;返回看板',
    'v.NotFound.2': '页面走丢了',
    'v.NotFound.3': '返回上一页',
  },

  'v.admin.AdminAgentTemplates': {
    'v.admin.AdminAgentTemplates.0': '搜索模板',
    'v.admin.AdminAgentTemplates.1': '暂无模板',
    'v.admin.AdminAgentTemplates.2': '模板名称',
    'v.admin.AdminAgentTemplates.3': '如 资深 HRBP Agent',
    'v.admin.AdminAgentTemplates.4': '分类',
    'v.admin.AdminAgentTemplates.5': '描述',
    'v.admin.AdminAgentTemplates.6': '你是一个...',
    'v.admin.AdminAgentTemplates.7': '关联模型',
    'v.admin.AdminAgentTemplates.8': '工具 (逗号分隔)',
    'v.admin.AdminAgentTemplates.9': '是否公开',
    'v.admin.AdminAgentTemplates.10': 'Agent 模板市场',
    'v.admin.AdminAgentTemplates.11': '公开模板所有用户可见',
    'v.admin.AdminAgentTemplates.12': '新建模板',
    'v.admin.AdminAgentTemplates.13': '实例化',
    'v.admin.AdminAgentTemplates.14': 'Refresh',
    'v.admin.AdminAgentTemplates.15': 'Cancel',
    'v.admin.AdminAgentTemplates.16': 'Delete',
    'v.admin.AdminAgentTemplates.17': 'Save',
    'v.admin.AdminAgentTemplates.18': 'Edit',
  },

  'v.admin.AdminAlerts': {
    'v.admin.AdminAlerts.0': '来源',
    'v.admin.AdminAlerts.1': '严重级别',
    'v.admin.AdminAlerts.2': 'Status',
    'v.admin.AdminAlerts.3': '暂无告警',
    'v.admin.AdminAlerts.4': '来源',
    'v.admin.AdminAlerts.5': '告警管理',
    'v.admin.AdminAlerts.6': 'Refresh',
    'v.admin.AdminAlerts.7': '重置',
  },

  'v.admin.AdminAuditLogs': {
    'v.admin.AdminAuditLogs.0': '审计日志',
    'v.admin.AdminAuditLogs.1': 'Refresh',
  },

  'v.admin.AdminBilling': {
    'v.admin.AdminBilling.0': '开始月份',
    'v.admin.AdminBilling.1': '结束月份',
    'v.admin.AdminBilling.2': '按月费用趋势',
    'v.admin.AdminBilling.3': '计费管理',
    'v.admin.AdminBilling.4': '导出账单',
  },

  'v.admin.AdminEvalCenter': {
    'v.admin.AdminEvalCenter.0': '数据集',
    'v.admin.AdminEvalCenter.1': '暂无数据集',
    'v.admin.AdminEvalCenter.2': 'Name',
    'v.admin.AdminEvalCenter.3': 'Type',
    'v.admin.AdminEvalCenter.4': '新建数据集',
    'v.admin.AdminEvalCenter.5': '评测中心',
    'v.admin.AdminEvalCenter.6': 'Refresh',
  },

  'v.admin.AdminKnowledgeOps': {
    'v.admin.AdminKnowledgeOps.0': '暂无 GraphRAG 任务',
    'v.admin.AdminKnowledgeOps.1': '任务名称',
    'v.admin.AdminKnowledgeOps.2': '知识库',
    'v.admin.AdminKnowledgeOps.3': 'Status',
    'v.admin.AdminKnowledgeOps.4': '图谱搜索',
    'v.admin.AdminKnowledgeOps.5': '知识增强',
    'v.admin.AdminKnowledgeOps.6': 'Refresh',
  },

  'v.admin.AdminLLMConfig': {
    'v.admin.AdminLLMConfig.0':
      'LLM 配置中心 —— 在此输入 API Key、base_url、模型名等，保存后立即生效并持久化到',
    'v.admin.AdminLLMConfig.1': '（gitignored），重启后自动加载。敏感字段保存后以',
  },

  'v.admin.AdminMetrics': {
    'v.admin.AdminMetrics.0': '开始时间',
    'v.admin.AdminMetrics.1': '结束时间',
    'v.admin.AdminMetrics.2': '近 30 天',
    'v.admin.AdminMetrics.3': '近 7 天',
    'v.admin.AdminMetrics.4': '自定义',
  },

  'v.admin.AdminModel': {
    'v.admin.AdminModel.0': '当前模型状态',
  },

  'v.admin.AdminModelOps': {
    'v.admin.AdminModelOps.0': '容灾策略',
    'v.admin.AdminModelOps.1': '暂无容灾策略',
    'v.admin.AdminModelOps.2': 'Name',
    'v.admin.AdminModelOps.3': 'Fallback 链',
    'v.admin.AdminModelOps.4': '新建 Fallback 链',
    'v.admin.AdminModelOps.5': '模型运维',
    'v.admin.AdminModelOps.6': 'Refresh',
  },

  'v.admin.AdminQuotaBudget': {
    'v.admin.AdminQuotaBudget.0': '配额管理',
    'v.admin.AdminQuotaBudget.1': '最近 7 天',
    'v.admin.AdminQuotaBudget.2': '最近 30 天',
    'v.admin.AdminQuotaBudget.3': '最近 90 天',
    'v.admin.AdminQuotaBudget.4': '配额与预算管理',
    'v.admin.AdminQuotaBudget.5': '当前租户配额',
    'v.admin.AdminQuotaBudget.6': '重置今日用量',
    'v.admin.AdminQuotaBudget.7': 'Refresh',
  },

  'v.admin.AdminRLHF': {
    'v.admin.AdminRLHF.0':
      'RLHF 偏好数据闭环 — 采集用户对 Chat 输出的 like/dislike 反馈，构造偏好对数据集用于 DPO/PPO 训练',
    'v.admin.AdminRLHF.1': '格式',
    'v.admin.AdminRLHF.2': '偏好对构造逻辑',
    'v.admin.AdminRLHF.3':
      '仅导出有 dislike 反馈的 assistant 消息作为 rejected 样本。若同一会话中有 like 反馈的消息，取其回复作为 chosen 样本。若会话中无 like 反馈，chosen 字段为空。',
    'v.admin.AdminRLHF.4': '采集方式',
    'v.admin.AdminRLHF.5': '存储方式',
    'v.admin.AdminRLHF.6': '下游消费',
    'v.admin.AdminRLHF.7': '数据隔离',
    'v.admin.AdminRLHF.8':
      '导出的偏好数据集可用于 DPO (Direct Preference Optimization) 或 PPO 训练，优化 LLM 输出质量。',
    'v.admin.AdminRLHF.9':
      'prompt,chosen,rejected,feedback_comment\n"用户问题","点赞回复","点踩回复","反馈备注"',
    'v.admin.AdminRLHF.10':
      'Chat 界面中，每条 assistant 消息下方有点赞/点踩按钮。点击后弹出对话框收集可选的反馈备注。',
    'v.admin.AdminRLHF.11': 'JSONL 格式（推荐用于 DPO/PPO 训练）',
    'v.admin.AdminRLHF.12': '数据按租户隔离，仅导出当前租户的反馈数据。',
    'v.admin.AdminRLHF.13': 'CSV 格式（适合用 Excel 查看）',
    'v.admin.AdminRLHF.14': 'Assistant 消息总数',
    'v.admin.AdminRLHF.15': 'JSON 字段中，结构为',
    'v.admin.AdminRLHF.16': '导出偏好数据集',
    'v.admin.AdminRLHF.17': '偏好数据集导出',
    'v.admin.AdminRLHF.18': '数据集格式说明',
    'v.admin.AdminRLHF.19': '反馈采集说明',
    'v.admin.AdminRLHF.20': '反馈存储在',
    'v.admin.AdminRLHF.21': '刷新统计',
    'v.admin.AdminRLHF.22': '反馈统计',
    'v.admin.AdminRLHF.23': '点赞数',
    'v.admin.AdminRLHF.24': '点踩数',
    'v.admin.AdminRLHF.25': '点赞率',
  },

  'v.admin.AdminReleaseOps': {
    'v.admin.AdminReleaseOps.0': 'Agent 版本',
    'v.admin.AdminReleaseOps.1': '选择 Agent',
    'v.admin.AdminReleaseOps.2': '暂无版本',
    'v.admin.AdminReleaseOps.3': '版本号',
    'v.admin.AdminReleaseOps.4': '发布新版本',
    'v.admin.AdminReleaseOps.5': '发布运维',
    'v.admin.AdminReleaseOps.6': 'Refresh',
  },

  'v.admin.AdminScheduler': {
    'v.admin.AdminScheduler.0': '暂无定时任务',
    'v.admin.AdminScheduler.1': '任务名称',
    'v.admin.AdminScheduler.2': 'Cron 表达式',
    'v.admin.AdminScheduler.3': '定时任务管理',
    'v.admin.AdminScheduler.4': '新建任务',
    'v.admin.AdminScheduler.5': 'Refresh',
  },

  'v.admin.AdminSecurity': {
    'v.admin.AdminSecurity.0': '敏感词管理',
    'v.admin.AdminSecurity.1': '搜索敏感词',
    'v.admin.AdminSecurity.2': '审核状态',
    'v.admin.AdminSecurity.3': '待审核',
    'v.admin.AdminSecurity.4': '已通过',
    'v.admin.AdminSecurity.5': '已拒绝',
    'v.admin.AdminSecurity.6': '暂无敏感词',
    'v.admin.AdminSecurity.7': '敏感词',
    'v.admin.AdminSecurity.8': '分类',
    'v.admin.AdminSecurity.9': '审核状态',
    'v.admin.AdminSecurity.10': '安全治理',
    'v.admin.AdminSecurity.11': '批量导入',
    'v.admin.AdminSecurity.12': 'Refresh',
    'v.admin.AdminSecurity.13': '新增',
  },

  'v.admin.AdminTalentMatrix': {
    'v.admin.AdminTalentMatrix.0': '人才九宫格（绩效 × 潜力）',
  },

  'v.employee.EmployeeDashboard': {
    'v.employee.EmployeeDashboard.0': '我的成长看板',
  },

  'v.employee.EmployeeFeedback': {
    'v.employee.EmployeeFeedback.0': '我的评估列表',
  },

  'v.employee.EmployeeHistory': {
    'v.employee.EmployeeHistory.0': '综合得分趋势',
    'v.employee.EmployeeHistory.1': 'Refresh',
  },

  'v.employee.EmployeeInput': {
    'v.employee.EmployeeInput.0': '录入本周工作数据',
  },

  'v.employee.GrowthPath': {
    'v.employee.GrowthPath.0': '成长路径推荐',
    'v.employee.GrowthPath.1': 'Refresh',
  },

  'v.hr.HRAuditDetail': {
    'v.hr.HRAuditDetail.0': 'HR 复核详情',
    'v.hr.HRAuditDetail.1': '评估详情加载中',
    'v.hr.HRAuditDetail.2': '未找到评估数据',
    'v.hr.HRAuditDetail.3': '`状态: ${evaluation.status}`',
  },

  'v.hr.HRDashboard': {
    'v.hr.HRDashboard.0': 'Refresh',
  },

  'v.manager.ApprovalDetail': {
    'v.manager.ApprovalDetail.0': '评估详情',
  },

  'v.manager.AttritionRisk': {
    'v.manager.AttritionRisk.0': '离职风险预警',
  },

  'v.manager.CalibrationView': {
    'v.manager.CalibrationView.0': '新建校准会',
    'v.manager.CalibrationView.1': '校准会列表',
  },

  'v.manager.Review360View': {
    'v.manager.Review360View.0': '发起环评',
    'v.manager.Review360View.1': '发起 360° 环评',
  },

  'v.manager.TeamAnalytics': {
    'v.manager.TeamAnalytics.0': '团队分析',
  },

  'v.manager.TeamROI': {
    'v.manager.TeamROI.0': '团队 ROI 分析',
  },

  'v.talent.ActionItems': {
    'v.talent.ActionItems.0': '总数',
    'v.talent.ActionItems.1': '待处理',
    'v.talent.ActionItems.2': '进行中',
    'v.talent.ActionItems.3': '已完成',
    'v.talent.ActionItems.4': '逾期',
    'v.talent.ActionItems.5': '完成率',
    'v.talent.ActionItems.6': '行动项追踪看板',
    'v.talent.ActionItems.7': '创建行动项',
  },

  'v.talent.CompensationInsights': {
    'v.talent.CompensationInsights.0': '平均总薪酬',
    'v.talent.CompensationInsights.1': '低于市场',
    'v.talent.CompensationInsights.2': '符合市场',
    'v.talent.CompensationInsights.3': '高于市场',
    'v.talent.CompensationInsights.4': '平均比率',
    'v.talent.CompensationInsights.5': '创建/更新薪酬',
    'v.talent.CompensationInsights.6': '薪酬记录',
  },

  'v.talent.DevelopmentPlans': {
    'v.talent.DevelopmentPlans.0': '个人发展计划 (IDP)',
    'v.talent.DevelopmentPlans.1': '创建发展计划',
  },

  'v.talent.GoalManagement': {
    'v.talent.GoalManagement.0': '总目标数',
    'v.talent.GoalManagement.1': '进行中',
    'v.talent.GoalManagement.2': '已完成',
    'v.talent.GoalManagement.3': '目标管理 (OKR)',
    'v.talent.GoalManagement.4': '创建目标',
  },

  'v.talent.InternalMobility': {
    'v.talent.InternalMobility.0': '内部岗位',
    'v.talent.InternalMobility.1': '发布岗位',
  },

  'v.talent.OneOnOnes': {
    'v.talent.OneOnOnes.0': '本月会议数',
    'v.talent.OneOnOnes.1': '已完成数',
  },

  'v.talent.PIPManagement': {
    'v.talent.PIPManagement.0': 'PIP 绩效改进',
    'v.talent.PIPManagement.1': '创建 PIP',
  },

  'v.talent.PulseSurvey': {
    'v.talent.PulseSurvey.0': '平均分',
    'v.talent.PulseSurvey.1': '情感分布',
  },

  'v.talent.Recognition': {
    'v.talent.Recognition.0': '本月认可数',
    'v.talent.Recognition.1': '总积分',
    'v.talent.Recognition.2': '认可动态流',
    'v.talent.Recognition.3': '发送认可',
  },

  'v.talent.SkillMatrix': {
    'v.talent.SkillMatrix.0': '添加技能评估',
    'v.talent.SkillMatrix.1': '团队技能概览',
  },

  'v.talent.SuccessionPlanning': {
    'v.talent.SuccessionPlanning.0': '关键岗位数',
    'v.talent.SuccessionPlanning.1': '候选人数',
    'v.talent.SuccessionPlanning.2': '准备度分布',
  },

  'v.talent.TalentTrends': {
    'v.talent.TalentTrends.0': '团队趋势概览',
  },

  'v.talent.TeamHealth': {
    'v.talent.TeamHealth.0': '综合健康分',
  },
}
