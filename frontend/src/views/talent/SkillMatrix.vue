<template>
  <div class="skill-matrix">
    <!-- ============ 团队技能概览 ============ -->
    <el-card v-loading="matrixLoading" class="mb-16">
      <template #header>
        <div class="card-header">
          <span>{ $t('v.talent.SkillMatrix.1') }</span>
          <el-button type="primary" size="small" @click="openAssessDialog"
            >{ $t('v.talent.SkillMatrix.0') }</el-button
          >
        </div>
      </template>
      <el-table
        :data="skillMatrix"
        style="width: 100%"
        empty-text="暂无技能数据"
        @row-click="onRowClick"
      >
        <el-table-column prop="skill_name" label="技能名称" min-width="160" />
        <el-table-column prop="category" label="类别" width="120" />
        <el-table-column label="平均水平" width="160">
          <template #default="{ row }">
            <el-progress
              :percentage="Number(row.avg_level || 0) * 20"
              :format="() => row.avg_level + '/5'"
            />
          </template>
        </el-table-column>
        <el-table-column prop="employee_count" label="员工数" width="100" sortable />
        <el-table-column label="技能差距" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="gapTagType(row.gap)">{{ gapLabel(row.gap) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click.stop="viewSkillDetail(row)"
              >详情</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ============ 员工技能查询 ============ -->
    <el-card>
      <template #header><span>员工技能查询</span></template>
      <el-form :inline="true" class="filter-form">
        <el-form-item label="员工ID">
          <el-input
            v-model="employeeQuery"
            placeholder="例如 E1001"
            style="width: 220px"
            @keyup.enter="loadEmployeeSkills"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="empLoading" @click="loadEmployeeSkills"
            >查询</el-button
          >
        </el-form-item>
      </el-form>

      <div v-if="employeeSkills.length" class="radar-list">
        <el-row :gutter="20">
          <el-col v-for="skill in employeeSkills" :key="skill.skill_name" :span="8" class="mb-16">
            <el-card shadow="hover">
              <div class="emp-skill-header">
                <span class="skill-name">{{ skill.skill_name }}</span>
                <el-tag size="small" :type="levelTagType(skill.current_level)"
                  >{{ skill.current_level }}/5</el-tag
                >
              </div>
              <el-progress
                :percentage="Number(skill.current_level || 0) * 20"
                :color="levelColor(skill.current_level)"
              />
              <p class="muted" v-if="skill.last_assessed_at">
                最近评估：{{ formatDate(skill.last_assessed_at) }}
              </p>
            </el-card>
          </el-col>
        </el-row>
      </div>
      <el-empty v-else description="输入员工ID查询能力列表" :image-size="80" />
    </el-card>

    <!-- ============ 技能详情对话框 ============ -->
    <el-dialog v-model="showSkillDialog" title="技能详情" width="560px">
      <template v-if="currentSkill">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="技能名称">{{
            currentSkill.skill_name
          }}</el-descriptions-item>
          <el-descriptions-item label="类别">{{
            currentSkill.category || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="平均水平"
            >{{ currentSkill.avg_level }}/5</el-descriptions-item
          >
          <el-descriptions-item label="员工数">{{
            currentSkill.employee_count
          }}</el-descriptions-item>
          <el-descriptions-item label="技能差距">{{
            gapLabel(currentSkill.gap)
          }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="currentSkill.description" class="muted" style="margin-top: 12px">
          {{ currentSkill.description }}
        </div>
      </template>
    </el-dialog>

    <!-- ============ 添加技能评估对话框 ============ -->
    <el-dialog v-model="showAssessDialog" title="添加技能评估" width="480px">
      <el-form :model="assessForm" label-width="100px">
        <el-form-item label="员工ID" required>
          <el-input v-model="assessForm.employee_id" placeholder="例如 E1001" />
        </el-form-item>
        <el-form-item label="技能名称" required>
          <el-input v-model="assessForm.skill_name" placeholder="例如 Python 后端" />
        </el-form-item>
        <el-form-item label="能力等级" required>
          <el-rate v-model="assessForm.level" :max="10" show-score score-template="{value}/10" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="assessForm.notes" type="textarea" :rows="2" placeholder="评估备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssessDialog = false">取消</el-button>
        <el-button type="primary" :loading="assessing" @click="submitAssess">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { growthApi } from '@/api/client'

const matrixLoading = ref(false)
const empLoading = ref(false)
const skillMatrix = ref([])
const employeeQuery = ref('')
const employeeSkills = ref([])

async function loadMatrix() {
  matrixLoading.value = true
  try {
    const res = await growthApi.teamSkillMatrix()
    skillMatrix.value = res.items || res.skills || res || []
  } catch (err) {
    ElMessage.error(err.message || '加载技能矩阵失败')
  } finally {
    matrixLoading.value = false
  }
}

async function loadEmployeeSkills() {
  if (!employeeQuery.value.trim()) {
    ElMessage.warning('请输入员工ID')
    return
  }
  empLoading.value = true
  try {
    const res = await growthApi.getEmployeeSkills(employeeQuery.value.trim())
    employeeSkills.value = res.items || res.skills || res || []
    if (!employeeSkills.value.length) {
      ElMessage.info('未查询到该员工的技能数据')
    }
  } catch (err) {
    ElMessage.error(err.message || '查询员工技能失败')
  } finally {
    empLoading.value = false
  }
}

// ============ 技能详情 ============
const showSkillDialog = ref(false)
const currentSkill = ref(null)

function viewSkillDetail(row) {
  currentSkill.value = row
  showSkillDialog.value = true
}

function onRowClick(row) {
  viewSkillDetail(row)
}

// ============ 添加技能评估 ============
const showAssessDialog = ref(false)
const assessing = ref(false)
const assessForm = ref({ employee_id: '', skill_name: '', level: 5, notes: '' })

function openAssessDialog() {
  assessForm.value = { employee_id: '', skill_name: '', level: 5, notes: '' }
  showAssessDialog.value = true
}

async function submitAssess() {
  if (!assessForm.value.employee_id.trim() || !assessForm.value.skill_name.trim()) {
    ElMessage.warning('请填写员工ID和技能名称')
    return
  }
  assessing.value = true
  try {
    // 第一步：查找或创建技能定义
    const skillName = assessForm.value.skill_name.trim()
    let skillId = null
    try {
      const listRes = await growthApi.listSkills({ name: skillName })
      const skills = listRes.items || []
      const existing = skills.find((s) => s.name === skillName)
      if (existing) {
        skillId = existing.skill_id
      }
    } catch {
      // 查找失败，直接创建
    }
    if (!skillId) {
      const createRes = await growthApi.createSkill({ name: skillName, category: 'technical' })
      skillId = createRes.skill_id
    }

    // 第二步：将 1-10 等级映射到 1-5
    const currentLevel = Math.max(1, Math.min(5, Math.round(assessForm.value.level / 2 + 0.5)))

    // 第三步：关联员工技能
    await growthApi.setEmployeeSkill({
      employee_id: assessForm.value.employee_id.trim(),
      skill_id: skillId,
      current_level: currentLevel,
      target_level: Math.min(5, currentLevel + 1),
      notes: assessForm.value.notes || null,
    })
    ElMessage.success('技能评估已提交')
    showAssessDialog.value = false
    await loadMatrix()
  } catch (err) {
    ElMessage.error(err.message || '提交评估失败')
  } finally {
    assessing.value = false
  }
}

// ============ 通用工具 ============
function gapLabel(g) {
  return { none: '无差距', small: '轻微', medium: '中等', large: '较大' }[g] || g || '-'
}
function gapTagType(g) {
  return { none: 'success', small: 'info', medium: 'warning', large: 'danger' }[g] || 'info'
}
function levelTagType(level) {
  if (level >= 4) return 'success'
  if (level >= 3) return 'warning'
  return 'danger'
}
function levelColor(level) {
  if (level >= 4) return '#67c23a'
  if (level >= 3) return '#e6a23c'
  return '#f56c6c'
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
  loadMatrix()
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
.radar-list {
  margin-top: 12px;
}
.emp-skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.skill-name {
  font-weight: 600;
}
</style>
