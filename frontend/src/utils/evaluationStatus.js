// 评估状态 -> 中文标签 / el-tag 类型的统一映射
// HumanValue 简化版：无审批流

const STATUS_LABELS = {
  processing: '评估中',
  completed: '已完成',
  error: '评估失败',
  // 向后兼容
  ai_drafted: '已完成',
  manager_review: '已完成',
  hr_audit: '已完成',
  approved: '已完成',
  rejected: '已完成',
}

const STATUS_TAG_TYPES = {
  processing: 'warning',
  completed: 'success',
  error: 'danger',
  // 向后兼容
  ai_drafted: 'success',
  manager_review: 'success',
  hr_audit: 'success',
  approved: 'success',
  rejected: 'success',
}

const RISK_TAG_TYPES = {
  critical: 'error',
  high: 'warning',
  medium: 'warning',
  low: 'info',
}

export function statusLabel(status) {
  return STATUS_LABELS[status] || status
}

export function statusTagType(status) {
  return STATUS_TAG_TYPES[status] || 'info'
}

export function riskTagType(level) {
  return RISK_TAG_TYPES[level] || 'info'
}
