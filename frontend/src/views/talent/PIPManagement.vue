<template>
  <div class="pip-management">
    <!-- ============ PIP 列表 ============ -->
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{ $t('v.talent.PIPManagement.0') }</span>
          <el-button type="primary" size="small" @click="openCreateDialog"
            >{ $t('v.talent.PIPManagement.1') }</el-button
          >
        </div>
      </template>

      <el-table :data="pipList" style="width: 100%" empty-text="暂无 PIP 记录">
        <el-table-column prop="employee_id" label="员工" width="120" />
        <el-table-column prop="reason" label="原因" min-width="180">
          <template #default="{ row }">
            <span class="muted"
              >{{ (row.reason || '').slice(0, 50)
              }}{{ (row.reason || '').length > 50 ? '...' : '' }}</span
            >
          </template>
        </el-table-column>
        <el-table-column label="开始日期" width="120">
          <template #default="{ row }">{{ formatDate(row.start_date) }}</template>
        </el-table-column>
        <el-table-column label="结束日期" width="120">
          <template #default="{ row }">{{ formatDate(row.end_date) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{
              statusLabel(row.status)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评审频率" width="110">
          <template #default="{ row }">{{ reviewLabel(row.review_frequency) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openDetailDialog(row)"
              >详情</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ============ 创建 PIP 对话框 ============ -->
    <el-dialog v-model="showCreateDialog" title="创建 PIP" width="640px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="员工" required>
          <el-input v-model="createForm.employee_id" placeholder="例如 E1001" />
        </el-form-item>
        <el-form-item label="原因" required>
          <el-input
            v-model="createForm.reason"
            type="textarea"
            :rows="2"
            placeholder="进入 PIP 的原因"
          />
        </el-form-item>
        <el-form-item label="改进目标">
          <div v-for="(goal, idx) in createForm.improvement_goals" :key="idx" class="line-row">
            <el-input v-model="goal.description" placeholder="改进目标描述" style="flex: 1" />
            <el-button
              type="danger"
              link
              icon="Delete"
              @click="createForm.improvement_goals.splice(idx, 1)"
            />
          </div>
          <el-button
            type="primary"
            link
            icon="Plus"
            @click="createForm.improvement_goals.push({ description: '' })"
            >添加目标</el-button
          >
        </el-form-item>
        <el-form-item label="里程碑">
          <div v-for="(ms, idx) in createForm.milestones" :key="idx" class="line-row">
            <el-input v-model="ms.title" placeholder="里程碑标题" style="flex: 1" />
            <el-date-picker
              v-model="ms.target_date"
              type="date"
              placeholder="目标日期"
              value-format="YYYY-MM-DD"
              style="width: 160px"
            />
            <el-button
              type="danger"
              link
              icon="Delete"
              @click="createForm.milestones.splice(idx, 1)"
            />
          </div>
          <el-button
            type="primary"
            link
            icon="Plus"
            @click="createForm.milestones.push({ title: '', target_date: '' })"
            >添加里程碑</el-button
          >
        </el-form-item>
        <el-form-item label="时间范围" required>
          <el-date-picker
            v-model="createForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="评审频率">
          <el-select v-model="createForm.review_frequency" style="width: 100%">
            <el-option label="每周" value="weekly" />
            <el-option label="每两周" value="biweekly" />
            <el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createPIP">创建</el-button>
      </template>
    </el-dialog>

    <!-- ============ PIP 详情对话框 ============ -->
    <el-dialog v-model="showDetailDialog" title="PIP 详情" width="640px">
      <template v-if="currentPIP">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="员工">{{ currentPIP.employee_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag size="small" :type="statusTagType(currentPIP.status)">{{
              statusLabel(currentPIP.status)
            }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始日期">{{
            formatDate(currentPIP.start_date)
          }}</el-descriptions-item>
          <el-descriptions-item label="结束日期">{{
            formatDate(currentPIP.end_date)
          }}</el-descriptions-item>
          <el-descriptions-item label="评审频率">{{
            reviewLabel(currentPIP.review_frequency)
          }}</el-descriptions-item>
          <el-descriptions-item label="原因" :span="2">{{
            currentPIP.reason
          }}</el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">改进目标</el-divider>
        <div
          v-if="currentPIP.improvement_goals && currentPIP.improvement_goals.length"
          class="goal-list"
        >
          <div v-for="(goal, idx) in currentPIP.improvement_goals" :key="idx" class="goal-item">
            <el-checkbox v-model="goal.achieved" @change="markGoal(idx)">{{
              goal.description
            }}</el-checkbox>
            <el-tag v-if="goal.achieved" size="small" type="success">已达成</el-tag>
          </div>
        </div>
        <el-empty v-else description="暂无改进目标" :image-size="60" />

        <el-divider content-position="left">里程碑进度</el-divider>
        <div
          v-if="currentPIP.milestones && currentPIP.milestones.length"
          class="milestone-progress"
        >
          <div v-for="(ms, idx) in currentPIP.milestones" :key="idx" class="milestone-row">
            <span class="ms-title">{{ ms.title }}</span>
            <span class="muted">{{ formatDate(ms.target_date) }}</span>
            <el-progress
              :percentage="Number(ms.progress || 0)"
              :status="ms.progress >= 100 ? 'success' : undefined"
              style="flex: 1"
            />
          </div>
        </div>
        <el-empty v-else description="暂无里程碑" :image-size="60" />

        <el-divider content-position="left">结果备注</el-divider>
        <el-input
          v-model="detailForm.result_notes"
          type="textarea"
          :rows="3"
          placeholder="PIP 结果备注"
        />
      </template>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" :loading="updating" @click="saveDetail">保存备注</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { talentApi } from '@/api/client'

const loading = ref(false)
const pipList = ref([])

async function loadPIPs() {
  loading.value = true
  try {
    const res = await talentApi.listPIPs({})
    pipList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载 PIP 列表失败')
  } finally {
    loading.value = false
  }
}

// ============ 创建 PIP ============
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({
  employee_id: '',
  reason: '',
  improvement_goals: [{ description: '' }],
  milestones: [],
  dateRange: [],
  review_frequency: 'weekly',
})

function openCreateDialog() {
  createForm.value = {
    employee_id: '',
    reason: '',
    improvement_goals: [{ description: '' }],
    milestones: [],
    dateRange: [],
    review_frequency: 'weekly',
  }
  showCreateDialog.value = true
}

async function createPIP() {
  if (
    !createForm.value.employee_id.trim() ||
    !createForm.value.reason.trim() ||
    !createForm.value.dateRange.length
  ) {
    ElMessage.warning('请填写员工、原因和时间范围')
    return
  }
  creating.value = true
  try {
    const [startDate, endDate] = createForm.value.dateRange
    await talentApi.createPIP({
      employee_id: createForm.value.employee_id.trim(),
      reason: createForm.value.reason.trim(),
      improvement_goals: createForm.value.improvement_goals
        .filter((g) => g.description.trim())
        .map((g) => ({ description: g.description.trim() })),
      milestones: createForm.value.milestones
        .filter((m) => m.title.trim())
        .map((m) => ({ title: m.title.trim(), target_date: m.target_date || null })),
      start_date: startDate,
      end_date: endDate,
      review_frequency: createForm.value.review_frequency,
    })
    ElMessage.success('PIP 已创建')
    showCreateDialog.value = false
    await loadPIPs()
  } catch (err) {
    ElMessage.error(err.message || '创建 PIP 失败')
  } finally {
    creating.value = false
  }
}

// ============ PIP 详情 ============
const showDetailDialog = ref(false)
const currentPIP = ref(null)
const updating = ref(false)
const detailForm = ref({ result_notes: '' })

async function openDetailDialog(row) {
  try {
    const res = await talentApi.getPIP(row.pip_id || row.id)
    currentPIP.value = res || row
  } catch (err) {
    ElMessage.error(err.message || '加载详情失败')
    currentPIP.value = row
  }
  detailForm.value = { result_notes: currentPIP.value.result_notes || '' }
  showDetailDialog.value = true
}

function markGoal(_idx) {
  // 本地变更，保存时提交
}

async function saveDetail() {
  updating.value = true
  try {
    await talentApi.updatePIP(currentPIP.value.pip_id || currentPIP.value.id, {
      result_notes: detailForm.value.result_notes,
      improvement_goals: currentPIP.value.improvement_goals,
    })
    ElMessage.success('备注已保存')
    await loadPIPs()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    updating.value = false
  }
}

// ============ 通用工具 ============
function statusLabel(s) {
  return (
    {
      active: '进行中',
      completed: '已完成',
      successful: '改进成功',
      unsuccessful: '未达标',
      cancelled: '已取消',
    }[s] || s
  )
}
function statusTagType(s) {
  return (
    {
      active: 'warning',
      completed: 'success',
      successful: 'success',
      unsuccessful: 'danger',
      cancelled: 'info',
    }[s] || 'info'
  )
}
function reviewLabel(r) {
  return { weekly: '每周', biweekly: '每两周', monthly: '每月' }[r] || r
}
function formatDate(d) {
  if (!d) return '-'
  try {
    return new Date(d).toLocaleDateString('zh-CN')
  } catch {
    return d
  }
}

onMounted(() => {
  loadPIPs()
})
</script>

<style scoped>
.muted {
  color: #909399;
  font-size: 13px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.line-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.goal-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.goal-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.milestone-progress {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.milestone-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ms-title {
  min-width: 140px;
  font-weight: 500;
}
</style>
