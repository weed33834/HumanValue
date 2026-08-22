<template>
  <div class="succession-planning">
    <!-- ============ 继任管线概览 ============ -->
    <el-row :gutter="20" class="mb-16">
      <el-col :span="8">
        <el-card v-loading="summaryLoading">
          <el-statistic
            :title="$t('v.talent.SuccessionPlanning.0')"
            :value="summary.key_positions || 0"
            value-style="color: var(--el-color-primary)"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card v-loading="summaryLoading">
          <el-statistic
            :title="$t('v.talent.SuccessionPlanning.1')"
            :value="summary.candidates || 0"
            value-style="color: var(--el-color-warning)"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card v-loading="summaryLoading">
          <template #header><span>{ $t('v.talent.SuccessionPlanning.2') }</span></template>
          <div class="readiness-row">
            <div v-for="r in readinessList" :key="r.label" class="readiness-item">
              <el-tag size="small" :type="r.type">{{ r.label }}</el-tag>
              <span class="muted">{{ r.count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 计划列表 ============ -->
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>继任计划列表</span>
          <el-button type="primary" size="small" @click="openCreateDialog">创建继任计划</el-button>
        </div>
      </template>
      <el-table :data="planList" style="width: 100%" empty-text="暂无继任计划">
        <el-table-column prop="position_title" label="岗位" min-width="160" />
        <el-table-column prop="candidate_id" label="候选人" width="120" />
        <el-table-column label="准备度" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="readinessTagType(row.readiness)">{{
              readinessLabel(row.readiness)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{
              statusLabel(row.status)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="development_gaps" label="发展差距" min-width="200">
          <template #default="{ row }">
            <span class="muted">{{ row.development_gaps || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openEditDialog(row)"
              >更新</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ============ 创建/更新继任计划对话框 ============ -->
    <el-dialog
      v-model="showDialog"
      :title="editingId ? '更新继任计划' : '创建继任计划'"
      width="560px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="岗位名称" required>
          <el-input v-model="form.position_title" placeholder="例如 研发总监" />
        </el-form-item>
        <el-form-item label="候选人" required>
          <el-input v-model="form.candidate_id" placeholder="例如 E1001" />
        </el-form-item>
        <el-form-item label="准备度">
          <el-select v-model="form.readiness" style="width: 100%">
            <el-option label="就绪 (Ready Now)" value="ready-now" />
            <el-option label="1-2年内就绪 (Ready 1-2)" value="1-2-years" />
            <el-option label="2年以上 (Ready 2+)" value="3-plus-years" />
          </el-select>
        </el-form-item>
        <el-form-item label="发展差距">
          <el-input
            v-model="form.development_gaps"
            type="textarea"
            :rows="3"
            placeholder="候选人需要弥补的能力差距"
          />
        </el-form-item>
        <el-form-item label="风险备注">
          <el-input
            v-model="form.risk_notes"
            type="textarea"
            :rows="2"
            placeholder="离职风险或其他备注"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="识别中" value="identified" />
            <el-option label="培养中" value="developing" />
            <el-option label="已就绪" value="ready" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">{{
          editingId ? '保存' : '创建'
        }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { successionApi } from '@/api/client'

const loading = ref(false)
const summaryLoading = ref(false)
const planList = ref([])
const summary = ref({})

const readinessList = computed(() => {
  const dist = summary.value.readiness_distribution || {}
  return [
    { label: '就绪', count: dist.ready_now || 0, type: 'success' },
    { label: '1-2年', count: dist.ready_1_2 || 0, type: 'warning' },
    { label: '2年以上', count: dist.ready_2_plus || 0, type: 'info' },
  ]
})

async function loadSummary() {
  summaryLoading.value = true
  try {
    const res = await successionApi.summary()
    summary.value = res || {}
  } catch (err) {
    ElMessage.error(err.message || '加载概览失败')
  } finally {
    summaryLoading.value = false
  }
}

async function loadPlans() {
  loading.value = true
  try {
    const res = await successionApi.list({})
    planList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载继任计划失败')
  } finally {
    loading.value = false
  }
}

// ============ 创建/更新 ============
const showDialog = ref(false)
const submitting = ref(false)
const editingId = ref('')
const form = ref({
  position_title: '',
  candidate_id: '',
  readiness: '1-2-years',
  development_gaps: '',
  risk_notes: '',
  status: 'identified',
})

function openCreateDialog() {
  editingId.value = ''
  form.value = {
    position_title: '',
    candidate_id: '',
    readiness: '1-2-years',
    development_gaps: '',
    risk_notes: '',
    status: 'identified',
  }
  showDialog.value = true
}

function openEditDialog(row) {
  editingId.value = row.plan_id || row.id
  form.value = {
    position_title: row.position_title || '',
    candidate_id: row.candidate_id || '',
    readiness: row.readiness || '1-2-years',
    development_gaps: Array.isArray(row.development_gaps)
      ? row.development_gaps.map((g) => g.description || g.area || JSON.stringify(g)).join('\n')
      : row.development_gaps || '',
    risk_notes: row.risk_notes || '',
    status: row.status || 'identified',
  }
  showDialog.value = true
}

async function submitForm() {
  if (!form.value.position_title.trim() || !form.value.candidate_id.trim()) {
    ElMessage.warning('请填写岗位名称和候选人')
    return
  }
  submitting.value = true
  try {
    const gaps = form.value.development_gaps
      ? form.value.development_gaps
          .split('\n')
          .filter((l) => l.trim())
          .map((l) => ({ area: l.trim() }))
      : []

    if (editingId.value) {
      const payload = {
        readiness: form.value.readiness,
        development_gaps: gaps,
        risk_notes: form.value.risk_notes || null,
        status: form.value.status,
      }
      await successionApi.update(editingId.value, payload)
      ElMessage.success('继任计划已更新')
    } else {
      const payload = {
        position_title: form.value.position_title.trim(),
        candidate_id: form.value.candidate_id.trim(),
        readiness: form.value.readiness,
        development_gaps: gaps,
        risk_notes: form.value.risk_notes || null,
      }
      await successionApi.create(payload)
      ElMessage.success('继任计划已创建')
    }
    showDialog.value = false
    await loadPlans()
    await loadSummary()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// ============ 通用工具 ============
function readinessLabel(r) {
  return { 'ready-now': '就绪', '1-2-years': '1-2年', '3-plus-years': '2年以上' }[r] || r
}
function readinessTagType(r) {
  return { 'ready-now': 'success', '1-2-years': 'warning', '3-plus-years': 'info' }[r] || 'info'
}
function statusLabel(s) {
  return { identified: '识别中', developing: '培养中', ready: '已就绪' }[s] || s
}
function statusTagType(s) {
  return { identified: 'info', developing: 'warning', ready: 'success' }[s] || 'info'
}

onMounted(() => {
  loadSummary()
  loadPlans()
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
.readiness-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.readiness-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
