"""
人才成长路由 — 技能矩阵 / 薪酬洞察 / 内部流动 / 团队健康度 / 多期趋势

端点前缀: /api/v1/growth
权限: Boss / Manager / HR / Admin
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from auth.rbac import Role, get_current_user_id, require_role
from core.database import get_db
from core.tenant_context import get_current_tenant
from models.talent_models import (
    CompensationRecord,
    EmployeeSkill,
    InternalApplication,
    JobPosting,
    Skill,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/growth", tags=["growth"])


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def _tenant() -> str:
    return get_current_tenant() or "default"


# ============================================================
# Schemas
# ============================================================


class SkillCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    category: str = Field(default="technical", max_length=64)
    description: Optional[str] = None


class EmployeeSkillCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: str = Field(min_length=1, max_length=64)
    skill_id: str = Field(min_length=1, max_length=128)
    current_level: int = Field(ge=1, le=5)
    target_level: int = Field(default=3, ge=1, le=5)
    notes: Optional[str] = None


class EmployeeSkillUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_level: Optional[int] = Field(default=None, ge=1, le=5)
    target_level: Optional[int] = Field(default=None, ge=1, le=5)
    notes: Optional[str] = None


class CompensationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: str = Field(min_length=1, max_length=64)
    base_salary: float = Field(ge=0)
    bonus: float = Field(default=0, ge=0)
    equity_value: float = Field(default=0, ge=0)
    market_benchmark: Optional[float] = None
    market_percentile: Optional[float] = None
    last_review_date: Optional[datetime] = None
    recommended_adjustment: Optional[float] = None
    adjustment_reason: Optional[str] = None
    period: str = Field(min_length=1, max_length=32)


class JobPostingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=256)
    department: Optional[str] = None
    job_type: str = Field(default="fulltime", max_length=32)
    description: str = Field(min_length=1, max_length=5000)
    required_skills: List[Dict[str, Any]] = Field(default_factory=list, max_length=20)
    preferred_skills: List[Dict[str, Any]] = Field(default_factory=list, max_length=20)
    location: Optional[str] = None
    closing_date: Optional[datetime] = None


class InternalApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    posting_id: str = Field(min_length=1, max_length=128)
    cover_note: Optional[str] = None


# ============================================================
# 技能矩阵
# ============================================================


@router.post("/skills", response_model=Dict[str, Any])
async def create_skill(
    payload: SkillCreate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建技能定义"""
    skill = Skill(
        skill_id=_new_id("skill"),
        name=payload.name,
        category=payload.category,
        description=payload.description,
        proficiency_levels=[
            {"level": 1, "label": "入门", "description": "了解基本概念"},
            {"level": 2, "label": "基础", "description": "能完成简单任务"},
            {"level": 3, "label": "熟练", "description": "独立完成常规工作"},
            {"level": 4, "label": "精通", "description": "能解决复杂问题"},
            {"level": 5, "label": "专家", "description": "能指导他人并制定标准"},
        ],
        tenant_id=_tenant(),
    )
    session.add(skill)
    await session.commit()
    return {"skill_id": skill.skill_id, "status": "created"}


