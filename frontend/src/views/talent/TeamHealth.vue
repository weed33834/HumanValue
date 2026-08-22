<template>
  <div class="team-health" v-loading="loading">
    <!-- ============ 大圆环：综合健康分 ============ -->
    <el-card class="mb-16">
      <div class="health-hero">
        <div class="ring-wrap">
          <el-progress
            type="dashboard"
            :percentage="healthScore"
            :width="200"
            :stroke-width="16"
            :color="ringColors"
          >
            <template #default>
              <div class="ring-inner">
                <span class="ring-score">{{ healthScore }}</span>
                <span class="ring-label">{ $t('v.talent.TeamHealth.0') }</span>
              </div>
            </template>
          </el-progress>
        </div>
        <div class="health-level">
          <span class="muted">健康等级</span>
          <el-tag size="large" :type="levelTagType(healthLevel)" effect="dark">{{
            levelLabel(healthLevel)
          }}</el-tag>
        </div>
      </div>
    </el-card>

    <!-- ============ 四个维度卡片 ============ -->
    <el-row :gutter="20" class="mb-16">
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="评估得分"
            :value="dimensions.evaluation_score || 0"
            :precision="1"
            value-style="color: var(--el-color-primary)"
          />
          <el-progress
            :percentage="Number(dimensions.evaluation_score || 0)"
            :show-text="false"
            :stroke-width="6"
            style="margin-top: 8px"
          />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="行动完成率"
            :value="dimensions.action_completion_rate || 0"
            suffix="%"
            value-style="color: var(--el-color-success)"
          />
          <el-progress
            :percentage="Number(dimensions.action_completion_rate || 0)"
            :show-text="false"
            :stroke-width="6"
            status="success"
            style="margin-top: 8px"
          />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="敬业度"
            :value="dimensions.engagement_score || 0"
            :precision="1"
            value-style="color: var(--el-color-warning)"
          />
          <el-progress
            :percentage="Number(dimensions.engagement_score || 0)"
            :show-text="false"
            :stroke-width="6"
            status="warning"
            style="margin-top: 8px"
          />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="认可活跃度"
            :value="dimensions.recognition_activity || 0"
            value-style="color: var(--el-color-danger)"
          />
          <el-progress
            :percentage="Math.min(Number(dimensions.recognition_activity || 0), 100)"
            :show-text="false"
            :stroke-width="6"
            status="exception"
            style="margin-top: 8px"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 底部统计 ============ -->
    <el-card>
      <template #header><span>底部统计</span></template>
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="总评估数" :value="stats.total_evaluations || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="总行动项" :value="stats.total_action_items || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="脉搏回复数" :value="stats.pulse_responses || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="认可数" :value="stats.total_recognitions || 0" />
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { growthApi } from '@/api/client'

const loading = ref(false)
const healthData = ref({})

const healthScore = computed(() => Number(healthData.value.overall_score || 0))
const dimensions = computed(() => healthData.value.dimensions || {})
const stats = computed(() => healthData.value.stats || {})

const healthLevel = computed(() => {
  const s = healthScore.value
  if (s >= 85) return 'excellent'
  if (s >= 70) return 'good'
  if (s >= 50) return 'fair'
  return 'poor'
})

const ringColors = [
  { color: '#f56c6c', percentage: 50 },
  { color: '#e6a23c', percentage: 70 },
  { color: '#67c23a', percentage: 85 },
  { color: '#409eff', percentage: 100 },
]

async function loadHealth() {
  loading.value = true
  try {
    const res = await growthApi.teamHealth()
    healthData.value = res || {}
  } catch (err) {
    ElMessage.error(err.message || '加载团队健康度失败')
  } finally {
    loading.value = false
  }
}

// ============ 通用工具 ============
function levelLabel(l) {
  return { excellent: '优秀', good: '良好', fair: '一般', poor: '需关注' }[l] || l
}
function levelTagType(l) {
  return { excellent: 'success', good: 'success', fair: 'warning', poor: 'danger' }[l] || 'info'
}

onMounted(() => {
  loadHealth()
})
</script>

<style scoped>
.mb-16 {
  margin-bottom: 16px;
}
.muted {
  color: #909399;
  font-size: 13px;
}
.health-hero {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48px;
  padding: 20px 0;
}
.ring-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.ring-score {
  font-size: 36px;
  font-weight: 700;
  color: var(--el-color-primary);
}
.ring-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.health-level {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
</style>
