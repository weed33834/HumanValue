"""人才价值引擎 (Talent Value Engine)

面向老板/管理者，基于真实评估数据 + 管理学理论，最大化人才价值利用。

理论支撑:
- 人才九宫格 (9-Box Grid): 绩效(overall_score) × 潜力(成长维度均分) → 9 区分类
- 波士顿矩阵映射: 明星 / 骨干 / 潜力待激活 / 待改进 四类处置策略
- 双因素理论 (Herzberg): 激励因素(成就/成长/认可) vs 保健因素(薪酬/环境)
- 期望理论 (Vroom): 目标可达 × 手段清晰 × 结果有吸引力 → 激励策略
- 帕累托二八法则: 少数人贡献多数价值 → 集中度与单点依赖风险
- 单点故障 (Bus Factor): 关键且不可替代/有风险的人 = 组织脆弱点

输入: 已审批评估 (Evaluation) + 用户信息。
输出: 分类 / 策略 / 关键人风险 / 二八集中度 / 人效 / 激励建议。
"""

from __future__ import annotations

import logging
import statistics
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenant_context import get_current_tenant
from models.models import Evaluation, User

logger = logging.getLogger(__name__)

# 九宫格阈值 (0-100)
PERF_HIGH = 80.0
PERF_LOW = 65.0
POT_HIGH = 75.0
POT_LOW = 55.0

# 处置类别
CAT_STAR = "star"  # 明星: 高绩效 × 高潜力
CAT_WORKHORSE = "workhorse"  # 骨干: 高绩效 × 中低潜力
CAT_POTENTIAL = "potential"  # 潜力待激活: 低绩效 × 高潜力
CAT_UNDER = "under"  # 待改进: 低绩效 × 低潜力
CAT_GROWING = "growing"  # 成长型: 中绩效 × 高潜力
CAT_STABLE = "stable"  # 稳定型: 中绩效 × 中潜力

