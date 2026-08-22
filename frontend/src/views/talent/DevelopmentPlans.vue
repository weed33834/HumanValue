<template>
  <div class="development-plans">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{ $t('v.talent.DevelopmentPlans.0') }</span>
          <el-button type="primary" size="small" @click="openCreateDialog"
            >{ $t('v.talent.DevelopmentPlans.1') }</el-button
          >
        </div>
      </template>

      <div v-if="!planList.length && !loading" class="empty-tip">
        <el-empty description="暂无发展计划" />
      </div>

      <el-row :gutter="20">
        <el-col v-for="plan in planList" :key="plan.plan_id || plan.id" :span="12" class="mb-16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span class="plan-title">{{ plan.title }}</span>
                <el-tag size="small" :type="statusTagType(plan.status)">{{
                  statusLabel(plan.status)
                }}</el-tag>
              </div>
            </template>

            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="员工">{{ plan.employee_id }}</el-descriptions-item>
              <el-descriptions-item label="时间范围"
                >{{ formatDate(plan.start_date) }} ~
                {{ formatDate(plan.end_date) }}</el-descriptions-item
              >
              <el-descriptions-item label="发展目标" :span="2">{{
                plan.development_goal || '-'
              }}</el-descriptions-item>
              <el-descriptions-item label="关联评估" :span="2">
                <span v-if="plan.evaluation_id">{{ plan.evaluation_id }}</span>
                <span v-else class="muted">未关联</span>
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="plan.focus_areas && plan.focus_areas.length" class="tag-row">
              <span class="muted">关注领域：</span>
              <el-tag v-for="area in plan.focus_areas" :key="area" size="small" class="tag-gap">{{
                area
              }}</el-tag>
            </div>

            <div class="progress-row">
              <span class="muted">总体进度</span>
              <el-progress
                :percentage="Number(plan.progress || 0)"
                :status="plan.status === 'completed' ? 'success' : undefined"
              />
            </div>

            <el-divider content-position="left">里程碑</el-divider>
            <el-timeline v-if="plan.milestones && plan.milestones.length">
              <el-timeline-item
                v-for="(ms, idx) in plan.milestones"
                :key="idx"
                :type="milestoneType(ms.status)"
                :timestamp="formatDate(ms.target_date)"
                placement="top"
              >
                <div class="milestone-item">
                  <span>{{ ms.title }}</span>
                  <el-tag size="small" :type="milestoneTagType(ms.status)" style="margin-left: 8px">
                    {{ milestoneLabel(ms.status) }}
                  </el-tag>
                  <el-button
                    v-if="ms.status !== 'completed'"
                    size="small"
                    link
                    type="success"
                    style="margin-left: 8px"
                    @click="toggleMilestone(plan, idx)"
                  >
                    标记完成
                  </el-button>
                  <el-button
                    v-else
                    size="small"
                    link
                    type="warning"
                    style="margin-left: 8px"
                    @click="toggleMilestone(plan, idx)"
                  >
                    重置
                  </el-button>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无里程碑" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- ============ 创建 IDP 对话框 ============ -->
    <el-dialog v-model="showCreateDialog" title="创建发展计划" width="640px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" placeholder="请输入计划标题" maxlength="256" />
        </el-form-item>
        <el-form-item label="员工" required>
          <el-input v-model="createForm.employee_id" placeholder="例如 E1001" />
        </el-form-item>
        <el-form-item label="发展目标" required>
          <el-input
            v-model="createForm.development_goal"
            type="textarea"
            :rows="2"
            placeholder="发展目标描述"
          />
        </el-form-item>
        <el-form-item label="关注领域">
          <div class="tag-input-row">
            <el-input
              v-model="tagInput"
              placeholder="输入关注领域后回车，例如 领导力"
              style="width: 220px"
              @keyup.enter="addTag"
            />
            <el-button type="primary" link @click="addTag">添加</el-button>
          </div>
          <div class="tag-row">
            <el-tag
              v-for="(tag, idx) in createForm.focus_areas"
              :key="idx"
              closable
              size="small"
              class="tag-gap"
              @close="removeTag(idx)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="时间范围">
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
        <el-form-item label="里程碑">
          <div v-for="(ms, idx) in createForm.milestones" :key="idx" class="milestone-input-row">
            <el-input v-model="ms.title" placeholder="里程碑标题" style="width: 240px" />
            <el-date-picker
              v-model="ms.target_date"
              type="date"
              placeholder="目标日期"
              value-format="YYYY-MM-DD"
              style="width: 160px; margin-left: 8px"
            />
            <el-button
              type="danger"
              link
              icon="Delete"
              style="margin-left: 8px"
              @click="createForm.milestones.splice(idx, 1)"
            />
          </div>
          <el-button type="primary" link icon="Plus" @click="addMilestone">添加里程碑</el-button>
        </el-form-item>
        <el-form-item label="关联评估ID">
          <el-input v-model="createForm.evaluation_id" placeholder="可选，例如 EVAL-XXXX" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createPlan">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { talentApi } from '@/api/client'

