<template>
  <div class="recognition">
    <!-- ============ 统计卡片 ============ -->
    <el-row :gutter="20" class="mb-16">
      <el-col :span="12">
        <el-card>
          <el-statistic
            :title="$t('v.talent.Recognition.0')"
            :value="stats.monthCount"
            value-style="color: var(--el-color-primary)"
          />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <el-statistic
            :title="$t('v.talent.Recognition.1')"
            :value="stats.totalPoints"
            value-style="color: var(--el-color-success)"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- ============ 左侧：动态流 ============ -->
      <el-col :span="16">
        <el-card v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>{ $t('v.talent.Recognition.2') }</span>
              <el-button type="primary" size="small" @click="openCreateDialog"
                >{ $t('v.talent.Recognition.3') }</el-button
              >
            </div>
          </template>
          <div v-if="!recognitionList.length && !loading" class="empty-tip">
            <el-empty description="暂无认可动态" />
          </div>
          <div
            v-for="item in recognitionList"
            :key="item.recognition_id || item.id"
            class="recognition-card"
          >
            <div class="recognition-header">
              <span class="sender">{{ item.sender_id }}</span>
              <el-icon class="arrow"><Right /></el-icon>
              <span class="receiver">{{ item.recipient_id }}</span>
              <el-tag
                size="small"
                :type="typeTagType(item.recognition_type)"
                style="margin-left: auto"
              >
                {{ typeLabel(item.recognition_type) }}
              </el-tag>
            </div>
            <p class="message">{{ item.message }}</p>
            <div class="recognition-footer">
              <div>
                <el-tag
                  v-for="tag in item.value_tags || []"
                  :key="tag"
                  size="small"
                  type="success"
                  effect="plain"
                  class="tag-gap"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <span class="muted"
                >{{ formatTime(item.created_at) }} · 积分 +{{ item.points || 0 }}</span
              >
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- ============ 右侧：排行榜 ============ -->
      <el-col :span="8">
        <el-card v-loading="boardLoading">
          <template #header><span>积分排行榜 (Top 5)</span></template>
          <div v-if="!leaderboard.length && !boardLoading">
            <el-empty description="暂无排行数据" :image-size="60" />
          </div>
          <div v-for="(emp, idx) in leaderboard" :key="emp.employee_id" class="rank-item">
            <div class="rank-no" :class="rankClass(idx)">{{ idx + 1 }}</div>
            <div class="rank-info">
              <div class="rank-name">{{ emp.employee_id }}</div>
              <div class="muted">{{ emp.recognition_count || 0 }} 次认可</div>
            </div>
            <el-statistic
              :value="emp.total_points || 0"
              suffix="分"
              value-style="font-size: 16px"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ============ 发送认可对话框 ============ -->
    <el-dialog v-model="showCreateDialog" title="发送认可" width="560px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="接收人" required>
          <el-input v-model="createForm.to_user_id" placeholder="例如 E1001" />
        </el-form-item>
        <el-form-item label="认可类型" required>
          <el-select
            v-model="createForm.recognition_type"
            placeholder="请选择类型"
            style="width: 100%"
          >
            <el-option label="感谢" value="thank_you" />
            <el-option label="表扬" value="praise" />
            <el-option label="里程碑" value="milestone" />
            <el-option label="团队协作" value="teamwork" />
          </el-select>
        </el-form-item>
        <el-form-item label="消息" required>
          <el-input
            v-model="createForm.message"
            type="textarea"
            :rows="3"
            placeholder="认可消息内容"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="价值观标签">
          <div class="tag-input-row">
            <el-input
              v-model="tagInput"
              placeholder="输入标签后回车，例如 客户至上"
              style="width: 220px"
              @keyup.enter="addTag"
            />
            <el-button type="primary" link @click="addTag">添加</el-button>
          </div>
          <div class="tag-row">
            <el-tag
              v-for="(tag, idx) in createForm.values_tags"
              :key="idx"
              closable
              size="small"
              class="tag-gap"
              @close="createForm.values_tags.splice(idx, 1)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="积分">
          <el-input-number v-model="createForm.points" :min="0" :max="1000" :step="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createRecognition">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Right } from '@element-plus/icons-vue'