# 人才体系类型: 淘汰制 / 培养制 / 晋升制 / 认证制 / 灵活用工制
# 同一引擎在不同语境下, 分类标签与处置策略不同。
SYSTEM_TYPES: Dict[str, Dict[str, Any]] = {
    "enterprise_elimination": {
        "label": "企业·淘汰制",
        "context": "商业组织，人效与 ROI 驱动，绩效不达标需改进或汰换",
        "dimension_labels": {"perf": "绩效", "pot": "潜力", "risk": "流失/风险"},
        "key_metrics": ["人效", "ROI", "高绩效占比", "淘汰/PIP 率", "流失风险"],
        "core_question": "如何最大化产出并控制风险",
        "theory": "波士顿矩阵 · 期望理论 · 双因素理论 · PIP",
        "category_strategy": {
            CAT_STAR: ["承担战略级任务", "晋升/继任候选", "高激励包", "防倦怠"],
            CAT_WORKHORSE: ["薪酬公平", "认可与成就感", "导师沉淀经验", "适度轮岗"],
            CAT_POTENTIAL: [
                "目标重设(可达+清晰)",
                "辅导带教",
                "匹配岗位",
                "短期里程碑验证",
            ],
            CAT_UNDER: ["PIP 明确改进标准", "转岗测试", "合规汰换", "谨慎投入资源"],
            CAT_GROWING: ["发展计划", "关键任务锻炼", "导师制"],
            CAT_STABLE: ["保持激励", "识别成长方向", "继任梯队观察"],
        },
    },
    "academic_cultivation": {
        "label": "高校·培养制",
        "context": "育人成才，潜能与成长为本，不以淘汰为目标而以培养成才为目的",
        "dimension_labels": {
            "perf": "当前水平",
            "pot": "成长潜能",
            "risk": "学业/心理风险",
        },
        "key_metrics": ["成才率", "毕业率", "深造率", "学术产出", "进步幅度"],
        "core_question": "如何把每个学生的潜能培养成才",
        "theory": "潜能发展 · 最近发展区(维果茨基) · 成长型思维",
        "category_strategy": {
            CAT_STAR: [
                "重点培养/科研项目",
                "论文与深造(保研)",
                "导师制深耕",
                "防过度施压",
            ],
            CAT_WORKHORSE: ["巩固基础", "竞赛/实践/项目", "团队协作与互助"],
            CAT_POTENTIAL: ["帮扶计划", "补齐短板", "导师结对", "阶段性评估与鼓励"],
            CAT_UNDER: ["学业预警", "分流/帮扶而非淘汰", "心理支持", "调整培养方向"],
            CAT_GROWING: ["提升计划", "科研训练", "学术导师"],
            CAT_STABLE: ["保持节奏", "拓宽视野", "方向探索"],
        },
    },
    "public_promotion": {
        "label": "事业单位·职级晋升制",
        "context": "稳定履职，按考核合格与资历晋升职级，绩效+纪律+服务",
        "dimension_labels": {
            "perf": "履职表现",
            "pot": "职级潜力",
            "risk": "纪律/合规风险",
        },
        "key_metrics": ["职级晋升率", "考核合格率", "岗位胜任", "纪律合规"],
        "core_question": "如何公平考核并平稳晋升",
        "theory": "职级体系 · 考核制度 · 资历+能力并重",
        "category_strategy": {
            CAT_STAR: ["优先晋升", "骨干培养", "重点岗位锻炼"],
            CAT_WORKHORSE: ["按期晋升", "岗位稳定", "传帮带"],
            CAT_POTENTIAL: ["培训提升", "轮岗历练", "后备干部"],
            CAT_UNDER: ["考核警示", "培训改进", "岗位调整"],
            CAT_GROWING: ["后备梯队", "专项培养"],
            CAT_STABLE: ["按章考核", "正常晋升"],
        },
    },
    "training_certification": {
        "label": "培训·技能认证制",
        "context": "以技能达标与认证为核心，通过率/合格率衡量培养成效",
        "dimension_labels": {"perf": "掌握度", "pot": "可塑度", "risk": "流失/放弃"},
        "key_metrics": ["认证通过率", "技能达标率", "进步幅度", "续训率"],
        "core_question": "如何提高技能达标与认证通过率",
        "theory": "技能形成 · 掌握学习 · 认证标准",
        "category_strategy": {
            CAT_STAR: ["高阶认证", "助教/带训", "快速进阶"],
            CAT_WORKHORSE: ["巩固达标", "实操强化", "示范带动"],
            CAT_POTENTIAL: ["针对性补训", "小步快测", "导师辅导"],
            CAT_UNDER: ["基础回炉", "个别辅导", "调整节奏", "避免放弃"],
            CAT_GROWING: ["提速培养", "扩展技能面"],
            CAT_STABLE: ["按部就班", "保持达标"],
        },
    },
    "platform_gig": {
        "label": "平台·灵活用工制",
        "context": "按单/按结果计酬，接单能力与交付质量驱动，流动灵活",
        "dimension_labels": {
            "perf": "交付质量",
            "pot": "接单潜力",
            "risk": "活跃度/流失",
        },
        "key_metrics": ["接单率", "交付质量分", "活跃度", "好评率"],
        "core_question": "如何激励优质接单与稳定交付",
        "theory": "按结果付酬 · 平台匹配 · 灵活用工",
        "category_strategy": {
            CAT_STAR: ["优先派单", "优质标的高配", "长期合作激励"],
            CAT_WORKHORSE: ["稳定派单", "阶梯报酬", "回访维护"],
            CAT_POTENTIAL: ["技能培训", "低门槛试单", "提升接单能力"],
            CAT_UNDER: ["限制派单", "质量整改", "降级处理"],
            CAT_GROWING: ["提级培养", "更高价值单"],
            CAT_STABLE: ["常规派单", "保持活跃"],
        },
    },
}


def _active_system_type() -> str:
    """读取当前人才体系类型 (settings.talent_system_type)。"""
    try:
        from core.config import get_settings

        t = getattr(get_settings(), "talent_system_type", "enterprise_elimination")
        return t if t in SYSTEM_TYPES else "enterprise_elimination"
    except Exception:
        return "enterprise_elimination"


