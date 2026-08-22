<template>
  <div class="goal-management">
    <!-- ============ 统计卡片 ============ -->
    <el-row :gutter="20" class="mb-16">
      <el-col :span="8">
        <el-card>
          <el-statistic
            :title="$t('v.talent.GoalManagement.0')"
            :value="stats.total"
            value-style="color: var(--el-color-primary)"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <el-statistic
            :title="$t('v.talent.GoalManagement.1')"
            :value="stats.inProgress"
            value-style="color: var(--el-color-warning)"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <el-statistic
            :title="$t('v.talent.GoalManagement.2')"
            :value="stats.completed"
            value-style="color: var(--el-color-success)"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 目标列表 ============ -->
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{ $t('v.talent.GoalManagement.3') }</span>
          <el-button type="primary" size="small" @click="openCreateDialog"
            >{ $t('v.talent.GoalManagement.4') }</el-button
          >
        </div>
      </template>

      <el-form :inline="true" class="filter-form">
        <el-form-item label="周期">
          <el-input
            v-model="filter.period"
            placeholder="例如 2026-Q2"
            style="width: 180px"
            clearable
            @keyup.enter="loadGoals"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filter.type" placeholder="全部" clearable style="width: 140px">
            <el-option label="公司级" value="company" />
            <el-option label="团队级" value="team" />
            <el-option label="个人级" value="individual" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已暂停" value="paused" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadGoals">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="goalList" style="width: 100%" empty-text="暂无目标">
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTagType(row.goal_type)">{{
              typeLabel(row.goal_type)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="period" label="周期" width="120" />
        <el-table-column prop="owner_id" label="归属人" width="120" />
        <el-table-column label="进度" width="180">
          <template #default="{ row }">
            <el-progress :percentage="Number(row.progress || 0)" :status="progressStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{
              statusLabel(row.status)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openEditDialog(row)"
              >编辑进度</el-button
            >
            <el-button size="small" link type="danger" @click="deleteGoal(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ============ 创建目标对话框 ============ -->
    <el-dialog v-model="showCreateDialog" title="创建目标" width="560px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" placeholder="请输入目标标题" maxlength="256" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="目标描述"
          />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="createForm.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="公司级" value="company" />
            <el-option label="团队级" value="team" />
            <el-option label="个人级" value="individual" />
          </el-select>
        </el-form-item>
        <el-form-item label="周期" required>
          <el-input v-model="createForm.period" placeholder="例如 2026-Q2" />
        </el-form-item>
        <el-form-item label="归属人">
          <el-input v-model="createForm.owner_id" placeholder="归属人员工ID，例如 E1001" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createGoal">创建</el-button>
      </template>
    </el-dialog>

    <!-- ============ 编辑进度对话框 ============ -->
    <el-dialog v-model="showEditDialog" title="编辑目标进度" width="480px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="标题">
          <span class="muted">{{ editForm.title }}</span>
        </el-form-item>
        <el-form-item label="进度" required>
          <el-slider v-model="editForm.progress" :min="0" :max="100" show-input />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已暂停" value="paused" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="updateGoal">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { talentApi } from '@/api/client'

const loading = ref(false)
const goalList = ref([])
const filter = ref({ period: '', type: '', status: '' })

const stats = computed(() => {
  const list = goalList.value
  return {
    total: list.length,
    inProgress: list.filter((g) => g.status === 'in_progress').length,
    completed: list.filter((g) => g.status === 'completed').length,
  }
})

async function loadGoals() {
  loading.value = true
  try {
    const params = {}
    if (filter.value.period) params.period = filter.value.period
    if (filter.value.type) params.type = filter.value.type
    if (filter.value.status) params.status = filter.value.status
    const res = await talentApi.listGoals(params)
    goalList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载目标列表失败')
  } finally {
    loading.value = false
  }
}

// ============ 创建目标 ============
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({ title: '', description: '', type: '', period: '', owner_id: '' })

function openCreateDialog() {
  createForm.value = { title: '', description: '', type: '', period: '', owner_id: '' }
  showCreateDialog.value = true
}

async function createGoal() {
  if (!createForm.value.title.trim() || !createForm.value.type || !createForm.value.period.trim()) {
    ElMessage.warning('请填写标题、类型和周期')
    return
  }
  creating.value = true
  try {
    await talentApi.createGoal({
      title: createForm.value.title.trim(),
      description: createForm.value.description || null,
      goal_type: createForm.value.type,
      period: createForm.value.period.trim(),
      owner_id: createForm.value.owner_id.trim() || 'M001',
      key_results: [],
    })
    ElMessage.success('目标已创建')
    showCreateDialog.value = false
    await loadGoals()
  } catch (err) {
    ElMessage.error(err.message || '创建目标失败')
  } finally {
    creating.value = false
  }
}

// ============ 编辑进度 ============
const showEditDialog = ref(false)
const editing = ref(false)
const editForm = ref({ goal_id: '', title: '', progress: 0, status: 'in_progress' })

function openEditDialog(row) {
  editForm.value = {
    goal_id: row.goal_id || row.id,
    title: row.title,
    progress: Number(row.progress || 0),
    status: row.status || 'in_progress',
  }
  showEditDialog.value = true
}

async function updateGoal() {
  editing.value = true
  try {
    await talentApi.updateGoal(editForm.value.goal_id, {
      progress: editForm.value.progress,
      status: editForm.value.status,
    })
    ElMessage.success('进度已更新')
    showEditDialog.value = false
    await loadGoals()
  } catch (err) {
    ElMessage.error(err.message || '更新进度失败')
  } finally {
    editing.value = false
  }
}

async function deleteGoal(row) {
  try {
    await ElMessageBox.confirm('确认删除该目标？此操作不可撤销。', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await talentApi.deleteGoal(row.goal_id || row.id)
    ElMessage.success('目标已删除')
    await loadGoals()
  } catch (err) {
    ElMessage.error(err.message || '删除目标失败')
  }
}

// ============ 通用工具 ============
function typeLabel(t) {
  return { company: '公司级', team: '团队级', individual: '个人级' }[t] || t
}
function typeTagType(t) {
  return { company: 'danger', team: 'warning', individual: 'info' }[t] || 'info'
}
function statusLabel(s) {
  return { in_progress: '进行中', completed: '已完成', paused: '已暂停' }[s] || s
}
function statusTagType(s) {
  return { in_progress: 'warning', completed: 'success', paused: 'info' }[s] || 'info'
}
function progressStatus(row) {
  if (row.status === 'completed') return 'success'
  if (Number(row.progress || 0) >= 100) return 'success'
  return undefined
}

onMounted(() => {
  loadGoals()
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
.filter-form {
  margin-bottom: 12px;
}
</style>
