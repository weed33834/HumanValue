<template>
  <div class="internal-mobility">
    <el-row :gutter="20">
      <!-- ============ 左侧：岗位列表 ============ -->
      <el-col :span="16">
        <el-card v-loading="jobLoading">
          <template #header>
            <div class="card-header">
              <span>{ $t('v.talent.InternalMobility.0') }</span>
              <el-button type="primary" size="small" @click="openCreateJobDialog"
                >{ $t('v.talent.InternalMobility.1') }</el-button
              >
            </div>
          </template>
          <div v-if="!jobList.length && !jobLoading" class="empty-tip">
            <el-empty description="暂无内部岗位" />
          </div>
          <el-row :gutter="16">
            <el-col v-for="job in jobList" :key="job.job_id || job.id" :span="12" class="mb-16">
              <el-card shadow="hover">
                <template #header>
                  <div class="card-header">
                    <span class="job-title">{{ job.title }}</span>
                    <el-tag size="small" :type="jobTypeTag(job.job_type)">{{
                      jobTypeLabel(job.job_type)
                    }}</el-tag>
                  </div>
                </template>
                <el-descriptions :column="1" size="small">
                  <el-descriptions-item label="部门">{{
                    job.department || '-'
                  }}</el-descriptions-item>
                  <el-descriptions-item label="描述">{{
                    job.description || '-'
                  }}</el-descriptions-item>
                </el-descriptions>
                <div class="skill-tags">
                  <el-tag
                    v-for="skill in job.required_skills || []"
                    :key="skill"
                    size="small"
                    effect="plain"
                    class="tag-gap"
                  >
                    {{ skill }}
                  </el-tag>
                </div>
                <div class="job-actions">
                  <el-button type="primary" size="small" @click="openApplyDialog(job)"
                    >申请岗位</el-button
                  >
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- ============ 右侧：我的申请列表 ============ -->
      <el-col :span="8">
        <el-card v-loading="appLoading">
          <template #header><span>我的申请</span></template>
          <div v-if="!appList.length && !appLoading">
            <el-empty description="暂无申请记录" :image-size="60" />
          </div>
          <div v-for="app in appList" :key="app.application_id || app.id" class="app-item">
            <div class="app-header">
              <span class="app-title">{{ app.job_title || app.job_id }}</span>
              <el-tag size="small" :type="appStatusTag(app.status)">{{
                appStatusLabel(app.status)
              }}</el-tag>
            </div>
            <div class="match-row">
              <span class="muted">匹配度</span>
              <el-progress
                :percentage="Number(app.match_score || 0)"
                :status="matchStatus(app.match_score)"
              />
            </div>
            <p class="muted">申请时间：{{ formatTime(app.applied_at) }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 发布岗位对话框 ============ -->
    <el-dialog v-model="showJobDialog" title="发布岗位" width="560px">
      <el-form :model="jobForm" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="jobForm.title" placeholder="例如 高级后端工程师" maxlength="256" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="jobForm.department" placeholder="例如 研发部" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="jobForm.job_type" style="width: 100%">
            <el-option label="晋升" value="promotion" />
            <el-option label="平调" value="lateral" />
            <el-option label="项目借调" value="project" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="jobForm.description"
            type="textarea"
            :rows="3"
            placeholder="岗位描述"
          />
        </el-form-item>
        <el-form-item label="所需技能">
          <div class="tag-input-row">
            <el-input
              v-model="skillInput"
              placeholder="输入技能后回车，例如 Python"
              style="width: 220px"
              @keyup.enter="addSkill"
            />
            <el-button type="primary" link @click="addSkill">添加</el-button>
          </div>
          <div class="tag-row">
            <el-tag
              v-for="(s, idx) in jobForm.required_skills"
              :key="idx"
              closable
              size="small"
              class="tag-gap"
              @close="jobForm.required_skills.splice(idx, 1)"
            >
              {{ s }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showJobDialog = false">取消</el-button>
        <el-button type="primary" :loading="jobCreating" @click="createJob">发布</el-button>
      </template>
    </el-dialog>

    <!-- ============ 申请岗位对话框 ============ -->
    <el-dialog v-model="showApplyDialog" title="申请岗位" width="480px">
      <el-form :model="applyForm" label-width="100px">
        <el-form-item label="岗位">
          <span class="strong">{{ applyForm.job_title }}</span>
        </el-form-item>
        <el-form-item label="申请人ID" required>
          <el-input v-model="applyForm.employee_id" placeholder="例如 E1001" />
        </el-form-item>
        <el-form-item label="申请理由">
          <el-input
            v-model="applyForm.statement"
            type="textarea"
            :rows="3"
            placeholder="为什么适合这个岗位"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApplyDialog = false">取消</el-button>
        <el-button type="primary" :loading="applying" @click="submitApply">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { growthApi } from '@/api/client'

const jobLoading = ref(false)
const appLoading = ref(false)
const jobList = ref([])
const appList = ref([])

async function loadJobs() {
  jobLoading.value = true
  try {
    const res = await growthApi.listJobPostings({})
    jobList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载岗位列表失败')
  } finally {
    jobLoading.value = false
  }
}

async function loadApplications() {
  appLoading.value = true
  try {
    const res = await growthApi.listApplications({})
    appList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载申请列表失败')
  } finally {
    appLoading.value = false
  }
}

// ============ 发布岗位 ============
const showJobDialog = ref(false)
const jobCreating = ref(false)
const skillInput = ref('')
const jobForm = ref({
  title: '',
  department: '',
  job_type: 'lateral',
  description: '',
  required_skills: [],
})

function openCreateJobDialog() {
  jobForm.value = {
    title: '',
    department: '',
    job_type: 'lateral',
    description: '',
    required_skills: [],
  }
  skillInput.value = ''
  showJobDialog.value = true
}

function addSkill() {
  const v = skillInput.value.trim()
  if (v && !jobForm.value.required_skills.includes(v)) {
    jobForm.value.required_skills.push(v)
  }
  skillInput.value = ''
}

async function createJob() {
  if (!jobForm.value.title.trim()) {
    ElMessage.warning('请填写岗位标题')
    return
  }
  jobCreating.value = true
  try {
    await growthApi.createJobPosting({
      title: jobForm.value.title.trim(),
      department: jobForm.value.department || null,
      job_type: jobForm.value.job_type,
      description: jobForm.value.description || null,
      required_skills: jobForm.value.required_skills.length ? jobForm.value.required_skills : null,
    })
    ElMessage.success('岗位已发布')
    showJobDialog.value = false
    await loadJobs()
  } catch (err) {
    ElMessage.error(err.message || '发布岗位失败')
  } finally {
    jobCreating.value = false
  }
}

// ============ 申请岗位 ============
const showApplyDialog = ref(false)
const applying = ref(false)
const applyForm = ref({ job_id: '', job_title: '', employee_id: '', statement: '' })

function openApplyDialog(job) {
  applyForm.value = {
    job_id: job.job_id || job.id,
    job_title: job.title,
    employee_id: '',
    statement: '',
  }
  showApplyDialog.value = true
}

async function submitApply() {
  if (!applyForm.value.employee_id.trim()) {
    ElMessage.warning('请填写申请人ID')
    return
  }
  applying.value = true
  try {
    await growthApi.applyInternal({
      job_id: applyForm.value.job_id,
      employee_id: applyForm.value.employee_id.trim(),
      statement: applyForm.value.statement || null,
    })
    ElMessage.success('申请已提交')
    showApplyDialog.value = false
    await loadApplications()
  } catch (err) {
    ElMessage.error(err.message || '申请失败')
  } finally {
    applying.value = false
  }
}

// ============ 通用工具 ============
function jobTypeLabel(t) {
  return { promotion: '晋升', lateral: '平调', project: '项目借调' }[t] || t
}
function jobTypeTag(t) {
  return { promotion: 'danger', lateral: 'info', project: 'warning' }[t] || 'info'
}
function appStatusLabel(s) {
  return { pending: '待审核', reviewing: '审核中', offered: '已录用', rejected: '已拒绝' }[s] || s
}
function appStatusTag(s) {
  return (
    { pending: 'info', reviewing: 'warning', offered: 'success', rejected: 'danger' }[s] || 'info'
  )
}
function matchStatus(score) {
  if (score >= 80) return 'success'
  if (score >= 50) return undefined
  return 'exception'
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
  loadJobs()
  loadApplications()
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
.strong {
  font-weight: 600;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.empty-tip {
  padding: 20px 0;
}
.job-title {
  font-size: 15px;
  font-weight: 600;
}
.skill-tags {
  margin-top: 10px;
}
.tag-gap {
  margin-right: 6px;
  margin-bottom: 4px;
}
.tag-row {
  margin-top: 8px;
}
.tag-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.job-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.app-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.app-title {
  font-weight: 600;
}
.match-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
</style>
