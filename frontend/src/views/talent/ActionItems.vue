<template>
  <div class="action-items">
    <!-- ============ 顶部统计卡片 ============ -->
    <el-row :gutter="20" class="mb-16">
      <el-col :span="4">
        <el-card>
          <el-statistic :title="$t('v.talent.ActionItems.0')" :value="summary.total || 0" />
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <el-statistic
            :title="$t('v.talent.ActionItems.1')"
            :value="summary.pending || 0"
            value-style="color: var(--el-color-info)"
          />
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <el-statistic
            :title="$t('v.talent.ActionItems.2')"
            :value="summary.in_progress || 0"
            value-style="color: var(--el-color-warning)"
          />
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <el-statistic
            :title="$t('v.talent.ActionItems.3')"
            :value="summary.completed || 0"
            value-style="color: var(--el-color-success)"
          />
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <el-statistic
            :title="$t('v.talent.ActionItems.4')"
            :value="summary.overdue || 0"
            value-style="color: var(--el-color-danger)"
          />
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card>
          <el-statistic
            :title="$t('v.talent.ActionItems.5')"
            :value="summary.completion_rate || 0"
            suffix="%"
            value-style="color: var(--el-color-primary)"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 行动项列表 ============ -->
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{ $t('v.talent.ActionItems.6') }</span>
          <el-button type="primary" size="small" @click="openCreateDialog"
            >{ $t('v.talent.ActionItems.7') }</el-button
          >
        </div>
      </template>

      <el-form :inline="true" class="filter-form">
        <el-form-item label="状态筛选">
          <el-select
            v-model="filter.status"
            placeholder="全部"
            clearable
            style="width: 160px"
            @change="loadItems"
          >
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadItems">刷新</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="actionList" style="width: 100%" empty-text="暂无行动项">
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="employee_id" label="关联员工" width="120" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column label="优先级" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="priorityTagType(row.priority)">{{
              priorityLabel(row.priority)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{
              statusLabel(row.status)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="140">
          <template #default="{ row }">
            <span :class="{ overdue: isOverdue(row) }">{{ formatDate(row.due_date) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== 'in_progress'"
              size="small"
              link
              type="warning"
              @click="changeStatus(row, 'in_progress')"
            >
              开始
            </el-button>
            <el-button
              v-if="row.status !== 'completed'"
              size="small"
              link
              type="success"
              @click="changeStatus(row, 'completed')"
            >
              完成
            </el-button>
            <el-button size="small" link type="danger" @click="deleteItem(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ============ 创建行动项对话框 ============ -->
    <el-dialog v-model="showCreateDialog" title="创建行动项" width="560px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" placeholder="请输入行动项标题" maxlength="256" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="行动项描述"
          />
        </el-form-item>
        <el-form-item label="员工ID" required>
          <el-input v-model="createForm.employee_id" placeholder="例如 E1001" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="createForm.category" placeholder="例如 培训、项目、绩效" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="createForm.priority" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="createForm.due_date"
            type="date"
            placeholder="选择截止日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createItem">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { talentApi } from '@/api/client'

const loading = ref(false)
const actionList = ref([])
const summary = ref({})
const filter = ref({ status: '' })

async function loadSummary() {
  try {
    const res = await talentApi.actionItemsSummary()
    summary.value = res || {}
  } catch (err) {
    ElMessage.error(err.message || '加载统计失败')
  }
}

async function loadItems() {
  loading.value = true
  try {
    const params = {}
    if (filter.value.status) params.status = filter.value.status
    const res = await talentApi.listActionItems(params)
    actionList.value = res.items || res || []
    await loadSummary()
  } catch (err) {
    ElMessage.error(err.message || '加载行动项列表失败')
  } finally {
    loading.value = false
  }
}

// ============ 创建行动项 ============
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({
  title: '',
  description: '',
  employee_id: '',
  category: '',
  priority: 'medium',
  due_date: '',
})

function openCreateDialog() {
  createForm.value = {
    title: '',
    description: '',
    employee_id: '',
    category: '',
    priority: 'medium',
    due_date: '',
  }
  showCreateDialog.value = true
}

async function createItem() {
  if (!createForm.value.title.trim() || !createForm.value.employee_id.trim()) {
    ElMessage.warning('请填写标题和员工ID')
    return
  }
  creating.value = true
  try {
    await talentApi.createActionItem({
      title: createForm.value.title.trim(),
      description: createForm.value.description || null,
      employee_id: createForm.value.employee_id.trim(),
      category: createForm.value.category || null,
      priority: createForm.value.priority,
      due_date: createForm.value.due_date || null,
    })
    ElMessage.success('行动项已创建')
    showCreateDialog.value = false
    await loadItems()
  } catch (err) {
    ElMessage.error(err.message || '创建行动项失败')
  } finally {
    creating.value = false
  }
}

// ============ 更新状态 ============
async function changeStatus(row, status) {
  try {
    await talentApi.updateActionItem(row.action_id || row.id, { status })
    ElMessage.success('状态已更新')
    await loadItems()
  } catch (err) {
    ElMessage.error(err.message || '更新状态失败')
  }
}

async function deleteItem(row) {
  try {
    await ElMessageBox.confirm('确认删除该行动项？', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await talentApi.deleteActionItem(row.action_id || row.id)
    ElMessage.success('行动项已删除')
    await loadItems()
  } catch (err) {
    ElMessage.error(err.message || '删除行动项失败')
  }
}

// ============ 通用工具 ============
function priorityLabel(p) {
  return { low: '低', medium: '中', high: '高' }[p] || p
}
function priorityTagType(p) {
  return { low: 'info', medium: 'warning', high: 'danger' }[p] || 'info'
}
function statusLabel(s) {
  return { pending: '待处理', in_progress: '进行中', completed: '已完成' }[s] || s
}
function statusTagType(s) {
  return { pending: 'info', in_progress: 'warning', completed: 'success' }[s] || 'info'
}
function isOverdue(row) {
  if (!row.due_date || row.status === 'completed') return false
  return new Date(row.due_date) < new Date(new Date().toDateString())
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
  loadItems()
})
</script>

<style scoped>
.mb-16 {
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-form {
  margin-bottom: 12px;
}
.overdue {
  color: #f56c6c;
  font-weight: 600;
}
</style>
