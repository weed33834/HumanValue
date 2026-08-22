<template>
  <div class="talent-trends">
    <!-- ============ 团队趋势概览 ============ -->
    <el-card v-loading="overviewLoading" class="mb-16">
      <template #header><span>{ $t('v.talent.TalentTrends.0') }</span></template>
      <el-table :data="teamOverview" style="width: 100%" empty-text="暂无趋势数据">
        <el-table-column prop="period" label="周期" width="140" />
        <el-table-column label="平均分" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="scoreTagType(row.avg_score)">{{ row.avg_score }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="max_score" label="最高分" width="110" sortable />
        <el-table-column prop="min_score" label="最低分" width="110" sortable />
        <el-table-column prop="evaluation_count" label="评估数" width="110" sortable />
        <el-table-column label="趋势" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="trendTagType(row.trend)" effect="plain">
              {{ trendLabel(row.trend) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-row :gutter="20">
      <!-- ============ 员工趋势查询 ============ -->
      <el-col :span="14">
        <el-card v-loading="empLoading">
          <template #header><span>员工趋势查询</span></template>
          <el-form :inline="true" class="filter-form">
            <el-form-item label="员工ID">
              <el-input
                v-model="employeeQuery"
                placeholder="例如 E1001"
                style="width: 220px"
                @keyup.enter="loadEmployeeTrend"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="empLoading" @click="loadEmployeeTrend"
                >查询</el-button
              >
            </el-form-item>
          </el-form>

          <div v-if="employeeTrendList.length" class="trend-list">
            <el-timeline>
              <el-timeline-item
                v-for="(item, idx) in employeeTrendList"
                :key="idx"
                :type="scoreTimelineType(item.score)"
                :timestamp="item.period"
                placement="top"
              >
                <div class="trend-item">
                  <span class="trend-score-text">得分：{{ item.score }}</span>
                  <el-tag size="small" :type="directionTagType(item.direction)">
                    {{ directionLabel(item.direction) }}
                  </el-tag>
                  <span v-if="item.delta != null" class="muted"
                    >变化 {{ item.delta > 0 ? '+' : '' }}{{ item.delta }}</span
                  >
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
          <el-empty v-else description="输入员工ID查询得分趋势" :image-size="80" />
        </el-card>
      </el-col>

      <!-- ============ 九宫格移动轨迹 ============ -->
      <el-col :span="10">
        <el-card>
          <template #header><span>九宫格移动轨迹</span></template>
          <div class="grid-wrap">
            <div class="grid-axis-y">
              <span>高潜力</span>
              <span>中潜力</span>
              <span>低潜力</span>
            </div>
            <div class="grid-container">
              <div
                v-for="(cell, idx) in gridCells"
                :key="idx"
                class="grid-cell"
                :class="{ active: cell.trajectory }"
              >
                <span class="cell-label">{{ cell.label }}</span>
                <span v-if="cell.trajectory" class="cell-marker">{{ cell.trajectory }}</span>
              </div>
            </div>
            <div class="grid-axis-x">
              <span>低绩效</span>
              <span>中绩效</span>
              <span>高绩效</span>
            </div>
          </div>
          <p class="muted grid-tip">
            虚线方向表示绩效轴（横向），潜力轴（纵向），轨迹数字代表周期顺序。
          </p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { growthApi } from '@/api/client'

const overviewLoading = ref(false)
const empLoading = ref(false)
const teamOverview = ref([])
const employeeQuery = ref('')
const employeeTrendList = ref([])
const gridTrajectory = ref([])

async function loadOverview() {
  overviewLoading.value = true
  try {
    const res = await growthApi.teamTrendOverview()
    teamOverview.value = res.trend || res.items || res.periods || []
    gridTrajectory.value = res.trajectory || []
  } catch (err) {
    ElMessage.error(err.message || '加载团队趋势概览失败')
  } finally {
    overviewLoading.value = false
  }
}

async function loadEmployeeTrend() {
  if (!employeeQuery.value.trim()) {
    ElMessage.warning('请输入员工ID')
    return
  }
  empLoading.value = true
  try {
    const res = await growthApi.employeeTrend(employeeQuery.value.trim(), {})
    employeeTrendList.value = res.items || res.trends || res || []
    if (!employeeTrendList.value.length) {
      ElMessage.info('未查询到该员工的趋势数据')
    }
  } catch (err) {
    ElMessage.error(err.message || '查询员工趋势失败')
  } finally {
    empLoading.value = false
  }
}

// ============ 九宫格 ============
// 3x3 网格：行=潜力(高/中/低)，列=绩效(低/中/高)
const gridLabels = ['明星', '明星', '潜力股', '中坚', '中坚', '核心', '问题', '待提升', '稳定']

const gridCells = computed(() => {
  const cells = gridLabels.map((label, idx) => ({ label, idx, trajectory: '' }))
  // 将轨迹数据按顺序标记到对应格子
  ;(gridTrajectory.value || []).forEach((point, order) => {
    const row = potentialIndex(point.potential)
    const col = performanceIndex(point.performance)
    const cellIdx = row * 3 + col
    if (cells[cellIdx]) {
      cells[cellIdx].trajectory = String(order + 1)
    }
  })
  return cells
})

function potentialIndex(p) {
  const v = String(p || '').toLowerCase()
  if (v.startsWith('high') || v === '高' || Number(p) >= 7) return 0
  if (v.startsWith('low') || v === '低' || Number(p) < 4) return 2
  return 1
}
function performanceIndex(p) {
  const v = String(p || '').toLowerCase()
  if (v.startsWith('high') || v === '高' || Number(p) >= 7) return 2
  if (v.startsWith('low') || v === '低' || Number(p) < 4) return 0
  return 1
}

// ============ 通用工具 ============
function scoreTagType(score) {
  if (score >= 85) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}
function scoreTimelineType(score) {
  if (score >= 85) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}
function trendLabel(t) {
  return { up: '上升', down: '下降', flat: '持平' }[t] || t || '持平'
}
function trendTagType(t) {
  return { up: 'success', down: 'danger', flat: 'info' }[t] || 'info'
}
function directionLabel(d) {
  return { up: '↑ 上升', down: '↓ 下降', flat: '→ 持平' }[d] || d || '→ 持平'
}
function directionTagType(d) {
  return { up: 'success', down: 'danger', flat: 'info' }[d] || 'info'
}

onMounted(() => {
  loadOverview()
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
.filter-form {
  margin-bottom: 12px;
}
.trend-list {
  margin-top: 12px;
}
.trend-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.trend-score-text {
  font-weight: 600;
}
.grid-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.grid-axis-y {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  height: 240px;
  position: absolute;
  left: 0;
  top: 0;
  padding-left: 4px;
  font-size: 12px;
  color: #909399;
}
.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  width: 100%;
  position: relative;
  padding-left: 60px;
}
.grid-cell {
  height: 80px;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: #fafafa;
}
.grid-cell.active {
  border: 2px solid var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.cell-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}
.cell-marker {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}
.grid-axis-x {
  display: flex;
  justify-content: space-around;
  width: calc(100% - 60px);
  margin-left: 60px;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}
.grid-tip {
  margin-top: 12px;
  font-size: 12px;
  text-align: center;
}
</style>