@router.get("/skills", response_model=Dict[str, Any])
async def list_skills(
    category: Optional[str] = None,
    name: Optional[str] = None,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询技能列表"""
    conditions = [Skill.tenant_id == _tenant(), Skill.is_active.is_(True)]
    if category:
        conditions.append(Skill.category == category)
    if name:
        conditions.append(Skill.name.ilike(f"%{name}%"))
    result = await session.execute(
        select(Skill).where(and_(*conditions)).order_by(Skill.category, Skill.name)
    )
    skills = result.scalars().all()
    return {
        "items": [
            {
                "skill_id": s.skill_id,
                "name": s.name,
                "category": s.category,
                "description": s.description,
                "proficiency_levels": s.proficiency_levels,
            }
            for s in skills
        ],
        "total": len(skills),
    }


@router.post("/employee-skills", response_model=Dict[str, Any])
async def set_employee_skill(
    payload: EmployeeSkillCreate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """设置/更新员工技能水平"""
    # 检查是否已有记录
    result = await session.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == payload.employee_id,
            EmployeeSkill.skill_id == payload.skill_id,
            EmployeeSkill.tenant_id == _tenant(),
        )
    )
    existing = result.scalar_one_or_none()
    gap = payload.target_level - payload.current_level
    if existing:
        existing.current_level = payload.current_level
        existing.target_level = payload.target_level
        existing.gap = gap
        existing.notes = payload.notes
        existing.last_assessed_at = datetime.now(timezone.utc)
        await session.commit()
        return {"record_id": existing.record_id, "status": "updated"}
    record = EmployeeSkill(
        record_id=_new_id("es"),
        employee_id=payload.employee_id,
        skill_id=payload.skill_id,
        current_level=payload.current_level,
        target_level=payload.target_level,
        gap=gap,
        notes=payload.notes,
        tenant_id=_tenant(),
    )
    session.add(record)
    await session.commit()
    return {"record_id": record.record_id, "status": "created"}


@router.get("/employee-skills/{employee_id}", response_model=Dict[str, Any])
async def get_employee_skills(
    employee_id: str,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """获取员工技能矩阵"""
    result = await session.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.tenant_id == _tenant(),
        )
    )
    records = result.scalars().all()
    # 关联技能名称
    skill_ids = [r.skill_id for r in records]
    skills_map = {}
    if skill_ids:
        skill_result = await session.execute(
            select(Skill).where(Skill.skill_id.in_(skill_ids))
        )
        for s in skill_result.scalars().all():
            skills_map[s.skill_id] = {"name": s.name, "category": s.category}

    items = []
    for r in records:
        skill_info = skills_map.get(r.skill_id, {})
        items.append(
            {
                "record_id": r.record_id,
                "skill_id": r.skill_id,
                "skill_name": skill_info.get("name", r.skill_id),
                "category": skill_info.get("category", "unknown"),
                "current_level": r.current_level,
                "target_level": r.target_level,
                "gap": r.gap,
                "assessment_source": r.assessment_source,
                "last_assessed_at": (
                    r.last_assessed_at.isoformat() if r.last_assessed_at else None
                ),
                "notes": r.notes,
            }
        )
    total_gaps = sum(1 for i in items if i["gap"] > 0)
    return {
        "employee_id": employee_id,
        "items": items,
        "total_skills": len(items),
        "gap_count": total_gaps,
        "avg_level": round(
            sum(i["current_level"] for i in items) / max(len(items), 1), 2
        ),
    }


@router.get("/skill-matrix/team", response_model=Dict[str, Any])
async def team_skill_matrix(
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """团队技能矩阵概览"""
    result = await session.execute(
        select(EmployeeSkill).where(EmployeeSkill.tenant_id == _tenant())
    )
    records = result.scalars().all()
    # 按技能聚合
    skill_agg = {}
    for r in records:
        if r.skill_id not in skill_agg:
            skill_agg[r.skill_id] = {"levels": [], "gaps": []}
        skill_agg[r.skill_id]["levels"].append(r.current_level)
        skill_agg[r.skill_id]["gaps"].append(r.gap)
    # 获取技能名称
    skill_ids = list(skill_agg.keys())
    skills_map = {}
    if skill_ids:
        skill_result = await session.execute(
            select(Skill).where(Skill.skill_id.in_(skill_ids))
        )
        for s in skill_result.scalars().all():
            skills_map[s.skill_id] = {"name": s.name, "category": s.category}

    matrix = []
    for sid, agg in skill_agg.items():
        info = skills_map.get(sid, {})
        avg = sum(agg["levels"]) / len(agg["levels"]) if agg["levels"] else 0
        total_gap = sum(g for g in agg["gaps"] if g > 0)
        matrix.append(
            {
                "skill_id": sid,
                "skill_name": info.get("name", sid),
                "category": info.get("category", "unknown"),
                "avg_level": round(avg, 2),
                "employee_count": len(agg["levels"]),
                "total_gap": total_gap,
            }
        )
    matrix.sort(key=lambda x: x["total_gap"], reverse=True)
    return {"items": matrix, "total": len(matrix)}


# ============================================================
# 薪酬洞察
# ============================================================


@router.post("/compensation", response_model=Dict[str, Any])
async def create_compensation(
    payload: CompensationCreate,
    role: Role = Depends(require_role(Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建/更新薪酬记录"""
    total = payload.base_salary + payload.bonus + payload.equity_value
    ratio = (
        round(total / payload.market_benchmark, 3) if payload.market_benchmark else None
    )
    record = CompensationRecord(
        record_id=_new_id("comp"),
        employee_id=payload.employee_id,
        base_salary=payload.base_salary,
        bonus=payload.bonus,
        equity_value=payload.equity_value,
        total_compensation=total,
        market_benchmark=payload.market_benchmark,
        market_percentile=payload.market_percentile,
        compensation_ratio=ratio,
        last_review_date=payload.last_review_date,
        recommended_adjustment=payload.recommended_adjustment,
        adjustment_reason=payload.adjustment_reason,
        period=payload.period,
        tenant_id=_tenant(),
    )
    session.add(record)
    await session.commit()
    return {"record_id": record.record_id, "status": "created"}


@router.get("/compensation", response_model=Dict[str, Any])
async def list_compensation(
    employee_id: Optional[str] = None,
    period: Optional[str] = None,
    role: Role = Depends(require_role(Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询薪酬记录"""
    conditions = [CompensationRecord.tenant_id == _tenant()]
    if employee_id:
        conditions.append(CompensationRecord.employee_id == employee_id)
    if period:
        conditions.append(CompensationRecord.period == period)
    result = await session.execute(
        select(CompensationRecord)
        .where(and_(*conditions))
        .order_by(CompensationRecord.created_at.desc())
    )
    records = result.scalars().all()
    return {
        "items": [
            {
                "record_id": r.record_id,
                "employee_id": r.employee_id,
                "base_salary": r.base_salary,
                "bonus": r.bonus,
                "equity_value": r.equity_value,
                "total_compensation": r.total_compensation,
                "market_benchmark": r.market_benchmark,
                "market_percentile": r.market_percentile,
                "compensation_ratio": r.compensation_ratio,
                "last_review_date": (
                    r.last_review_date.isoformat() if r.last_review_date else None
                ),
                "recommended_adjustment": r.recommended_adjustment,
                "adjustment_reason": r.adjustment_reason,
                "period": r.period,
            }
            for r in records
        ],
        "total": len(records),
    }


@router.get("/compensation/insights", response_model=Dict[str, Any])
async def compensation_insights(
    period: Optional[str] = None,
    role: Role = Depends(require_role(Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """薪酬洞察分析"""
    conditions = [CompensationRecord.tenant_id == _tenant()]
    if period:
        conditions.append(CompensationRecord.period == period)
    result = await session.execute(select(CompensationRecord).where(and_(*conditions)))
    records = result.scalars().all()
    if not records:
        return {
            "total_employees": 0,
            "avg_total": None,
            "below_market": 0,
            "above_market": 0,
        }
    totals = [r.total_compensation for r in records]
    below = sum(
        1 for r in records if r.compensation_ratio and r.compensation_ratio < 0.9
    )
    above = sum(
        1 for r in records if r.compensation_ratio and r.compensation_ratio > 1.1
    )
    return {
        "total_employees": len(records),
        "avg_total": round(sum(totals) / len(totals), 2),
        "median_total": sorted(totals)[len(totals) // 2],
        "below_market": below,
        "at_market": len(records) - below - above,
        "above_market": above,
        "avg_ratio": round(
            sum(r.compensation_ratio for r in records if r.compensation_ratio)
            / max(sum(1 for r in records if r.compensation_ratio), 1),
            3,
        ),
    }


# ============================================================
# 内部人才流动
# ============================================================


@router.post("/job-postings", response_model=Dict[str, Any])
async def create_job_posting(
    payload: JobPostingCreate,
    request: Request,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """发布内部岗位/项目机会"""
    actor_id = await get_current_user_id(request)
    posting = JobPosting(
        posting_id=_new_id("job"),
        title=payload.title,
        department=payload.department,
        job_type=payload.job_type,
        description=payload.description,
        required_skills=payload.required_skills,
        preferred_skills=payload.preferred_skills,
        location=payload.location,
        posted_by=actor_id,
        closing_date=payload.closing_date,
        tenant_id=_tenant(),
    )
    session.add(posting)
    await session.commit()
    return {"posting_id": posting.posting_id, "status": "created"}


@router.get("/job-postings", response_model=Dict[str, Any])
async def list_job_postings(
    job_type: Optional[str] = None,
    department: Optional[str] = None,
    role: Role = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)
    ),
    session: AsyncSession = Depends(get_db),
):
    """查询内部岗位列表"""
    conditions = [JobPosting.tenant_id == _tenant(), JobPosting.status == "open"]
    if job_type:
        conditions.append(JobPosting.job_type == job_type)
    if department:
        conditions.append(JobPosting.department == department)
    result = await session.execute(
        select(JobPosting)
        .where(and_(*conditions))
        .order_by(JobPosting.created_at.desc())
    )
    postings = result.scalars().all()
    return {
        "items": [
            {
                "posting_id": p.posting_id,
                "title": p.title,
                "department": p.department,
                "job_type": p.job_type,
                "description": p.description,
                "required_skills": p.required_skills,
                "preferred_skills": p.preferred_skills,
                "location": p.location,
                "posted_by": p.posted_by,
                "closing_date": p.closing_date.isoformat() if p.closing_date else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in postings
        ],
        "total": len(postings),
    }


@router.post("/applications", response_model=Dict[str, Any])
async def apply_internal(
    payload: InternalApplicationCreate,
    request: Request,
    role: Role = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)
    ),
    session: AsyncSession = Depends(get_db),
):
    """申请内部岗位"""
    actor_id = await get_current_user_id(request)
    # 检查是否已申请
    existing = await session.execute(
        select(InternalApplication).where(
            InternalApplication.posting_id == payload.posting_id,
            InternalApplication.applicant_id == actor_id,
            InternalApplication.tenant_id == _tenant(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="已申请过此岗位"
        )
    # 简单匹配：基于技能匹配度（如有员工技能数据）
    match_score = None
    match_reasons = []
    # 查询岗位要求
    posting_result = await session.execute(
        select(JobPosting).where(
            JobPosting.posting_id == payload.posting_id,
            JobPosting.tenant_id == _tenant(),
        )
    )
    posting = posting_result.scalar_one_or_none()
    if posting and posting.required_skills:
        # 查询申请人技能
        skills_result = await session.execute(
            select(EmployeeSkill).where(
                EmployeeSkill.employee_id == actor_id,
                EmployeeSkill.tenant_id == _tenant(),
            )
        )
        emp_skills = {
            s.skill_id: s.current_level for s in skills_result.scalars().all()
        }
        matched = 0
        total_req = len(posting.required_skills)
        for req in posting.required_skills:
            sid = req.get("skill_id")
            min_level = req.get("min_level", 3)
            if sid and emp_skills.get(sid, 0) >= min_level:
                matched += 1
        if total_req > 0:
            match_score = round(matched / total_req * 100, 1)
            match_reasons.append(f"技能匹配 {matched}/{total_req}")
    app = InternalApplication(
        application_id=_new_id("app"),
        posting_id=payload.posting_id,
        applicant_id=actor_id,
        match_score=match_score,
        match_reasons=match_reasons,
        cover_note=payload.cover_note,
        tenant_id=_tenant(),
    )
    session.add(app)
    await session.commit()
    return {
        "application_id": app.application_id,
        "match_score": match_score,
        "status": "applied",
    }


@router.get("/applications", response_model=Dict[str, Any])
async def list_applications(
    posting_id: Optional[str] = None,
    applicant_id: Optional[str] = None,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询内部申请列表"""
    conditions = [InternalApplication.tenant_id == _tenant()]
    if posting_id:
        conditions.append(InternalApplication.posting_id == posting_id)
    if applicant_id:
        conditions.append(InternalApplication.applicant_id == applicant_id)
    result = await session.execute(
        select(InternalApplication)
        .where(and_(*conditions))
        .order_by(InternalApplication.created_at.desc())
    )
    apps = result.scalars().all()
    return {
        "items": [
            {
                "application_id": a.application_id,
                "posting_id": a.posting_id,
                "applicant_id": a.applicant_id,
                "match_score": a.match_score,
                "match_reasons": a.match_reasons,
                "status": a.status,
                "cover_note": a.cover_note,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in apps
        ],
        "total": len(apps),
    }


# ============================================================
# 团队健康度评分（综合指标）
# ============================================================


@router.get("/team-health", response_model=Dict[str, Any])
async def team_health(
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """团队健康度综合评分（0-100）

    综合维度：
    - 评估得分趋势（来自 Evaluation）
    - 行动项完成率（来自 ActionItem）
    - 脉搏调研平均分（来自 PulseResponse）
    - 认可活跃度（来自 Recognition）
    """
    from models.talent_models import ActionItem, PulseResponse, Recognition
    from models.models import Evaluation
    from models.constants import EvaluationStatus

    tenant = _tenant()
    scores = {}

    # 1. 评估得分（最近 20 条已完成的平均分，归一化到 0-100）
    eval_result = await session.execute(
        select(Evaluation)
        .where(
            Evaluation.tenant_id == tenant,
            Evaluation.status == EvaluationStatus.COMPLETED,
        )
        .order_by(Evaluation.created_at.desc())
        .limit(20)
    )
    evals = eval_result.scalars().all()
    if evals:
        avg_eval = sum(e.overall_score for e in evals) / len(evals)
        scores["evaluation"] = round(avg_eval, 1)
    else:
        scores["evaluation"] = None

    # 2. 行动项完成率
    action_result = await session.execute(
        select(ActionItem).where(ActionItem.tenant_id == tenant)
    )
    actions = action_result.scalars().all()
    if actions:
        completed = sum(1 for a in actions if a.status == "completed")
        scores["action_completion"] = round(completed / len(actions) * 100, 1)
    else:
        scores["action_completion"] = None

    # 3. 脉搏调研平均分（1-5 → 0-100）
    pulse_result = await session.execute(
        select(PulseResponse).where(PulseResponse.tenant_id == tenant).limit(100)
    )
    pulses = pulse_result.scalars().all()
    if pulses:
        avg_pulse = sum(p.score for p in pulses) / len(pulses)
        scores["engagement"] = round(avg_pulse / 5 * 100, 1)
    else:
        scores["engagement"] = None

    # 4. 认可活跃度（最近 30 天的认可数，每 5 条 = 10 分，上限 100）
    rec_result = await session.execute(
        select(Recognition).where(Recognition.tenant_id == tenant).limit(200)
    )
    recs = rec_result.scalars().all()
    scores["recognition_activity"] = min(len(recs) * 10, 100)

    # 综合健康分（有值的维度取平均）
    valid_scores = [v for v in scores.values() if v is not None]
    overall = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0
    # 健康等级
    if overall >= 80:
        level = "excellent"
    elif overall >= 65:
        level = "good"
    elif overall >= 50:
        level = "attention"
    else:
        level = "risk"

    return {
        "overall_score": overall,
        "health_level": level,
        "dimensions": scores,
        "summary": {
            "total_evaluations": len(evals),
            "total_actions": len(actions),
            "total_pulse_responses": len(pulses),
            "total_recognitions": len(recs),
        },
    }


# ============================================================
# 多期趋势追踪
# ============================================================


@router.get("/trends/{employee_id}", response_model=Dict[str, Any])
async def employee_trend(
    employee_id: str,
    limit: int = 20,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """员工多期评估趋势"""
    from models.models import Evaluation
    from models.constants import EvaluationStatus

    result = await session.execute(
        select(Evaluation)
        .where(
            Evaluation.employee_id == employee_id,
            Evaluation.tenant_id == _tenant(),
            Evaluation.status == EvaluationStatus.COMPLETED,
        )
        .order_by(Evaluation.created_at.desc())
        .limit(min(limit, 100))
    )
    evals = result.scalars().all()
    evals.reverse()  # 按时间正序展示趋势
    trend_data = [
        {
            "evaluation_id": e.evaluation_id,
            "period": e.period,
            "overall_score": e.overall_score,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in evals
    ]
    # 计算趋势方向
    if len(trend_data) >= 2:
        first = trend_data[0]["overall_score"]
        last = trend_data[-1]["overall_score"]
        delta = round(last - first, 2)
        direction = (
            "improving" if delta > 2 else ("declining" if delta < -2 else "stable")
        )
    else:
        delta = 0
        direction = "insufficient-data"

    # 九宫格移动轨迹
    positions = []
    for e in evals:
        mv = e.manager_view or {}
        perf = mv.get("performance_level", "unknown")
        pot = mv.get("potential_level", "unknown")
        positions.append({"period": e.period, "performance": perf, "potential": pot})

    return {
        "employee_id": employee_id,
        "trend": trend_data,
        "score_delta": delta,
        "direction": direction,
        "matrix_positions": positions,
        "total_periods": len(trend_data),
    }


@router.get("/trends/team/overview", response_model=Dict[str, Any])
async def team_trend_overview(
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """团队多期评估趋势概览"""
    from models.models import Evaluation
    from models.constants import EvaluationStatus

    result = await session.execute(
        select(Evaluation)
        .where(
            Evaluation.tenant_id == _tenant(),
            Evaluation.status == EvaluationStatus.COMPLETED,
        )
        .order_by(Evaluation.created_at.desc())
        .limit(200)
    )
    evals = result.scalars().all()
    # 按周期聚合
    period_agg = {}
    for e in evals:
        period_agg.setdefault(e.period, []).append(e.overall_score)
    trend = [
        {
            "period": period,
            "avg_score": round(sum(scores) / len(scores), 2),
            "min_score": min(scores),
            "max_score": max(scores),
            "count": len(scores),
        }
        for period, scores in sorted(period_agg.items())
    ]
    return {
        "trend": trend,
        "total_evaluations": len(evals),
        "unique_employees": len(set(e.employee_id for e in evals)),
        "unique_periods": len(period_agg),
    }