const loading = ref(false)
const planList = ref([])

async function loadPlans() {
  loading.value = true
  try {
    const res = await talentApi.listIDPs({})
    planList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载发展计划失败')
  } finally {
    loading.value = false
  }
}

// ============ 创建 IDP ============
const showCreateDialog = ref(false)
const creating = ref(false)
const tagInput = ref('')
const createForm = ref({
  title: '',
  employee_id: '',
  development_goal: '',
  focus_areas: [],
  dateRange: [],
  milestones: [],
  evaluation_id: '',
})

function openCreateDialog() {
  createForm.value = {
    title: '',
    employee_id: '',
    development_goal: '',
    focus_areas: [],
    dateRange: [],
    milestones: [],
    evaluation_id: '',
  }
  tagInput.value = ''
  showCreateDialog.value = true
}

function addTag() {
  const v = tagInput.value.trim()
  if (v && !createForm.value.focus_areas.includes(v)) {
    createForm.value.focus_areas.push(v)
  }
  tagInput.value = ''
}

function removeTag(idx) {
  createForm.value.focus_areas.splice(idx, 1)
}

function addMilestone() {
  createForm.value.milestones.push({ title: '', target_date: '' })
}

async function createPlan() {
  if (
    !createForm.value.title.trim() ||
    !createForm.value.employee_id.trim() ||
    !createForm.value.development_goal.trim()
  ) {
    ElMessage.warning('请填写标题、员工和发展目标')
    return
  }
  creating.value = true
  try {
    const [startDate, endDate] = createForm.value.dateRange || []
    await talentApi.createIDP({
      title: createForm.value.title.trim(),
      employee_id: createForm.value.employee_id.trim(),
      development_goal: createForm.value.development_goal.trim(),
      focus_areas: createForm.value.focus_areas.length ? createForm.value.focus_areas : [],
      timeline_start: startDate || null,
      timeline_end: endDate || null,
      milestones: createForm.value.milestones
        .filter((m) => m.title.trim())
        .map((m) => ({ title: m.title.trim(), target_date: m.target_date || null })),
      evaluation_id: createForm.value.evaluation_id || null,
    })
    ElMessage.success('发展计划已创建')
    showCreateDialog.value = false
    await loadPlans()
  } catch (err) {
    ElMessage.error(err.message || '创建发展计划失败')
  } finally {
    creating.value = false
  }
}

// ============ 编辑里程碑状态 ============
async function toggleMilestone(plan, idx) {
  const milestones = (plan.milestones || []).map((m, i) => ({
    ...m,
    status: i === idx ? (m.status === 'completed' ? 'pending' : 'completed') : m.status,
  }))
  try {
    await talentApi.updateIDP(plan.plan_id || plan.id, { milestones })
    ElMessage.success('里程碑状态已更新')
    await loadPlans()
  } catch (err) {
    ElMessage.error(err.message || '更新里程碑失败')
  }
}

// ============ 通用工具 ============
function statusLabel(s) {
  return { draft: '草稿', active: '进行中', completed: '已完成', paused: '已暂停' }[s] || s
}
function statusTagType(s) {
  return { draft: 'info', active: 'warning', completed: 'success', paused: 'info' }[s] || 'info'
}
function milestoneLabel(s) {
  return { pending: '待完成', in_progress: '进行中', completed: '已完成' }[s] || '待完成'
}
function milestoneTagType(s) {
  return { pending: 'info', in_progress: 'warning', completed: 'success' }[s] || 'info'
}
function milestoneType(s) {
  return { pending: 'info', in_progress: 'warning', completed: 'success' }[s] || 'info'
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
.plan-title {
  font-size: 15px;
  font-weight: 600;
}
.empty-tip {
  padding: 40px 0;
}
.tag-row {
  margin-top: 12px;
}
.tag-gap {
  margin-right: 6px;
  margin-bottom: 4px;
}
.tag-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.progress-row {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.milestone-item {
  display: flex;
  align-items: center;
}
.milestone-input-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
</style>
