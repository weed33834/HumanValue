<template>
  <div class="approval-detail">
    <el-page-header @back="goBack" :title="$t('v.manager.ApprovalDetail.0')" />

    <el-card v-if="evaluation" v-loading="loading" :aria-busy="loading" class="detail-card">
      <template #header>
        <div class="card-header">
          <span>评估详情 — {{ evaluation.employee_id }} / {{ evaluation.period }}</span>
          <el-tag :type="statusType">{{ evaluation.status }}</el-tag>
        </div>
      </template>

      <EvaluationDetailPanel :evaluation="evaluation" />

      <el-divider />

      <h3>备注</h3>
      <el-form label-position="top">
        <el-form-item label="备注">
          <el-input v-model="comment" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
        <el-form-item>
          <div class="approval-actions">
            <el-button :loading="submitting" @click="reEvaluate">重新评估</el-button>
            <template v-if="isPending">
              <el-button type="success" :loading="submitting" @click="approveEval">通过</el-button>
              <el-button type="danger" :loading="submitting" @click="rejectEval">驳回</el-button>
              <el-button type="warning" :loading="submitting" @click="requestHr"
                >申请 HR 复核</el-button
              >
            </template>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 无障碍：骨架屏加载态用 role=status 通告屏幕阅读器 -->
    <el-skeleton v-else-if="loading" :rows="6" animated role="status" aria-label="评估详情加载中" />

    <el-empty v-else description="未找到评估数据" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { evaluationApi } from '@/api/client'
import { statusTagType } from '@/utils/evaluationStatus'
import EvaluationDetailPanel from '@/components/EvaluationDetailPanel.vue'

const route = useRoute()
const router = useRouter()

const evaluationId = computed(() => route.params.id)
const loading = ref(false)
const submitting = ref(false)
const evaluation = ref(null)
const comment = ref('')

const statusType = computed(() => statusTagType(evaluation.value?.status))

// 待审批状态（ai_drafted / manager_review / hr_audit）才显示审批操作
const PENDING_STATUSES = ['ai_drafted', 'manager_review', 'hr_audit']
const isPending = computed(
  () => evaluation.value && PENDING_STATUSES.includes(evaluation.value.status),
)

async function loadEvaluation() {
  loading.value = true
  try {
    const data = await evaluationApi.get(evaluationId.value)
    evaluation.value = data
  } catch (err) {
    console.error('加载评估失败:', err)
    ElMessage.error('加载评估失败')
  } finally {
    loading.value = false
  }
}

async function reEvaluate() {
  if (!evaluation.value) return
  try {
    await ElMessageBox.confirm(
      '确认基于现有输入重新运行 AI 评估？将生成新的草稿结果。',
      '重新评估',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  submitting.value = true
  try {
    const res = await evaluationApi.reEvaluate(evaluationId.value, {
      feedback: comment.value ? [comment.value] : [],
    })
    ElMessage.success(`已重新评估，状态：${res.status}`)
    comment.value = ''
    await loadEvaluation()
  } catch (err) {
    ElMessage.error(err.message || '重新评估失败')
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.push('/boss')
}

async function approveEval() {
  await _submitApproval('approve', '确认通过该评估？通过后评估生效。')
}

async function rejectEval() {
  await _submitApproval('reject', '确认驳回该评估？驳回后评估不生效。')
}

async function requestHr() {
  await _submitApproval('requestHrReview', '确认申请 HR 复核？将把该评估送交 HR 审核。')
}

async function _submitApproval(action, confirmText) {
  if (!evaluation.value) return
  if (!comment.value.trim()) {
    ElMessage.warning('请填写审批备注')
    return
  }
  try {
    await ElMessageBox.confirm(confirmText, '审批操作', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  submitting.value = true
  try {
    const res = await evaluationApi[action](evaluationId.value, {
      current_status: evaluation.value.status,
      comment: comment.value,
    })
    ElMessage.success(`操作成功，状态：${res.status}`)
    comment.value = ''
    await loadEvaluation()
  } catch (err) {
    ElMessage.error(err.message || '审批操作失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadEvaluation)
</script>

<style scoped>
.approval-detail {
  padding: 10px;
}
.detail-card {
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.risk-alert {
  margin-bottom: 12px;
}
.approval-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