CATEGORY_META: Dict[str, Dict[str, Any]] = {
    CAT_STAR: {
        "label": "明星员工",
        "cn": "高绩效 × 高潜力",
        "theory": "波士顿矩阵·明星 / 9-Box 右上",
        "focus": "最大化价值：授权、晋升、承担关键项目",
        "risk": "警惕过度压榨导致倦怠/流失(双因素·保健因素失衡)",
        "actions": [
            "承担战略级任务",
            "晋升/继任候选",
            "高激励包(期望理论:结果有吸引力)",
            "防倦怠:合理负荷+认可",
        ],
    },
    CAT_WORKHORSE: {
        "label": "骨干员工",
        "cn": "高绩效 × 中/低潜力",
        "theory": "波士顿矩阵·现金牛",
        "focus": "稳定产出、激励保留",
        "risk": "易被忽视或薪酬滞后导致流失",
        "actions": [
            "薪酬公平(保健因素)",
            "认可与成就感(激励因素)",
            "作为导师沉淀经验",
            "防技能固化:适度轮岗",
        ],
    },
    CAT_POTENTIAL: {
        "label": "潜力待激活",
        "cn": "低绩效 × 高潜力",
        "theory": "9-Box 右上/波士顿·问题型",
        "focus": "诊断绩效低因:能力/意愿/资源",
        "risk": "潜力被浪费,或期望过高(期望理论:目标可达性差)",
        "actions": [
            "目标重设:可达+清晰(期望理论)",
            "辅导/带教",
            "匹配岗位与能力",
            "短期里程碑验证",
        ],
    },
    CAT_UNDER: {
        "label": "待改进",
        "cn": "低绩效 × 低潜力",
        "theory": "波士顿·瘦狗 / PIP",
        "focus": "PIP 改进或转岗/汰换",
        "risk": "长期占用成本,拖累团队人效",
        "actions": [
            "PIP(明确改进标准)",
            "转岗测试",
            "合规汰换(记录留痕)",
            "避免投入过多资源",
        ],
    },
    CAT_GROWING: {
        "label": "成长型",
        "cn": "中绩效 × 高潜力",
        "theory": "9-Box 中间偏上",
        "focus": "培养为主,防流失",
        "risk": "培养不到位易流失; 需明确成长路径",
        "actions": ["发展计划(IDP)", "关键任务锻炼", "导师制"],
    },
    CAT_STABLE: {
        "label": "稳定型",
        "cn": "中绩效 × 中潜力",
        "theory": "9-Box 中心",
        "focus": "维持产出,关注成长",
        "risk": "激励平淡易安于现状",
        "actions": ["保持激励", "识别成长方向", "纳入继任梯队观察"],
    },
}


def _avg_dim_score(employee_view: dict) -> float:
    """从员工视图的成长维度取均分作为潜力代理 (0-100)。"""
    try:
        scores = [
            float(g.get("score", 0))
            for g in (employee_view or {}).get("growth_areas", [])
            if g.get("score") is not None
        ]
        return statistics.mean(scores) if scores else 50.0
    except Exception:
        return 50.0


def _max_risk_level(manager_view: dict) -> str:
    flags = (manager_view or {}).get("risk_flags", []) or []
    order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    if not flags:
        return "low"
    return max(
        (f.get("level", "low") for f in flags if isinstance(f, dict)),
        key=lambda x: order.get(x, 1),
    )


def _strategy_for(cat: str) -> list:
    """按当前体系类型取该类别的处置策略 (培养制/淘汰制等各有侧重)。"""
    sys_t = _active_system_type()
    meta = SYSTEM_TYPES.get(sys_t, {}).get("category_strategy", {})
    return meta.get(cat) or CATEGORY_META.get(cat, {}).get("actions", [])


def classify(performance: float, potential: float) -> str:
    """9-Box → 处置类别。"""
    if performance >= PERF_HIGH and potential >= POT_HIGH:
        return CAT_STAR
    if performance >= PERF_HIGH:
        return CAT_WORKHORSE
    if performance >= PERF_LOW:
        return (
            CAT_GROWING
            if potential >= POT_HIGH
            else (CAT_POTENTIAL if potential >= POT_LOW else CAT_STABLE)
        )
    # 低绩效
    if potential >= POT_HIGH:
        return CAT_POTENTIAL
    return CAT_UNDER


def _parse_manager_view(mv: Any) -> dict:
    if isinstance(mv, dict):
        return mv
    try:
        return dict(mv or {})
    except Exception:
        return {}


