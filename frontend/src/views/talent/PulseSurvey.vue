<template>
  <div class="pulse-survey">
    <!-- ============ 顶部：平均分 + 情感分布 ============ -->
    <el-row :gutter="20" class="mb-16">
      <el-col :span="8">
        <el-card v-loading="analyticsLoading">
          <el-statistic
            :title="$t('v.talent.PulseSurvey.0')"
            :value="analytics.average_score || 0"
            :precision="2"
            value-style="color: var(--el-color-primary)"
          />
          <p class="muted">基于 {{ analytics.response_count || 0 }} 条回复</p>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card v-loading="analyticsLoading">
          <template #header><span>{ $t('v.talent.PulseSurvey.1') }</span></template>
          <div class="sentiment-row">
            <div v-for="item in sentimentList" :key="item.label" class="sentiment-item">
              <div class="sentiment-bar-wrap">
                <div
                  class="sentiment-bar"
                  :style="{ width: item.percent + '%', background: item.color }"
                ></div>
              </div>
              <div class="sentiment-label">
                <span>{{ item.label }}</span>
                <span class="muted">{{ item.count }} ({{ item.percent }}%)</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 趋势图 ============ -->
    <el-card class="mb-16" v-loading="analyticsLoading">
      <template #header><span>各周期均分趋势</span></template>
      <div v-if="trendList.length" class="trend-chart">
        <div v-for="t in trendList" :key="t.period" class="trend-col">
          <div class="trend-bar-wrap">
            <div
              class="trend-bar"
              :style="{ height: (t.score / 5) * 100 + '%', background: trendColor(t.score) }"
            >
              <span class="trend-score">{{ t.score }}</span>
            </div>
          </div>
          <span class="trend-period">{{ t.period }}</span>
        </div>
      </div>
      <el-empty v-else description="暂无趋势数据" :image-size="60" />
    </el-card>

    <!-- ============ 调研题管理 ============ -->
    <el-card class="mb-16" v-loading="surveyLoading">
      <template #header>
        <div class="card-header">
          <span>调研题目管理</span>
          <el-button type="primary" size="small" @click="openCreateSurveyDialog"
            >创建调研题目</el-button
          >
        </div>
      </template>
      <el-table :data="surveyList" style="width: 100%" empty-text="暂无调研题目">
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="question" label="问题" min-width="220" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '进行中' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_count" label="回复数" width="100" />
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            <span class="muted">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ============ 最近回复列表 ============ -->
    <el-card v-loading="analyticsLoading">
      <template #header><span>最近回复</span></template>
      <el-table :data="recentResponses" style="width: 100%" empty-text="暂无回复">
        <el-table-column prop="employee_id" label="员工" width="120" />
        <el-table-column prop="score" label="评分" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="scoreTagType(row.score)">{{ row.score }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="情感" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="sentimentTagType(row.sentiment)">{{
              sentimentLabel(row.sentiment)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="comment" label="评论" min-width="220" />
        <el-table-column label="时间" width="160">
          <template #default="{ row }">
            <span class="muted">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ============ 创建调研题目对话框 ============ -->
    <el-dialog v-model="showCreateDialog" title="创建调研题目" width="560px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" placeholder="例如 本月敬业度调研" maxlength="256" />
        </el-form-item>
        <el-form-item label="问题" required>
          <el-input
            v-model="createForm.question"
            type="textarea"
            :rows="3"
            placeholder="调研问题内容"
          />
        </el-form-item>
        <el-form-item label="周期">
          <el-input v-model="createForm.period" placeholder="例如 2026-W32" />
        </el-form-item>
        <el-form-item label="评分范围">
          <el-select v-model="createForm.scale_type" style="width: 100%">
            <el-option label="1-5 分" value="1-5" />
            <el-option label="1-10 分" value="1-10" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createSurvey">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { engagementApi } from '@/api/client'

const analyticsLoading = ref(false)
const surveyLoading = ref(false)
const analytics = ref({})
const surveyList = ref([])
const recentResponses = ref([])

const sentimentList = computed(() => {
  const dist = analytics.value.sentiment_distribution || {}
  const total = (dist.positive || 0) + (dist.neutral || 0) + (dist.negative || 0) || 1
  return [
    {
      label: '积极',
      count: dist.positive || 0,
      percent: Math.round(((dist.positive || 0) / total) * 100),
      color: '#67c23a',
    },
    {
      label: '中性',
      count: dist.neutral || 0,
      percent: Math.round(((dist.neutral || 0) / total) * 100),
      color: '#909399',
    },
    {
      label: '消极',
      count: dist.negative || 0,
      percent: Math.round(((dist.negative || 0) / total) * 100),
      color: '#f56c6c',
    },
  ]
})

const trendList = computed(() => analytics.value.trends || [])

async function loadAnalytics() {
  analyticsLoading.value = true
  try {
    const res = await engagementApi.pulseAnalytics({})
    analytics.value = res || {}
    recentResponses.value = res.recent_responses || []
  } catch (err) {
    ElMessage.error(err.message || '加载脉搏分析失败')
  } finally {
    analyticsLoading.value = false
  }
}

async function loadSurveys() {
  surveyLoading.value = true
  try {
    const res = await engagementApi.listPulseSurveys({})
    surveyList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载调研题目失败')
  } finally {
    surveyLoading.value = false
  }
}

// ============ 创建调研题目 ============
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({ title: '', question: '', period: '', scale_type: '1-5' })

function openCreateSurveyDialog() {
  createForm.value = { title: '', question: '', period: '', scale_type: '1-5' }
  showCreateDialog.value = true
}

async function createSurvey() {
  if (!createForm.value.title.trim() || !createForm.value.question.trim()) {
    ElMessage.warning('请填写标题和问题')
    return
  }
  creating.value = true
  try {
    await engagementApi.createPulseSurvey({
      title: createForm.value.title.trim(),
      question: createForm.value.question.trim(),
      period: createForm.value.period || '',
      scale_type: createForm.value.scale_type,
    })
    ElMessage.success('调研题目已创建')
    showCreateDialog.value = false
    await loadSurveys()
  } catch (err) {
    ElMessage.error(err.message || '创建调研题目失败')
  } finally {
    creating.value = false
  }
}

// ============ 通用工具 ============
function scoreTagType(score) {
  if (score >= 4) return 'success'
  if (score >= 3) return 'warning'
  return 'danger'
}
function sentimentLabel(s) {
  return { positive: '积极', neutral: '中性', negative: '消极' }[s] || s
}
function sentimentTagType(s) {
  return { positive: 'success', neutral: 'info', negative: 'danger' }[s] || 'info'
}
function trendColor(score) {
  if (score >= 4) return '#67c23a'
  if (score >= 3) return '#e6a23c'
  return '#f56c6c'
}
function formatTime(iso) {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}

onMounted(() => {
  loadAnalytics()
  loadSurveys()
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sentiment-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sentiment-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sentiment-bar-wrap {
  height: 18px;
  background: #f0f2f5;
  border-radius: 9px;
  overflow: hidden;
}
.sentiment-bar {
  height: 100%;
  border-radius: 9px;
  transition: width 0.3s;
}
.sentiment-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}
.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  height: 220px;
  padding: 12px 0;
}
.trend-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 60px;
  height: 100%;
}
.trend-bar-wrap {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.trend-bar {
  width: 60%;
  min-height: 8px;
  border-radius: 6px 6px 0 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  padding-top: 4px;
}
.trend-score {
  font-weight: 600;
}
.trend-period {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
</style>
