<template>
  <div class="one-on-ones">
    <!-- ============ 统计卡片 ============ -->
    <el-row :gutter="20" class="mb-16">
      <el-col :span="12">
        <el-card>
          <el-statistic
            :title="$t('v.talent.OneOnOnes.0')"
            :value="stats.monthCount"
            value-style="color: var(--el-color-primary)"
          />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <el-statistic
            :title="$t('v.talent.OneOnOnes.1')"
            :value="stats.completedCount"
            value-style="color: var(--el-color-success)"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 会议列表 ============ -->
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>1:1 会议管理</span>
          <el-button type="primary" size="small" @click="openCreateDialog">创建 1:1 会议</el-button>
        </div>
      </template>

      <el-table :data="meetingList" style="width: 100%" empty-text="暂无会议">
        <el-table-column prop="employee_id" label="员工" width="120" />
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">
            <span class="muted">{{ formatTime(row.scheduled_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时长" width="100">
          <template #default="{ row }">{{ row.duration_minutes || 0 }} 分钟</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{
              statusLabel(row.status)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="议程数" width="90">
          <template #default="{ row }">{{ (row.agenda_items || []).length }}</template>
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

    <!-- ============ 创建 1:1 对话框 ============ -->
    <el-dialog v-model="showCreateDialog" title="创建 1:1 会议" width="560px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="选择员工" required>
          <el-input v-model="createForm.employee_id" placeholder="例如 E1001" />
        </el-form-item>
        <el-form-item label="会议时间" required>
          <el-date-picker
            v-model="createForm.scheduled_at"
            type="datetime"
            placeholder="选择会议时间"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="时长(分钟)">
          <el-input-number v-model="createForm.duration_minutes" :min="15" :max="180" :step="15" />
        </el-form-item>
        <el-form-item label="议程项">
          <div v-for="(item, idx) in createForm.agenda_items" :key="idx" class="agenda-row">
            <el-input v-model="item.topic" placeholder="议程主题" style="width: 320px" />
            <el-button
              type="danger"
              link
              icon="Delete"
              @click="createForm.agenda_items.splice(idx, 1)"
            />
          </div>
          <el-button
            type="primary"
            link
            icon="Plus"
            @click="createForm.agenda_items.push({ topic: '' })"
            >添加议程</el-button
          >
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createMeeting">创建</el-button>
      </template>
    </el-dialog>

    <!-- ============ 会议详情对话框 ============ -->
    <el-dialog v-model="showDetailDialog" title="会议详情" width="640px">
      <template v-if="currentMeeting">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="员工">{{ currentMeeting.employee_id }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{
            formatTime(currentMeeting.scheduled_at)
          }}</el-descriptions-item>
          <el-descriptions-item label="时长"
            >{{ currentMeeting.duration_minutes || 0 }} 分钟</el-descriptions-item
          >
          <el-descriptions-item label="状态">
            <el-tag size="small" :type="statusTagType(currentMeeting.status)">{{
              statusLabel(currentMeeting.status)
            }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">议程列表</el-divider>
        <div
          v-if="currentMeeting.agenda_items && currentMeeting.agenda_items.length"
          class="agenda-list"
        >
          <div v-for="(item, idx) in currentMeeting.agenda_items" :key="idx" class="agenda-item">
            <el-checkbox v-model="item.completed" @change="markAgendaDone(idx)">{{
              item.topic
            }}</el-checkbox>
          </div>
        </div>
        <el-empty v-else description="暂无议程" :image-size="60" />

        <el-divider content-position="left">会议笔记</el-divider>
        <el-input v-model="detailForm.notes" type="textarea" :rows="4" placeholder="记录会议笔记" />

        <el-divider content-position="left">行动项提取</el-divider>
        <el-input
          v-model="detailForm.action_summary"
          type="textarea"
          :rows="3"
          placeholder="从会议中提取的行动项，每行一条"
        />
      </template>
      <template #footer>
        <el-button @click="showDetailDialog = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="saveDetail">保存笔记</el-button>
        <el-button
          type="success"
          :loading="completing"
          :disabled="currentMeeting?.status === 'completed'"
          @click="completeMeeting"
          >完成会议</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { talentApi } from '@/api/client'

const loading = ref(false)
const meetingList = ref([])

const stats = computed(() => {
  const now = new Date()
  const list = meetingList.value
  const monthList = list.filter((m) => {
    if (!m.scheduled_at) return false
    const d = new Date(m.scheduled_at)
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
  })
  return {
    monthCount: monthList.length,
    completedCount: list.filter((m) => m.status === 'completed').length,
  }
})

async function loadMeetings() {
  loading.value = true
  try {
    const res = await talentApi.listOneOnOnes({})
    meetingList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载会议列表失败')
  } finally {
    loading.value = false
  }
}

// ============ 创建会议 ============
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({
  employee_id: '',
  scheduled_at: '',
  duration_minutes: 30,
  agenda_items: [{ topic: '' }],
})

function openCreateDialog() {
  createForm.value = {
    employee_id: '',
    scheduled_at: '',
    duration_minutes: 30,
    agenda_items: [{ topic: '' }],
  }
  showCreateDialog.value = true
}

async function createMeeting() {
  if (!createForm.value.employee_id.trim() || !createForm.value.scheduled_at) {
    ElMessage.warning('请填写员工和会议时间')
    return
  }
  creating.value = true
  try {
    await talentApi.createOneOnOne({
      employee_id: createForm.value.employee_id.trim(),
      scheduled_at: createForm.value.scheduled_at,
      duration_minutes: createForm.value.duration_minutes,
      agenda_items: createForm.value.agenda_items
        .filter((a) => a.topic.trim())
        .map((a) => ({ topic: a.topic.trim() })),
    })
    ElMessage.success('会议已创建')
    showCreateDialog.value = false
    await loadMeetings()
  } catch (err) {
    ElMessage.error(err.message || '创建会议失败')
  } finally {
    creating.value = false
  }
}

// ============ 会议详情 ============
const showDetailDialog = ref(false)
const currentMeeting = ref(null)
const updating = ref(false)
const completing = ref(false)
const detailForm = ref({ notes: '', action_summary: '' })

function openDetailDialog(row) {
  currentMeeting.value = row
  detailForm.value = {
    notes: row.notes || '',
    action_summary: row.action_summary || '',
  }
  showDetailDialog.value = true
}

function markAgendaDone(_idx) {
  // 标记仅本地变更，保存时一并提交
}

async function saveDetail() {
  updating.value = true
  try {
    await talentApi.updateOneOnOne(currentMeeting.value.meeting_id || currentMeeting.value.id, {
      notes: detailForm.value.notes,
      action_summary: detailForm.value.action_summary,
      agenda_items: currentMeeting.value.agenda_items,
    })
    ElMessage.success('笔记已保存')
    await loadMeetings()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    updating.value = false
  }
}

async function completeMeeting() {
  completing.value = true
  try {
    await talentApi.updateOneOnOne(currentMeeting.value.meeting_id || currentMeeting.value.id, {
      status: 'completed',
      notes: detailForm.value.notes,
      action_summary: detailForm.value.action_summary,
    })
    ElMessage.success('会议已完成')
    showDetailDialog.value = false
    await loadMeetings()
  } catch (err) {
    ElMessage.error(err.message || '完成会议失败')
  } finally {
    completing.value = false
  }
}

// ============ 通用工具 ============
function statusLabel(s) {
  return (
    { scheduled: '已排期', in_progress: '进行中', completed: '已完成', cancelled: '已取消' }[s] || s
  )
}
function statusTagType(s) {
  return (
    { scheduled: 'info', in_progress: 'warning', completed: 'success', cancelled: 'danger' }[s] ||
    'info'
  )
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
  loadMeetings()
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
.agenda-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.agenda-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.agenda-item {
  padding: 4px 0;
}
</style>