class TalentValueService:
    """人才价值引擎。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def system_types(self) -> Dict[str, Any]:
        """列出全部人才体系类型及其差异。"""
        return {
            "current": _active_system_type(),
            "types": {
                k: {
                    "label": v["label"],
                    "context": v["context"],
                    "dimension_labels": v["dimension_labels"],
                    "key_metrics": v["key_metrics"],
                    "core_question": v["core_question"],
                    "theory": v["theory"],
                }
                for k, v in SYSTEM_TYPES.items()
            },
        }

    async def insights(self) -> Dict[str, Any]:
        """当前体系类型的引擎洞察: 分类逻辑与处置策略如何在当前语境下生效。"""
        sys_t = _active_system_type()
        meta = SYSTEM_TYPES[sys_t]
        return {
            "system_type": sys_t,
            "label": meta["label"],
            "context": meta["context"],
            "core_question": meta["core_question"],
            "theory": meta["theory"],
            "key_metrics": meta["key_metrics"],
            "dimension_labels": meta["dimension_labels"],
            "strategy_preview": {
                CATEGORY_META[k]["label"]: SYSTEM_TYPES[sys_t]["category_strategy"].get(
                    k, []
                )
                for k in CATEGORY_META
            },
            "distinct_note": (
                "培养制以潜能与成才为本(帮扶/分流而非淘汰); 淘汰制以人效与ROI为本(PIP/汰换)。"
                "引擎分类结构相同, 但处置策略与关键指标随体系类型切换。"
            ),
        }

    async def _latest_evaluations(self) -> List[tuple]:
        """取每个员工最近一个已审批周期的评估 + 用户信息。"""
        tenant = get_current_tenant()
        evals = (
            (
                await self.session.execute(
                    select(Evaluation).where(
                        Evaluation.tenant_id == tenant,
                        Evaluation.status.in_(["approved", "completed"]),
                    )
                )
            )
            .scalars()
            .all()
        )
        # 按员工取最近周期
        latest: Dict[str, Evaluation] = {}
        for e in evals:
            cur = latest.get(e.employee_id)
            if cur is None or e.period > cur.period:
                latest[e.employee_id] = e
        users = {
            u.user_id: u
            for u in (
                await self.session.execute(select(User).where(User.tenant_id == tenant))
            )
            .scalars()
            .all()
        }
        # 无 User 记录时也保留该员工 (用 employee_id 兜底), 避免数据缺失导致被过滤
        return [(latest[uid], users.get(uid)) for uid in latest]

    async def talent_classification(self) -> Dict[str, Any]:
        """全员九宫格分类 + 处置策略。"""
        rows = await self._latest_evaluations()
        employees = []
        summary = {k: 0 for k in CATEGORY_META}
        for ev, user in rows:
            mv = _parse_manager_view(ev.manager_view)
            performance = float(ev.overall_score or 0)
            potential = _avg_dim_score(ev.employee_view)
            cat = classify(performance, potential)
            summary[cat] = summary.get(cat, 0) + 1
            employees.append(
                {
                    "employee_id": ev.employee_id,
                    "name": user.name if user else ev.employee_id,
                    "department": user.department if user else None,
                    "performance": round(performance, 1),
                    "potential": round(potential, 1),
                    "category": cat,
                    "category_label": CATEGORY_META[cat]["label"],
                    "risk_level": _max_risk_level(mv),
                    "roi": (mv.get("roi_analysis") or "")[:200],
                    "reallocation": (mv.get("reallocation_suggestion") or "")[:200],
                    "strategy": _strategy_for(cat),
                    "risk_note": CATEGORY_META[cat]["risk"],
                }
            )
        # 按 价值(绩效×潜力) 降序
        employees.sort(key=lambda e: e["performance"] * e["potential"], reverse=True)
        sys_t = _active_system_type()
        return {
            "generated_from": "已审批评估",
            "system_type": sys_t,
            "system_type_label": SYSTEM_TYPES[sys_t]["label"],
            "summary": summary,
            "categories": {k: CATEGORY_META[k] for k in CATEGORY_META},
            "employees": employees,
            "total": len(employees),
        }

    async def critical_dependency(self) -> Dict[str, Any]:
        """单点依赖/关键人风险: 高价值 × 高风险(或团队唯一高价值) = 组织脆弱点。"""
        rows = await self._latest_evaluations()
        scored = []
        for ev, user in rows:
            mv = _parse_manager_view(ev.manager_view)
            performance = float(ev.overall_score or 0)
            potential = _avg_dim_score(ev.employee_view)
            value = performance * potential
            risk = _max_risk_level(mv)
            scored.append(
                {
                    "employee_id": ev.employee_id,
                    "name": user.name if user else ev.employee_id,
                    "department": user.department if user else None,
                    "value": round(value, 1),
                    "performance": round(performance, 1),
                    "potential": round(potential, 1),
                    "risk_level": risk,
                    "critical": value >= 6000 and risk in ("high", "critical"),
                }
            )
        scored.sort(key=lambda x: x["value"], reverse=True)
        criticals = [s for s in scored if s["critical"]]
        return {
            "critical_count": len(criticals),
            "critical": criticals,
            "note": "关键人 = 高价值且高风险(不可替代 + 有流失/塌方风险)。建议备份、知识沉淀、继任梯队。",
            "all": scored,
        }

    async def pareto_concentration(self) -> Dict[str, Any]:
        """二八价值集中度: 前 N 名贡献占比, 提示对少数人的依赖。"""
        rows = await self._latest_evaluations()
        vals = []
        for ev, user in rows:
            value = float(ev.overall_score or 0) * _avg_dim_score(ev.employee_view)
            vals.append(
                {
                    "employee_id": ev.employee_id,
                    "name": user.name if user else ev.employee_id,
                    "value": round(value, 1),
                }
            )
        vals.sort(key=lambda x: x["value"], reverse=True)
        total = sum(v["value"] for v in vals) or 1
        top20_pct = max(1, round(len(vals) * 0.2))
        top20 = vals[:top20_pct]
        top20_share = round(sum(v["value"] for v in top20) / total * 100, 1)
        top1 = vals[0] if vals else None
        return {
            "total": len(vals),
            "top_20_count": top20_pct,
            "top_20_share_pct": top20_share,
            "top_1": top1,
            "warning": (
                "依赖度过高: 建议为高价值者建立备份与知识沉淀, 降低单点风险"
                if top20_share >= 60
                else "价值分布相对均衡"
            ),
            "rank": vals[: max(10, top20_pct)],
        }

    async def team_efficiency(self) -> Dict[str, Any]:
        """人效/团队价值密度: 均值/最高/最低/离散度 + 头部依赖。"""
        rows = await self._latest_evaluations()
        scores = []
        by_dept: Dict[str, List[float]] = {}
        for ev, user in rows:
            p = float(ev.overall_score or 0)
            scores.append(p)
            d = user.department if user else "未分组"
            by_dept.setdefault(d, []).append(p)
        if not scores:
            return {"total": 0, "note": "暂无已审批评估"}
        dept_stats = {
            d: {"avg": round(statistics.mean(v), 1), "n": len(v)}
            for d, v in by_dept.items()
        }
        return {
            "total": len(scores),
            "avg": round(statistics.mean(scores), 1),
            "max": round(max(scores), 1),
            "min": round(min(scores), 1),
            "std": round(statistics.pstdev(scores), 1),
            "top_bottom_gap": round(max(scores) - min(scores), 1),
            "by_department": dept_stats,
            "note": "绩效离散度大 → 头部依赖高、尾部拖累人效; 建议头部防流失 + 尾部提效或转岗。",
        }

    async def incentive_recommendations(self) -> Dict[str, Any]:
        """激励策略推荐 (双因素 + 期望理论)。"""
        rows = await self._latest_evaluations()
        out = []
        for ev, user in rows:
            mv = _parse_manager_view(ev.manager_view)
            p = float(ev.overall_score or 0)
            pot = _avg_dim_score(ev.employee_view)
            risk = _max_risk_level(mv)
            cat = classify(p, pot)
            # 双因素: 激励因素 vs 保健因素
            if cat in (CAT_STAR, CAT_WORKHORSE):
                motivator = "高绩效: 重成就/成长/认可(激励因素), 薪酬公平(保健因素)"
                hygiene_risk = (
                    "倦怠风险" if risk in ("high", "critical") else "激励疲劳"
                )
            elif cat == CAT_POTENTIAL:
                motivator = "潜力型: 重目标可达+清晰(期望理论), 匹配岗位, 避免期望落空"
                hygiene_risk = "期望落差"
            else:
                motivator = "待改进型: 明确改进标准(PIP), 阶段性反馈, 慎投资源"
                hygiene_risk = "绩效拖累"
            out.append(
                {
                    "employee_id": ev.employee_id,
                    "name": user.name if user else ev.employee_id,
                    "performance": round(p, 1),
                    "potential": round(pot, 1),
                    "category": cat,
                    "category_label": CATEGORY_META[cat]["label"],
                    "risk_level": risk,
                    "motivator": motivator,
                    "hygiene_risk": hygiene_risk,
                }
            )
        return {
            "recommendations": out,
            "theory": "双因素理论(Herzberg) + 期望理论(Vroom)",
        }

    # ================= 市场价值对标 / 薪酬竞争力 =================

    async def market_competitiveness(self) -> Dict[str, Any]:
        """薪酬竞争力: 市场基准比(compensation_ratio) × 人才价值 → 流失风险与调薪建议。

        理论: 期望理论(薪酬是保健因素) + 双因素 — 高价值低薪酬 = 高流失风险。
        """
        from models.talent_models import CompensationRecord

        tenant = get_current_tenant()
        comps = (
            (
                await self.session.execute(
                    select(CompensationRecord).where(
                        CompensationRecord.tenant_id == tenant
                    )
                )
            )
            .scalars()
            .all()
        )
        # 每员工取最近周期
        latest_comp: Dict[str, CompensationRecord] = {}
        for c in comps:
            cur = latest_comp.get(c.employee_id)
            if cur is None or c.period > cur.period:
                latest_comp[c.employee_id] = c

        rows = await self._latest_evaluations()
        by_emp = {ev.employee_id: (ev, user) for ev, user in rows}
        out = []
        at_risk = []
        for eid, comp in latest_comp.items():
            ratio = comp.compensation_ratio
            ev, user = by_emp.get(eid, (None, None))
            perf = float(ev.overall_score or 0) if ev else 0
            pot = _avg_dim_score(ev.employee_view) if ev else 0
            value = perf * pot
            below = ratio is not None and ratio < 1.0
            risk = (
                "high" if (below and value >= 6000) else ("medium" if below else "low")
            )
            if risk == "high":
                at_risk.append(eid)
            out.append(
                {
                    "employee_id": eid,
                    "name": user.name if user else eid,
                    "department": user.department if user else None,
                    "total_compensation": comp.total_compensation,
                    "market_benchmark": comp.market_benchmark,
                    "market_percentile": comp.market_percentile,
                    "compensation_ratio": (
                        round(ratio, 3) if ratio is not None else None
                    ),
                    "value_score": round(value, 1),
                    "below_market": below,
                    "retention_risk": risk,
                    "recommended_adjustment": comp.recommended_adjustment,
                    "adjustment_reason": comp.adjustment_reason,
                }
            )
        out.sort(key=lambda x: x.get("value_score") or 0, reverse=True)
        return {
            "total": len(out),
            "below_market_count": sum(1 for x in out if x["below_market"]),
            "at_risk_underpaid_high_value": at_risk,
            "note": "compensation_ratio < 1 = 低于市场。高价值(价值分≥6000)却低于市场 = 高流失风险, 建议优先调薪(保健因素)。",
            "employees": out,
        }

    # ================= 继任梯队 / 领导力管道 =================

    async def succession_pipeline(self) -> Dict[str, Any]:
        """继任梯队覆盖: 关键岗位是否有后备, 准备度分布, 高价值者的继任候选。"""
        from models.talent_models import SuccessionPlan

        tenant = get_current_tenant()
        plans = (
            (
                await self.session.execute(
                    select(SuccessionPlan).where(
                        SuccessionPlan.tenant_id == tenant,
                        SuccessionPlan.status.in_(["active", "promoted"]),
                    )
                )
            )
            .scalars()
            .all()
        )
        readiness_dist = {}
        by_position: Dict[str, List[dict]] = {}
        for p in plans:
            readiness_dist[p.readiness] = readiness_dist.get(p.readiness, 0) + 1
            by_position.setdefault(p.position_title, []).append(
                {
                    "candidate_id": p.candidate_id,
                    "current_holder_id": p.current_holder_id,
                    "readiness": p.readiness,
                    "gaps": p.development_gaps or [],
                }
            )
        # 高价值者是否有继任候选
        rows = await self._latest_evaluations()
        high_value_ids = set()
        for ev, user in rows:
            value = float(ev.overall_score or 0) * _avg_dim_score(ev.employee_view)
            if value >= 6000:
                high_value_ids.add(ev.employee_id)
        covered_high_value = {
            eid: any(p.current_holder_id == eid for p in plans)
            for eid in high_value_ids
        }
        return {
            "total_plans": len(plans),
            "readiness_distribution": readiness_dist,
            "by_position": by_position,
            "high_value_with_backup": {eid: v for eid, v in covered_high_value.items()},
            "high_value_without_backup": [
                eid for eid, v in covered_high_value.items() if not v
            ],
            "note": "继任梯队 = 关键岗位后备保障。高价值者若无后备 = 单点风险, 应提前 1-2 年培养候选。",
        }

    # ================= 明星倦怠预警 / 负荷均衡 =================

    _BURNOUT_KEYWORDS = (
        "倦怠",
        "负荷",
        "过载",
        "疲劳",
        "工作量大",
        "burnout",
        "overload",
        "长时间",
        "加班",
    )

    async def burnout_warning(self) -> Dict[str, Any]:
        """明星员工倦怠预警 + 负荷均衡建议。

        理论: 双因素 — 明星被过度压榨(保健因素失衡) → 倦怠/流失, 高价值损失。
        """
        rows = await self._latest_evaluations()
        out = []
        for ev, user in rows:
            mv = _parse_manager_view(ev.manager_view)
            perf = float(ev.overall_score or 0)
            pot = _avg_dim_score(ev.employee_view)
            cat = classify(perf, pot)
            if cat not in (CAT_STAR, CAT_WORKHORSE):
                continue  # 仅关注高价值
            flags = mv.get("risk_flags", []) or []
            burnout_hits = []
            for f in flags:
                if isinstance(f, dict):
                    text = f"{f.get('category','')} {f.get('description','')} {f.get('suggested_action','')}"
                    if any(kw in text for kw in self._BURNOUT_KEYWORDS):
                        burnout_hits.append(f)
            risk = _max_risk_level(mv)
            level = (
                "high"
                if (burnout_hits or risk in ("high", "critical"))
                else ("medium" if risk == "medium" else "low")
            )
            if level == "low":
                continue
            out.append(
                {
                    "employee_id": ev.employee_id,
                    "name": user.name if user else ev.employee_id,
                    "performance": round(perf, 1),
                    "potential": round(pot, 1),
                    "category": cat,
                    "category_label": CATEGORY_META[cat]["label"],
                    "risk_level": level,
                    "burnout_indicators": [
                        f.get("category", "")
                        + (
                            ": " + f.get("description", "")[:60]
                            if f.get("description")
                            else ""
                        )
                        for f in burnout_hits
                    ]
                    or ["综合风险偏高"],
                    "suggestion": "识别关键项目负荷, 分配可替代/协作者, 提供恢复期与认可(防倦怠流失)",
                }
            )
        out.sort(
            key=lambda x: {"high": 3, "medium": 2}.get(x["risk_level"], 1), reverse=True
        )
        return {
            "at_risk_count": len(out),
            "employees": out,
            "note": "明星/骨干高价值但倦怠风险 → 组织最大隐形损失。建议负荷均衡 + 认可 + 合理边界。",
        }

    # ================= 技能 / 岗位匹配度 =================

    async def skill_fit(self) -> Dict[str, Any]:
        """技能/岗位匹配度 + 再配置建议。

        理论: 人岗匹配 — 高技能低绩效(放错位置) → 再配置; 低技能高要求(缺口) → 培训/招聘。
        """
        from models.talent_models import EmployeeSkill

        tenant = get_current_tenant()
        skills = (
            (
                await self.session.execute(
                    select(EmployeeSkill).where(EmployeeSkill.tenant_id == tenant)
                )
            )
            .scalars()
            .all()
        )
        by_emp: Dict[str, List[dict]] = {}
        for s in skills:
            by_emp.setdefault(s.employee_id, []).append(
                {
                    "skill_id": s.skill_id,
                    "current_level": s.current_level,
                    "target_level": s.target_level,
                    "gap": s.gap,
                }
            )
        rows = await self._latest_evaluations()
        emp_perf = {ev.employee_id: float(ev.overall_score or 0) for ev, _ in rows}
        out = []
        reallocate = []
        for eid, sk in by_emp.items():
            total_gap = sum(x["gap"] for x in sk)
            gap_count = sum(1 for x in sk if x["gap"] > 0)
            met = sum(1 for x in sk if x["gap"] <= 0)
            perf = emp_perf.get(eid)
            # 高技能低绩效 = 放错位置 → 再配置候选
            if perf is not None and perf < PERF_LOW and met >= max(1, len(sk) * 0.6):
                reallocate.append(eid)
            out.append(
                {
                    "employee_id": eid,
                    "skills_count": len(sk),
                    "met_count": met,
                    "gap_count": gap_count,
                    "total_gap": total_gap,
                    "performance": perf,
                    "reallocation_candidate": perf is not None
                    and perf < PERF_LOW
                    and met >= max(1, len(sk) * 0.6),
                }
            )
        return {
            "total_with_skills": len(out),
            "reallocation_candidates": reallocate,
            "note": "技能覆盖好但绩效低 = 可能放错位置/激励不足 → 再配置或换岗; 缺口大 = 需培训/招聘补齐。",
            "employees": out,
        }

    # ================= 季度复盘 / 策略成效 =================

    async def strategy_review(self) -> Dict[str, Any]:
        """季度策略复盘: 员工在周期间的类别迁移 + PIP 成效, 验证人才策略是否有效。"""
        from models.talent_models import PerformanceImprovementPlan

        tenant = get_current_tenant()
        # 取每个员工最近两个周期的评估, 计算类别迁移
        evals = (
            (
                await self.session.execute(
                    select(Evaluation).where(
                        Evaluation.tenant_id == tenant,
                        Evaluation.status.in_(["approved", "completed"]),
                    )
                )
            )
            .scalars()
            .all()
        )
        by_emp: Dict[str, List[Evaluation]] = {}
        for e in evals:
            by_emp.setdefault(e.employee_id, []).append(e)
        movements = []
        cat_change = {}
        for eid, lst in by_emp.items():
            lst.sort(key=lambda e: e.period)
            if len(lst) < 2:
                continue
            last, prev = lst[-1], lst[-2]
            cat_last = classify(
                float(last.overall_score or 0), _avg_dim_score(last.employee_view)
            )
            cat_prev = classify(
                float(prev.overall_score or 0), _avg_dim_score(prev.employee_view)
            )
            if cat_last != cat_prev:
                key = f"{CATEGORY_META[cat_prev]['label']} → {CATEGORY_META[cat_last]['label']}"
                cat_change[key] = cat_change.get(key, 0) + 1
            movements.append(
                {
                    "employee_id": eid,
                    "from_category": CATEGORY_META[cat_prev]["label"],
                    "to_category": CATEGORY_META[cat_last]["label"],
                    "from_performance": round(float(prev.overall_score or 0), 1),
                    "to_performance": round(float(last.overall_score or 0), 1),
                    "trend": (
                        "up"
                        if (last.overall_score or 0) > (prev.overall_score or 0)
                        else "down"
                    ),
                }
            )
        # PIP 成效
        pips = (
            (
                await self.session.execute(
                    select(PerformanceImprovementPlan).where(
                        PerformanceImprovementPlan.tenant_id == tenant
                    )
                )
            )
            .scalars()
            .all()
        )
        pip_stats = {"total": len(pips), "success": 0, "failed": 0, "active": 0}
        for p in pips:
            if p.status == "completed-success":
                pip_stats["success"] += 1
            elif p.status == "completed-failed":
                pip_stats["failed"] += 1
            elif p.status == "active":
                pip_stats["active"] += 1
        return {
            "periods_analyzed": sorted({e.period for e in evals}),
            "category_movements": movements,
            "category_change_distribution": cat_change,
            "pip": pip_stats,
            "note": "类别上迁 = 策略有效; 下迁 = 需复盘干预。PIP 成功率衡量改进流程成效。",
        }
