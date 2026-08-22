<template>
  <div class="admin-rlhf">
    <el-alert :title="$t('v.admin.AdminRLHF.0')" type="info" show-icon :closable="false" />

    <!-- 反馈统计概览 -->
    <div class="section-title">
      <el-icon><DataAnalysis /></el-icon>
      反馈统计
    </div>
    <el-row :gutter="20" v-loading="statsLoading">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats.total_messages || 0 }}</div>
          <div class="stat-label">{ $t('v.admin.AdminRLHF.14') }</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-liked">
          <div class="stat-value">{{ stats.liked || 0 }}</div>
          <div class="stat-label">{ $t('v.admin.AdminRLHF.23') }</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-disliked">
          <div class="stat-value">{{ stats.disliked || 0 }}</div>
          <div class="stat-label">{ $t('v.admin.AdminRLHF.24') }</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ likeRatePercent }}%</div>
          <div class="stat-label">{ $t('v.admin.AdminRLHF.25') }</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 点赞率进度条 -->
    <el-card shadow="never" class="progress-card" v-if="!statsLoading">
      <div class="progress-label">
        <span>反馈覆盖率: {{ ratedCount }} / {{ stats.total_messages || 0 }}</span>
        <span>无反馈: {{ stats.no_feedback || 0 }}</span>
      </div>
      <el-progress
        :percentage="coveragePercent"
        :color="coveragePercent > 50 ? '#67c23a' : '#e6a23c'"
        :stroke-width="10"
      />
    </el-card>

    <el-divider />

    <!-- 偏好数据集导出 -->
    <div class="section-title">
      <el-icon><Download /></el-icon>
      偏好数据集导出
    </div>
    <el-card shadow="never">
      <el-form :inline="true" label-width="80px">
        <el-form-item :label="$t('v.admin.AdminRLHF.1')">
          <el-radio-group v-model="exportFormat" size="small">
            <el-radio-button label="jsonl">JSONL</el-radio-button>
            <el-radio-button label="csv">CSV</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="exportLoading" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出偏好数据集
          </el-button>
          <el-button @click="loadStats" icon="RefreshLeft" size="small"
            >{ $t('v.admin.AdminRLHF.21') }</el-button
          >
        </el-form-item>
      </el-form>

      <el-divider content-position="left">
        <span class="divider-text">{ $t('v.admin.AdminRLHF.18') }</span>
      </el-divider>

      <div class="format-doc">
        <h4>{ $t('v.admin.AdminRLHF.11') }</h4>
        <pre class="code-block">
每行一个 JSON 对象：
{
  "prompt": "用户问题",
  "chosen": "用户点赞的回复（正样本）",
  "rejected": "用户点踩的回复（负样本）",
  "feedback_comment": "用户反馈备注",
  "session_id": "会话ID",
  "message_id": "消息ID"
}</pre>

        <h4>{ $t('v.admin.AdminRLHF.13') }</h4>
        <pre class="code-block">{ $t('v.admin.AdminRLHF.9') }</pre>

        <el-alert
          type="warning"
          :closable="false"
          :title="$t('v.admin.AdminRLHF.2')"
          :description="$t('v.admin.AdminRLHF.3')"
          show-icon
        />
      </div>
    </el-card>

    <el-divider />

    <!-- 反馈采集说明 -->
    <div class="section-title">
      <el-icon><InfoFilled /></el-icon>
      反馈采集说明
    </div>
    <el-card shadow="never">
      <el-descriptions :column="1" border>
        <el-descriptions-item :label="$t('v.admin.AdminRLHF.4')">
          Chat 界面中，每条 assistant 消息下方有点赞/点踩按钮。点击后弹出对话框收集可选的反馈备注。
        </el-descriptions-item>
        <el-descriptions-item :label="$t('v.admin.AdminRLHF.5')">
          反馈存储在 <code>chat_messages.metadata</code> JSON 字段中，结构为
          <code>{"feedback": {"rating": "like|dislike", "comment": "..."}}</code>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('v.admin.AdminRLHF.6')">
          导出的偏好数据集可用于 DPO (Direct Preference Optimization) 或 PPO 训练，优化 LLM
          输出质量。
        </el-descriptions-item>
        <el-descriptions-item :label="$t('v.admin.AdminRLHF.7')">
          数据按租户隔离，仅导出当前租户的反馈数据。
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '@/api/client'

const statsLoading = ref(false)
const exportLoading = ref(false)
const exportFormat = ref('jsonl')
const stats = ref({})

const ratedCount = computed(() => (stats.value.liked || 0) + (stats.value.disliked || 0))
const likeRatePercent = computed(() => {
  const rate = stats.value.like_rate || 0
  return (rate * 100).toFixed(1)
})
const coveragePercent = computed(() => {
  const total = stats.value.total_messages || 0
  if (!total) return 0
  return Math.round((ratedCount.value / total) * 100)
})

async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await chatApi.feedbackStats()
  } catch {
    ElMessage.error('加载反馈统计失败')
  } finally {
    statsLoading.value = false
  }
}

async function handleExport() {
  exportLoading.value = true
  try {
    const blob = await chatApi.exportDataset(exportFormat.value)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `preference_dataset.${exportFormat.value}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('偏好数据集已下载')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.admin-rlhf {
  padding: 10px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  margin: 16px 0 12px;
}
.stat-card {
  text-align: center;
  margin-bottom: 12px;
}
.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}
.stat-liked .stat-value {
  color: var(--el-color-success);
}
.stat-disliked .stat-value {
  color: var(--el-color-danger);
}
.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
.progress-card {
  margin-top: 12px;
}
.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.format-doc {
  padding: 12px 0;
}
.format-doc h4 {
  margin: 16px 0 8px;
  font-size: 14px;
}
.code-block {
  background: var(--el-fill-color-light);
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  margin: 0;
}
.divider-text {
  font-size: 14px;
  font-weight: 600;
}
code {
  background: var(--el-fill-color);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}
</style>
