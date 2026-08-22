<template>
  <div class="talent-value av-page">
    <PageHeader :title="$t('page.talentValue')" :subtitle="$t('page.talentValueSub')" />

    <!-- 体系类型说明 (淘汰制/培养制等, 由 TALENT_SYSTEM_TYPE 配置) -->
    <el-alert
      v-if="insights.label"
      type="info"
      :closable="false"
      show-icon
      class="av-mb-lg"
      :title="$t('pages.tv.systemCurrent', { label: insights.label, context: insights.context })"
    >
      <template #default>
        <div class="sys-note">
          <span
            ><b>{{ $t('pages.tv.coreQuestion') }}：</b>{{ insights.core_question }}</span
          >
          <span
            ><b>{{ $t('pages.tv.keyMetrics') }}：</b
            >{{ (insights.key_metrics || []).join(' · ') }}</span
          >
          <span
            ><b>{{ $t('pages.tv.theory') }}：</b>{{ insights.theory }}</span
          >
          <span class="sys-note__muted">{{ insights.distinct_note }}</span>
        </div>
      </template>
    </el-alert>

    <!-- 顶部 KPI 概览 -->
    <el-row :gutter="16" class="av-mb-lg av-stagger">
      <el-col :span="6"
        ><el-card class="kpi-card"
          ><el-statistic :title="$t('pages.tv.kpiTotal')" :value="overview.total" /></el-card
      ></el-col>
      <el-col :span="6"
        ><el-card class="kpi-card"
          ><el-statistic :title="$t('pages.tv.kpiStar')" :value="starWorkhorse" /></el-card
      ></el-col>
      <el-col :span="6"
        ><el-card class="kpi-card"
          ><el-statistic
            :title="$t('pages.tv.kpiPotential')"
            :value="overview.potential" /></el-card
      ></el-col>
      <el-col :span="6"
        ><el-card class="kpi-card"
          ><el-statistic :title="$t('pages.tv.kpiUnder')" :value="overview.under" /></el-card
      ></el-col>
    </el-row>

    <el-tabs v-model="tab">
      <el-tab-pane :label="$t('pages.tv.tabGrid')" name="grid">
        <el-card>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            class="av-mb-md"
            :title="$t('pages.tv.gridAlert')"
          />
          <!-- 3x3 网格 -->
          <div class="box-grid">
            <div
              v-for="cell in gridCells"
              :key="cell.key"
              class="box-cell"
              :class="['box-cell--' + cell.color]"
              :style="{ opacity: cell.count > 0 ? 1 : 0.35 }"
            >
              <div class="box-cell__title">{{ cell.label }}</div>
              <div class="box-cell__count">{{ cell.count }}</div>
              <div v-if="cell.employees.length" class="box-cell__names">
                {{ cell.employees.map((e) => e.name).join('、') }}
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="av-mt-lg">
          <template #header>{{ $t('pages.tv.strategyHeader') }}</template>
          <el-table :data="classification.employees" size="small" stripe>
            <el-table-column prop="name" :label="$t('pages.tv.colEmployee')" width="120" />
            <el-table-column prop="department" :label="$t('pages.tv.colDept')" width="120" />
            <el-table-column
              prop="performance"
              :label="$t('pages.tv.colPerf')"
              width="80"
              sortable
            />
            <el-table-column prop="potential" :label="$t('pages.tv.colPot')" width="80" sortable />
            <el-table-column :label="$t('pages.tv.colCat')" width="110">
              <template #default="{ row }">
                <el-tag :type="tagType(row.category)">{{ row.category_label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="risk_level" :label="$t('pages.tv.colRisk')" width="80">
              <template #default="{ row }"
                ><el-tag :type="riskType(row.risk_level)" size="small">{{
                  row.risk_level
                }}</el-tag></template
              >
            </el-table-column>
            <el-table-column prop="strategy" :label="$t('pages.tv.colStrategy')" min-width="260">
              <template #default="{ row }"
                ><span class="strategy-text">{{ row.strategy.join(' · ') }}</span></template
              >
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabCritical')" name="critical">
        <el-card>
          <el-alert
            type="warning"
            :closable="false"
            show-icon
            :title="critical.note || $t('pages.tv.criticalFallback')"
          />
          <el-table
            :data="critical.critical"
            size="small"
            stripe
            class="av-mt-lg"
            :empty-text="$t('pages.tv.criticalEmpty')"
          >
            <el-table-column prop="name" :label="$t('pages.tv.colEmployee')" />
            <el-table-column prop="department" :label="$t('pages.tv.colDept')" />
            <el-table-column prop="value" label="价值分" sortable />
            <el-table-column prop="risk_level" :label="$t('pages.tv.colRisk')">
              <template #default="{ row }"
                ><el-tag :type="riskType(row.risk_level)">{{ row.risk_level }}</el-tag></template
              >
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabPareto')" name="pareto">
        <el-card>
          <div class="pareto-wrap">
            <div class="pareto-gauge">
              <div class="pareto-ring" :style="ringStyle">{{ pareto.top_20_share_pct }}%</div>
              <div class="pareto-label">
                {{
                  $t('pages.tv.paretoShare', {
                    n: pareto.top_20_count,
                    pct: pareto.top_20_share_pct,
                  })
                }}
              </div>
            </div>
            <div class="pareto-info">
              <el-alert
                :type="pareto.top_20_share_pct >= 60 ? 'warning' : 'success'"
                :closable="false"
                show-icon
                :title="pareto.warning"
              />
              <div class="av-mt-md">{{ $t('pages.tv.paretoTop') }}：</div>
              <div v-for="(p, i) in pareto.rank" :key="p.employee_id" class="pareto-row">
                <span>{{ i + 1 }}. {{ p.name }}</span>
                <el-progress
                  :percentage="
                    Math.min(100, Math.round((p.value / (pareto.top_1?.value || 1)) * 100))
                  "
                  :stroke-width="10"
                />
              </div>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabEfficiency')" name="efficiency">
        <el-card>
          <el-row :gutter="16">
            <el-col :span="4"
              ><el-card class="kpi-card mini"
                ><el-statistic :title="$t('pages.tv.effAvg')" :value="efficiency.avg" /></el-card
            ></el-col>
            <el-col :span="4"
              ><el-card class="kpi-card mini"
                ><el-statistic :title="$t('pages.tv.effMax')" :value="efficiency.max" /></el-card
            ></el-col>
            <el-col :span="4"
              ><el-card class="kpi-card mini"
                ><el-statistic :title="$t('pages.tv.effMin')" :value="efficiency.min" /></el-card
            ></el-col>
            <el-col :span="4"
              ><el-card class="kpi-card mini"
                ><el-statistic :title="$t('pages.tv.effStd')" :value="efficiency.std" /></el-card
            ></el-col>
            <el-col :span="8"
              ><el-card class="kpi-card mini"
                ><el-statistic
                  :title="$t('pages.tv.effGap')"
                  :value="efficiency.top_bottom_gap" /></el-card
            ></el-col>
          </el-row>
          <el-alert type="info" :closable="false" class="av-mt-md" :title="efficiency.note" />
          <div class="av-mt-md" v-if="efficiency.by_department">
            <div v-for="(v, d) in efficiency.by_department" :key="d" class="dept-row">
              <span class="dept-name">{{ d }}</span>
              <el-progress :percentage="Math.min(100, v.avg)" :stroke-width="12" />
              <span class="dept-avg">{{ v.avg }} / {{ v.n }}{{ $t('pages.tv.people') }}</span>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabIncentive')" name="incentive">
        <el-card>
          <el-alert
            type="success"
            :closable="false"
            show-icon
            class="av-mb-md"
            :title="'双因素理论(Herzberg) + 期望理论(Vroom)：' + (incentive.theory || '')"
          />
          <el-table :data="incentive.recommendations" size="small" stripe>
            <el-table-column prop="name" :label="$t('pages.tv.colEmployee')" width="120" />
            <el-table-column prop="category_label" :label="$t('pages.tv.colCat')" width="110">
              <template #default="{ row }"
                ><el-tag :type="tagType(row.category)">{{ row.category_label }}</el-tag></template
              >
            </el-table-column>
            <el-table-column prop="motivator" label="激励建议（激励因素）" min-width="260" />
            <el-table-column prop="hygiene_risk" label="保健风险" min-width="140" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabMarket')" name="market">
        <el-card>
          <el-alert
            type="warning"
            :closable="false"
            show-icon
            class="av-mb-md"
            :title="market.note"
          />
          <el-row :gutter="16" class="av-mb-md">
            <el-col :span="8"
              ><el-card class="kpi-card mini"
                ><el-statistic title="薪酬记录" :value="market.total" /></el-card
            ></el-col>
            <el-col :span="8"
              ><el-card class="kpi-card mini"
                ><el-statistic
                  title="低于市场"
                  :value="market.below_market_count"
                  value-style="color:var(--el-color-warning)" /></el-card
            ></el-col>
            <el-col :span="8"
              ><el-card class="kpi-card mini"
                ><el-statistic
                  title="高流失风险(低薪高值)"
                  :value="(market.at_risk_underpaid_high_value || []).length"
                  value-style="color:var(--el-color-danger)" /></el-card
            ></el-col>
          </el-row>
          <el-table :data="market.employees" size="small" stripe>
            <el-table-column prop="name" :label="$t('pages.tv.colEmployee')" width="120" />
            <el-table-column prop="total_compensation" label="总薪酬" width="110" />
            <el-table-column label="市场比" width="90">
              <template #default="{ row }">
                <el-tag
                  :type="
                    row.compensation_ratio && row.compensation_ratio < 1 ? 'warning' : 'success'
                  "
                  size="small"
                >
                  {{ row.compensation_ratio ?? '-' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="value_score" label="价值分" width="90" sortable />
            <el-table-column prop="retention_risk" label="流失风险" width="100">
              <template #default="{ row }"
                ><el-tag :type="riskType(row.retention_risk)">{{
                  row.retention_risk
                }}</el-tag></template
              >
            </el-table-column>
            <el-table-column prop="recommended_adjustment" label="建议调整" width="90" />
            <el-table-column prop="adjustment_reason" label="原因" min-width="180" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabSuccession')" name="succession">
        <el-card>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            class="av-mb-md"
            :title="succession.note"
          />
          <el-row :gutter="16" class="av-mb-md">
            <el-col :span="8"
              ><el-card class="kpi-card mini"
                ><el-statistic title="继任计划数" :value="succession.total_plans" /></el-card
            ></el-col>
            <el-col :span="16"
              ><el-card class="kpi-card mini"
                ><el-statistic
                  title="无后备的高价值者"
                  :value="(succession.high_value_without_backup || []).length"
                  value-style="color:var(--el-color-danger)" /></el-card
            ></el-col>
          </el-row>
          <div class="av-mb-md">
            <div v-for="(cands, pos) in succession.by_position" :key="pos" class="position-block">
              <div class="position-title">
                {{ pos }} <span class="position-count">{{ cands.length }} 位候选</span>
              </div>
              <div v-for="c in cands" :key="c.candidate_id" class="candidate-row">
                <span>候选 {{ c.candidate_id }}</span>
                <el-tag size="small" type="info">{{ c.readiness }}</el-tag>
                <span v-if="c.gaps && c.gaps.length" class="gap-text"
                  >待补: {{ c.gaps.map((g) => g.skill || g.gap_description).join('、') }}</span
                >
              </div>
            </div>
            <el-empty
              v-if="Object.keys(succession.by_position || {}).length === 0"
              description="暂无继任计划"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabBurnout')" name="burnout">
        <el-card>
          <el-alert
            type="error"
            :closable="false"
            show-icon
            class="av-mb-md"
            :title="burnout.note"
          />
          <el-row :gutter="16" class="av-mb-md">
            <el-col :span="24"
              ><el-card class="kpi-card mini"
                ><el-statistic
                  title="明星/骨干倦怠风险人数"
                  :value="burnout.at_risk_count"
                  value-style="color:var(--el-color-danger)" /></el-card
            ></el-col>
          </el-row>
          <el-table :data="burnout.employees" size="small" stripe empty-text="暂无倦怠风险">
            <el-table-column prop="name" :label="$t('pages.tv.colEmployee')" width="120" />
            <el-table-column prop="category_label" :label="$t('pages.tv.colCat')" width="110" />
            <el-table-column prop="risk_level" :label="$t('pages.tv.colRisk')" width="90">
              <template #default="{ row }"
                ><el-tag :type="riskType(row.risk_level)">{{ row.risk_level }}</el-tag></template
              >
            </el-table-column>
            <el-table-column label="倦怠迹象" min-width="220">
              <template #default="{ row }"
                ><span class="strategy-text">{{
                  (row.burnout_indicators || []).join('；')
                }}</span></template
              >
            </el-table-column>
            <el-table-column prop="suggestion" label="建议" min-width="240" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabSkill')" name="skill">
        <el-card>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            class="av-mb-md"
            :title="skillFit.note"
          />
          <el-alert
            v-if="skillFit.reallocation_candidates && skillFit.reallocation_candidates.length"
            type="warning"
            :closable="false"
            :title="`再配置候选：${skillFit.reallocation_candidates.join('、')}（技能覆盖好但绩效低，可能放错位置）`"
            class="av-mb-md"
          />
          <el-table :data="skillFit.employees" size="small" stripe empty-text="暂无技能数据">
            <el-table-column prop="employee_id" label="员工" width="120" />
            <el-table-column prop="skills_count" label="技能数" width="90" />
            <el-table-column prop="met_count" label="达标数" width="90" />
            <el-table-column prop="gap_count" label="缺口数" width="90" />
            <el-table-column prop="total_gap" label="总缺口" width="90" sortable />
            <el-table-column prop="performance" :label="$t('pages.tv.colPerf')" width="90" />
            <el-table-column label="再配置" width="110">
              <template #default="{ row }">
                <el-tag v-if="row.reallocation_candidate" type="warning">建议换岗</el-tag>
                <el-tag v-else type="info">匹配</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('pages.tv.tabReview')" name="review">
        <el-card>
          <el-alert
            type="success"
            :closable="false"
            show-icon
            class="av-mb-md"
            :title="review.note"
          />
          <div
            class="av-mb-md"
            v-if="Object.keys(review.category_change_distribution || {}).length"
          >
            <div class="position-title">类别迁移分布</div>
            <el-table
              :data="
                Object.entries(review.category_change_distribution).map(([k, v]) => ({
                  change: k,
                  count: v,
                }))
              "
              size="small"
            >
              <el-table-column prop="change" label="迁移" />
              <el-table-column prop="count" label="人数" />
            </el-table>
          </div>
          <el-table
            :data="review.category_movements"
            size="small"
            stripe
            empty-text="暂无跨周期数据"
          >
            <el-table-column prop="employee_id" label="员工" width="110" />
            <el-table-column prop="from_category" label="上期类别" width="130" />
            <el-table-column prop="to_category" label="本期类别" width="130" />
            <el-table-column prop="from_performance" label="上期绩效" width="90" />
            <el-table-column prop="to_performance" label="本期绩效" width="90" />
            <el-table-column label="趋势" width="90">
              <template #default="{ row }">
                <el-tag :type="row.trend === 'up' ? 'success' : 'danger'" size="small">{{
                  row.trend === 'up' ? '上升' : '下降'
                }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-card class="av-mt-md mini">
            <el-statistic title="PIP 成功 / 失败 / 进行中" :value="review.pip?.success || 0" />
            <span class="pip-note"
              >成功 {{ review.pip?.success || 0 }} / 失败 {{ review.pip?.failed || 0 }} / 进行中
              {{ review.pip?.active || 0 }}</span
            >
          </el-card>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { talentValueApi } from '@/api/client'

const tab = ref('grid')
const classification = ref({ employees: [], summary: {} })
const critical = ref({ critical: [], note: '' })
const pareto = ref({ rank: [], top_20_share_pct: 0 })
const efficiency = ref({})
const incentive = ref({ recommendations: [] })
const market = ref({ employees: [] })
const succession = ref({ by_position: {} })
const burnout = ref({ employees: [] })
const skillFit = ref({ employees: [] })
const review = ref({})
const insights = ref({})

const overview = computed(() => classification.value.summary || {})

const gridCells = [
  {
    key: 'star',
    label: '明星',
    color: 'green',
    row: 0,
    col: 2,
    filter: (c) => c.category === 'star',
  },
  {
    key: 'workhorse',
    label: '骨干',
    color: 'teal',
    row: 1,
    col: 2,
    filter: (c) => c.category === 'workhorse',
  },
  {
    key: 'growing',
    label: '成长型',
    color: 'teal',
    row: 0,
    col: 1,
    filter: (c) => c.category === 'growing',
  },
  {
    key: 'stable',
    label: '稳定型',
    color: 'amber',
    row: 1,
    col: 1,
    filter: (c) => c.category === 'stable',
  },
  {
    key: 'potential',
    label: '潜力待激活',
    color: 'amber',
    row: 2,
    col: 1,
    filter: (c) => c.category === 'potential',
  },
  {
    key: 'under',
    label: '待改进',
    color: 'red',
    row: 2,
    col: 0,
    filter: (c) => c.category === 'under',
  },
]
// 补齐空位展示
gridCells.push({ key: 'g1', label: '·', color: 'muted', row: 0, col: 0, filter: () => false })
gridCells.push({ key: 'g2', label: '·', color: 'muted', row: 0, col: 1, filter: () => false })
gridCells.push({ key: 'g3', label: '·', color: 'muted', row: 2, col: 2, filter: () => false })
gridCells.push({ key: 'g4', label: '·', color: 'muted', row: 2, col: 1, filter: () => false })
gridCells.forEach((c) => {
  const list = (classification.value.employees || []).filter(c.filter)
  c.count = list.length
  c.employees = list
  c.style = { gridRow: c.row + 1, gridColumn: c.col + 1 }
})

const starWorkhorse = computed(() => (overview.value.star || 0) + (overview.value.workhorse || 0))
const ringStyle = computed(() => {
  const p = Math.min(100, pareto.value.top_20_share_pct || 0)
  return {
    background: `conic-gradient(var(--el-color-primary) ${p * 3.6}deg, var(--el-fill-color) 0deg)`,
  }
})

function tagType(cat) {
  return (
    {
      star: 'success',
      workhorse: 'primary',
      growing: 'success',
      stable: 'info',
      potential: 'warning',
      under: 'danger',
    }[cat] || 'info'
  )
}
function riskType(r) {
  return { low: 'success', medium: 'warning', high: 'danger', critical: 'danger' }[r] || 'info'
}

async function loadAll() {
  try {
    const [c, cr, p, e, i, m, s, b, sf, rv, ins] = await Promise.all([
      talentValueApi.classification(),
      talentValueApi.criticalDependency(),
      talentValueApi.pareto(),
      talentValueApi.efficiency(),
      talentValueApi.incentives(),
      talentValueApi.marketCompetitiveness(),
      talentValueApi.successionPipeline(),
      talentValueApi.burnoutWarning(),
      talentValueApi.skillFit(),
      talentValueApi.strategyReview(),
      talentValueApi.insights(),
    ])
    classification.value = c
    critical.value = cr
    pareto.value = p
    efficiency.value = e
    incentive.value = i
    market.value = m
    succession.value = s
    burnout.value = b
    skillFit.value = sf
    review.value = rv
    insights.value = ins
    rebuildGrid()
  } catch (err) {
    ElMessage.error('加载人才价值分析失败：' + (err.message || err))
  }
}

function rebuildGrid() {
  const _cats = ['star', 'workhorse', 'growing', 'stable', 'potential', 'under']
  for (const c of gridCells) {
    if (!c.filter || c.key === 'g1' || c.key === 'g2' || c.key === 'g3' || c.key === 'g4') continue
    const list = (classification.value.employees || []).filter(c.filter)
    c.count = list.length
    c.employees = list
  }
}

onMounted(loadAll)
</script>

<style scoped>
.kpi-card {
  text-align: center;
}
.kpi-card.mini :deep(.el-statistic__content) {
  font-size: 22px;
}
.av-mb-md {
  margin-bottom: 16px;
}
.av-mt-md {
  margin-top: 16px;
}
.av-mt-lg {
  margin-top: 24px;
}
.strategy-text {
  color: var(--el-text-color-regular);
  font-size: 13px;
  line-height: 1.5;
}

.box-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, auto);
  gap: 10px;
  margin-top: 12px;
}
.box-cell {
  min-height: 90px;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid var(--el-border-color-lighter);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}
.box-cell:hover {
  transform: translateY(-2px);
  box-shadow: var(--av-shadow-md);
}
.box-cell--green {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.3);
}
.box-cell--teal {
  background: rgba(20, 184, 166, 0.08);
  border-color: rgba(20, 184, 166, 0.3);
}
.box-cell--amber {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.3);
}
.box-cell--red {
  background: rgba(244, 63, 94, 0.08);
  border-color: rgba(244, 63, 94, 0.3);
}
.box-cell--muted {
  background: transparent;
  border-style: dashed;
}
.box-cell__title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.box-cell__count {
  font-size: 26px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}
.box-cell__names {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  margin-top: 4px;
}

.pareto-wrap {
  display: flex;
  gap: 28px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.pareto-gauge {
  text-align: center;
  flex-shrink: 0;
}
.pareto-ring {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  font-weight: 700;
  color: var(--el-color-primary);
  margin: 0 auto;
}
.pareto-ring::after {
  content: '';
  position: absolute;
}
.pareto-label {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.pareto-info {
  flex: 1;
  min-width: 320px;
}
.pareto-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  font-size: 13px;
}
.pareto-row .el-progress {
  flex: 1;
}
.dept-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}
.dept-name {
  width: 100px;
  font-size: 13px;
}
.dept-row .el-progress {
  flex: 1;
}
.dept-avg {
  width: 90px;
  text-align: right;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.position-block {
  margin-bottom: 14px;
}
.position-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 6px;
}
.position-count {
  font-weight: 400;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-left: 6px;
}
.candidate-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
}
.gap-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.pip-note {
  margin-left: 16px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.sys-note {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.sys-note__muted {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