import { engagementApi } from '@/api/client'

const loading = ref(false)
const boardLoading = ref(false)
const recognitionList = ref([])
const leaderboard = ref([])

const stats = computed(() => {
  const now = new Date()
  const list = recognitionList.value
  const monthList = list.filter((r) => {
    if (!r.created_at) return false
    const d = new Date(r.created_at)
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
  })
  return {
    monthCount: monthList.length,
    totalPoints: list.reduce((sum, r) => sum + (r.points || 0), 0),
  }
})

async function loadRecognitions() {
  loading.value = true
  try {
    const res = await engagementApi.listRecognitions({})
    recognitionList.value = res.items || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载认可动态失败')
  } finally {
    loading.value = false
  }
}

async function loadLeaderboard() {
  boardLoading.value = true
  try {
    const res = await engagementApi.recognitionLeaderboard({})
    leaderboard.value = (res.items || res || []).slice(0, 5)
  } catch (err) {
    ElMessage.error(err.message || '加载排行榜失败')
  } finally {
    boardLoading.value = false
  }
}

// ============ 发送认可 ============
const showCreateDialog = ref(false)
const creating = ref(false)
const tagInput = ref('')
const createForm = ref({
  to_user_id: '',
  recognition_type: '',
  message: '',
  values_tags: [],
  points: 10,
})

function openCreateDialog() {
  createForm.value = {
    to_user_id: '',
    recognition_type: '',
    message: '',
    values_tags: [],
    points: 10,
  }
  tagInput.value = ''
  showCreateDialog.value = true
}

function addTag() {
  const v = tagInput.value.trim()
  if (v && !createForm.value.values_tags.includes(v)) {
    createForm.value.values_tags.push(v)
  }
  tagInput.value = ''
}

async function createRecognition() {
  if (
    !createForm.value.to_user_id.trim() ||
    !createForm.value.recognition_type ||
    !createForm.value.message.trim()
  ) {
    ElMessage.warning('请填写接收人、类型和消息')
    return
  }
  creating.value = true
  try {
    await engagementApi.createRecognition({
      to_user_id: createForm.value.to_user_id.trim(),
      recognition_type: createForm.value.recognition_type,
      message: createForm.value.message.trim(),
      values_tags: createForm.value.values_tags || [],
      points: createForm.value.points,
    })
    ElMessage.success('认可已发送')
    showCreateDialog.value = false
    await loadRecognitions()
    await loadLeaderboard()
  } catch (err) {
    ElMessage.error(err.message || '发送认可失败')
  } finally {
    creating.value = false
  }
}

// ============ 通用工具 ============
function typeLabel(t) {
  return { thank_you: '感谢', praise: '表扬', milestone: '里程碑', teamwork: '团队协作' }[t] || t
}
function typeTagType(t) {
  return (
    { thank_you: 'success', praise: 'warning', milestone: 'danger', teamwork: 'info' }[t] || 'info'
  )
}
function rankClass(idx) {
  if (idx === 0) return 'rank-gold'
  if (idx === 1) return 'rank-silver'
  if (idx === 2) return 'rank-bronze'
  return ''
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
  loadRecognitions()
  loadLeaderboard()
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
.empty-tip {
  padding: 20px 0;
}
.recognition-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
}
.recognition-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.sender {
  font-weight: 600;
  color: var(--el-color-primary);
}
.receiver {
  font-weight: 600;
  color: var(--el-color-success);
}
.arrow {
  color: #909399;
}
.message {
  margin: 6px 0;
  color: #303133;
  line-height: 1.6;
}
.recognition-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tag-gap {
  margin-right: 6px;
}
.tag-row {
  margin-top: 8px;
}
.tag-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f2f5;
}
.rank-item:last-child {
  border-bottom: none;
}
.rank-no {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #c0c4cc;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}
.rank-gold {
  background: #f7ba2a;
}
.rank-silver {
  background: #b0b3b8;
}
.rank-bronze {
  background: #cd7f32;
}
.rank-info {
  flex: 1;
}
.rank-name {
  font-weight: 600;
}
</style>
