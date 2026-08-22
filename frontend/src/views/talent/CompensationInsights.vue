<template>
  <div class="compensation-insights">
    <!-- ============ 顶部统计卡片 ============ -->
    <el-row :gutter="20" class="mb-16">
      <el-col :span="5">
        <el-card v-loading="insightsLoading">
          <el-statistic
            :title="$t('v.talent.CompensationInsights.0')"
            :value="insights.avg_total_comp || 0"
            :precision="2"
            prefix="¥"
            value-style="color: var(--el-color-primary)"
          />
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card v-loading="insightsLoading">
          <el-statistic
            :title="$t('v.talent.CompensationInsights.1')"
            :value="insights.below_market_count || 0"
            value-style="color: var(--el-color-danger)"
          />
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card v-loading="insightsLoading">
          <el-statistic
            :title="$t('v.talent.CompensationInsights.2')"
            :value="insights.at_market_count || 0"
            value-style="color: var(--el-color-success)"
          />
        </el-card>
      </el-col>
      <el-col :span="5">
        <el-card v-loading="insightsLoading">
          <el-statistic
            :title="$t('v.talent.CompensationInsights.3')"
            :value="insights.above_market_count || 0"
            value-style="color: var(--el-color-warning)"
          />
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card v-loading="insightsLoading">
          <el-statistic
            :title="$t('v.talent.CompensationInsights.4')"
            :value="insights.avg_ratio || 0"
            :precision="2"
            suffix="x"
            value-style="color: var(--el-color-primary)"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 薪酬记录列表 ============ -->
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{ $t('v.talent.CompensationInsights.6') }</span>
          <el-button type="primary" size="small" @click="openCreateDialog"
            >{ $t('v.talent.CompensationInsights.5') }</el-button
          >
        </div>
      </template>
      <el-table :data="compList" style="width: 100%" empty-text="暂无薪酬记录">
        <el-table-column prop="employee_id" label="员工" width="120" />
        <el-table-column label="基本薪资" width="130">
          <template #default="{ row }">¥{{ formatMoney(row.base_salary) }}</template>
        </el-table-column>
        <el-table-column label="奖金" width="120">
          <template #default="{ row }">¥{{ formatMoney(row.bonus) }}</template>
        </el-table-column>
        <el-table-column label="总薪酬" width="140">
          <template #default="{ row }"
            ><span class="strong">¥{{ formatMoney(row.total_compensation) }}</span></template
          >
        </el-table-column>
        <el-table-column label="市场基准" width="130">
          <template #default="{ row }">¥{{ formatMoney(row.market_benchmark) }}</template>
        </el-table-column>
        <el-table-column label="比率" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="ratioTagType(row.compensation_ratio)"
              >{{ Number(row.compensation_ratio || 0).toFixed(2) }}x</el-tag
            >
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

    <!-- ============ 创建/更新薪酬对话框 ============ -->
    <el-dialog v-model="showDialog" :title="editingId ? '更新薪酬' : '创建薪酬'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="员工" required>
          <el-input v-model="form.employee_id" placeholder="例如 E1001" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="基本薪资" required>
          <el-input-number v-model="form.base_salary" :min="0" :step="1000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="奖金">
          <el-input-number v-model="form.bonus" :min="0" :step="1000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="市场基准">
          <el-input-number
            v-model="form.market_benchmark"
            :min="0"
            :step="1000"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="生效日期">
          <el-date-picker
            v-model="form.effective_date"
            type="date"
            placeholder="选择生效日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="薪酬调整备注" />
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { growthApi } from '@/api/client'

const loading = ref(false)
const insightsLoading = ref(false)
const compList = ref([])
const insights = ref({})

async function loadInsights() {
  insightsLoading.value = true
  try {
    const res = await growthApi.compensationInsights({})
    insights.value = res || {}
  } catch (err) {
    ElMessage.error(err.message || '加载薪酬洞察失败')
  } finally {
    insightsLoading.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await growthApi.listCompensation({})
    compList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载薪酬记录失败')
  } finally {
    loading.value = false
  }
}

// ============ 创建/更新 ============
const showDialog = ref(false)
const submitting = ref(false)
const editingId = ref('')
const form = ref({
  employee_id: '',
  base_salary: 0,
  bonus: 0,
  market_benchmark: 0,
  effective_date: '',
  notes: '',
})

function openCreateDialog() {
  editingId.value = ''
  form.value = {
    employee_id: '',
    base_salary: 0,
    bonus: 0,
    market_benchmark: 0,
    effective_date: '',
    notes: '',
  }
  showDialog.value = true
}

function openEditDialog(row) {
  editingId.value = row.compensation_id || row.id
  form.value = {
    employee_id: row.employee_id || '',
    base_salary: Number(row.base_salary || 0),
    bonus: Number(row.bonus || 0),
    market_benchmark: Number(row.market_benchmark || 0),
    effective_date: row.effective_date || '',
    notes: row.notes || '',
  }
  showDialog.value = true
}

async function submitForm() {
  if (!form.value.employee_id.trim()) {
    ElMessage.warning('请填写员工')
    return
  }
  submitting.value = true
  try {
    // 从生效日期或当前日期推导 period
    let period = ''
    if (form.value.effective_date) {
      const d = new Date(form.value.effective_date)
      period = `${d.getFullYear()}-Q${Math.ceil((d.getMonth() + 1) / 3)}`
    } else {
      const now = new Date()
      period = `${now.getFullYear()}-Q${Math.ceil((now.getMonth() + 1) / 3)}`
    }
    const payload = {
      employee_id: form.value.employee_id.trim(),
      base_salary: form.value.base_salary,
      bonus: form.value.bonus,
      market_benchmark: form.value.market_benchmark,
      last_review_date: form.value.effective_date
        ? new Date(form.value.effective_date).toISOString()
        : null,
      adjustment_reason: form.value.notes || null,
      period: period,
    }
    await growthApi.createCompensation(payload)
    ElMessage.success(editingId.value ? '薪酬已更新' : '薪酬已创建')
    showDialog.value = false
    await loadList()
    await loadInsights()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// ============ 通用工具 ============
function ratioTagType(ratio) {
  const r = Number(ratio || 0)
  if (r < 0.9) return 'danger'
  if (r > 1.1) return 'warning'
  return 'success'
}
function formatMoney(v) {
  const n = Number(v || 0)
  return n.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

onMounted(() => {
  loadInsights()
  loadList()
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
.strong {
  font-weight: 600;
  color: var(--el-color-primary);
}
</style>
