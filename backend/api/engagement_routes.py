"""
员工敬业度路由 — 脉搏调研 / 认可奖励 / 继任规划

端点前缀: /api/v1/engagement (脉搏+认可) + /api/v1/succession (继任)
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
    PulseResponse,
    PulseSurvey,
    Recognition,
    SuccessionPlan,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/engagement", tags=["engagement"])
succession_router = APIRouter(prefix="/api/v1/succession", tags=["succession"])


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def _tenant() -> str:
    return get_current_tenant() or "default"


# ============================================================
# Schemas
# ============================================================


class PulseSurveyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="", max_length=256)
    question: str = Field(min_length=1, max_length=2000)
    category: str = Field(default="engagement", max_length=64)
    period: str = Field(default="", max_length=32)
    scale_type: str = Field(default="1-5", max_length=16)
    frequency: str = Field(default="biweekly", max_length=16)


class PulseResponseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    survey_id: str = Field(min_length=1, max_length=128)
    score: float = Field(ge=0, le=10)
    comment: Optional[str] = None


class RecognitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_user_id: str = Field(min_length=1, max_length=64)
    recognition_type: str = Field(default="kudos", max_length=64)
    message: str = Field(min_length=1, max_length=5000)
    values_tags: List[str] = Field(default_factory=list, max_length=10)
    is_public: bool = True
    points: int = Field(default=0, ge=0, le=1000)


class SuccessionPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    position_title: str = Field(min_length=1, max_length=256)
    position_level: Optional[str] = None
    current_holder_id: Optional[str] = None
    candidate_id: str = Field(min_length=1, max_length=64)
    readiness: str = Field(default="1-2-years", max_length=32)
    development_gaps: List[Dict[str, Any]] = Field(default_factory=list, max_length=20)
    risk_notes: Optional[str] = None


class SuccessionPlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    readiness: Optional[str] = None
    development_gaps: Optional[List[Dict[str, Any]]] = None
    risk_notes: Optional[str] = None
    status: Optional[str] = None


# ============================================================
# 脉搏调研
# ============================================================


@router.post("/pulse/surveys", response_model=Dict[str, Any])
async def create_pulse_survey(
    payload: PulseSurveyCreate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建脉搏调研题"""
    survey = PulseSurvey(
        survey_id=_new_id("pulse"),
        title=payload.title,
        question=payload.question,
        period=payload.period,
        category=payload.category,
        scale_type=payload.scale_type,
        frequency=payload.frequency,
        tenant_id=_tenant(),
    )
    session.add(survey)
    await session.commit()
    return {"survey_id": survey.survey_id, "status": "created"}


@router.get("/pulse/surveys", response_model=Dict[str, Any])
async def list_pulse_surveys(
    active_only: bool = True,
    role: Role = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)
    ),
    session: AsyncSession = Depends(get_db),
):
    """查询脉搏调研题列表"""
    conditions = [PulseSurvey.tenant_id == _tenant()]
    if active_only:
        conditions.append(PulseSurvey.is_active.is_(True))
    result = await session.execute(
        select(PulseSurvey)
        .where(and_(*conditions))
        .order_by(PulseSurvey.created_at.desc())
    )
    surveys = result.scalars().all()
    return {
        "items": [
            {
                "survey_id": s.survey_id,
                "title": s.title,
                "question": s.question,
                "period": s.period,
                "category": s.category,
                "scale_type": s.scale_type,
                "frequency": s.frequency,
                "is_active": s.is_active,
            }
            for s in surveys
        ],
        "total": len(surveys),
    }


@router.post("/pulse/responses", response_model=Dict[str, Any])
async def submit_pulse_response(
    payload: PulseResponseCreate,
    request: Request,
    role: Role = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)
    ),
    session: AsyncSession = Depends(get_db),
):
    """提交脉搏调研回复"""
    actor_id = await get_current_user_id(request)
    # 简单情感分析：score >= 4 positive, 3 neutral, <=2 negative
    sentiment = (
        "positive"
        if payload.score >= 4
        else ("neutral" if payload.score >= 3 else "negative")
    )
    resp = PulseResponse(
        response_id=_new_id("pr"),
        survey_id=payload.survey_id,
        user_id=actor_id,
        score=payload.score,
        comment=payload.comment,
        sentiment=sentiment,
        tenant_id=_tenant(),
    )
    session.add(resp)
    await session.commit()
    return {
        "response_id": resp.response_id,
        "sentiment": sentiment,
        "status": "submitted",
    }


@router.get("/pulse/analytics", response_model=Dict[str, Any])
async def pulse_analytics(
    category: Optional[str] = None,
    limit: int = 100,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """脉搏调研趋势分析"""
    survey_conditions = [PulseSurvey.tenant_id == _tenant()]
    if category:
        survey_conditions.append(PulseSurvey.category == category)
    survey_result = await session.execute(
        select(PulseSurvey).where(and_(*survey_conditions))
    )
    surveys = survey_result.scalars().all()
    survey_ids = [s.survey_id for s in surveys]
    if not survey_ids:
        return {"items": [], "avg_score": None, "total_responses": 0}

    resp_result = await session.execute(
        select(PulseResponse)
        .where(
            PulseResponse.survey_id.in_(survey_ids),
            PulseResponse.tenant_id == _tenant(),
        )
        .order_by(PulseResponse.submitted_at.desc())
        .limit(min(limit, 500))
    )
    responses = resp_result.scalars().all()
    scores = [r.score for r in responses]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None
    sentiment_dist = {
        "positive": sum(1 for r in responses if r.sentiment == "positive"),
        "neutral": sum(1 for r in responses if r.sentiment == "neutral"),
        "negative": sum(1 for r in responses if r.sentiment == "negative"),
    }
    # 按天聚合趋势
    trend = {}
    for r in responses:
        day = r.submitted_at.strftime("%Y-%m-%d") if r.submitted_at else "unknown"
        trend.setdefault(day, []).append(r.score)
    trend_data = [
        {"date": day, "avg_score": round(sum(s) / len(s), 2), "count": len(s)}
        for day, s in sorted(trend.items())
    ]
    return {
        "avg_score": avg_score,
        "total_responses": len(responses),
        "sentiment_distribution": sentiment_dist,
        "trend": trend_data,
    }


# ============================================================
# 认可与奖励
# ============================================================


@router.post("/recognitions", response_model=Dict[str, Any])
async def create_recognition(
    payload: RecognitionCreate,
    request: Request,
    role: Role = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)
    ),
    session: AsyncSession = Depends(get_db),
):
    """发送认可"""
    actor_id = await get_current_user_id(request)
    rec = Recognition(
        recognition_id=_new_id("rec"),
        from_user_id=actor_id,
        to_user_id=payload.to_user_id,
        recognition_type=payload.recognition_type,
        message=payload.message,
        values_tags=payload.values_tags,
        is_public=payload.is_public,
        points=payload.points,
        tenant_id=_tenant(),
    )
    session.add(rec)
    await session.commit()
    return {"recognition_id": rec.recognition_id, "status": "created"}


@router.get("/recognizations", response_model=Dict[str, Any])
async def list_recognizations(
    to_user_id: Optional[str] = None,
    from_user_id: Optional[str] = None,
    limit: int = 50,
    role: Role = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)
    ),
    session: AsyncSession = Depends(get_db),
):
    """查询认可动态流"""
    conditions = [Recognition.tenant_id == _tenant(), Recognition.is_public.is_(True)]
    if to_user_id:
        conditions.append(Recognition.to_user_id == to_user_id)
    if from_user_id:
        conditions.append(Recognition.from_user_id == from_user_id)
    result = await session.execute(
        select(Recognition)
        .where(and_(*conditions))
        .order_by(Recognition.created_at.desc())
        .limit(min(limit, 200))
    )
    recs = result.scalars().all()
    return {
        "items": [
            {
                "recognition_id": r.recognition_id,
                "from_user_id": r.from_user_id,
                "to_user_id": r.to_user_id,
                "recognition_type": r.recognition_type,
                "message": r.message,
                "values_tags": r.values_tags,
                "points": r.points,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recs
        ],
        "total": len(recs),
    }


@router.get("/recognitions", response_model=Dict[str, Any])
async def list_recognitions(
    limit: int = 50,
    offset: int = 0,
    role: Role = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)
    ),
    session: AsyncSession = Depends(get_db),
):
    """认可列表"""
    from sqlalchemy import select, func

    result = await session.execute(
        select(Recognition)
        .where(Recognition.tenant_id == _tenant())
        .order_by(Recognition.created_at.desc())
        .offset(offset)
        .limit(min(limit, 200))
    )
    recs = result.scalars().all()
    return {
        "items": [
            {
                "recognition_id": r.recognition_id,
                "from_user_id": r.from_user_id,
                "to_user_id": r.to_user_id,
                "recognition_type": r.recognition_type,
                "message": r.message,
                "values_tags": r.values_tags,
                "is_public": r.is_public,
                "points": r.points,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recs
        ],
        "total": len(recs),
    }


@router.get("/recognitions/leaderboard", response_model=Dict[str, Any])
async def recognition_leaderboard(
    limit: int = 20,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """认可积分排行榜"""
    result = await session.execute(
        select(
            Recognition.to_user_id,
            func.sum(Recognition.points).label("total_points"),
            func.count(Recognition.id).label("recognition_count"),
        )
        .where(Recognition.tenant_id == _tenant())
        .group_by(Recognition.to_user_id)
        .order_by(func.sum(Recognition.points).desc())
        .limit(min(limit, 100))
    )
    rows = result.all()
    return {
        "items": [
            {
                "user_id": row.to_user_id,
                "total_points": row.total_points or 0,
                "recognition_count": row.recognition_count,
            }
            for row in rows
        ],
        "total": len(rows),
    }


# ============================================================
# 继任规划
# ============================================================


@succession_router.post("", response_model=Dict[str, Any])
async def create_succession_plan(
    payload: SuccessionPlanCreate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建继任计划"""
    plan = SuccessionPlan(
        plan_id=_new_id("succ"),
        position_title=payload.position_title,
        position_level=payload.position_level,
        current_holder_id=payload.current_holder_id,
        candidate_id=payload.candidate_id,
        readiness=payload.readiness,
        development_gaps=payload.development_gaps,
        risk_notes=payload.risk_notes,
        tenant_id=_tenant(),
    )
    session.add(plan)
    await session.commit()
    return {"plan_id": plan.plan_id, "status": "created"}


@succession_router.get("", response_model=Dict[str, Any])
async def list_succession_plans(
    position_title: Optional[str] = None,
    candidate_id: Optional[str] = None,
    readiness: Optional[str] = None,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询继任管线"""
    conditions = [SuccessionPlan.tenant_id == _tenant()]
    if position_title:
        conditions.append(SuccessionPlan.position_title == position_title)
    if candidate_id:
        conditions.append(SuccessionPlan.candidate_id == candidate_id)
    if readiness:
        conditions.append(SuccessionPlan.readiness == readiness)
    result = await session.execute(
        select(SuccessionPlan)
        .where(and_(*conditions))
        .order_by(SuccessionPlan.created_at.desc())
    )
    plans = result.scalars().all()
    return {
        "items": [
            {
                "plan_id": p.plan_id,
                "position_title": p.position_title,
                "position_level": p.position_level,
                "current_holder_id": p.current_holder_id,
                "candidate_id": p.candidate_id,
                "readiness": p.readiness,
                "development_gaps": p.development_gaps,
                "risk_notes": p.risk_notes,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in plans
        ],
        "total": len(plans),
    }


@succession_router.patch("/{plan_id}", response_model=Dict[str, Any])
async def update_succession_plan(
    plan_id: str,
    payload: SuccessionPlanUpdate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """更新继任计划"""
    result = await session.execute(
        select(SuccessionPlan).where(
            SuccessionPlan.plan_id == plan_id, SuccessionPlan.tenant_id == _tenant()
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="继任计划不存在"
        )
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(plan, k, v)
    await session.commit()
    return {"plan_id": plan_id, "status": "updated"}


@succession_router.get("/summary", response_model=Dict[str, Any])
async def succession_summary(
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """继任管线概览统计"""
    result = await session.execute(
        select(SuccessionPlan).where(
            SuccessionPlan.tenant_id == _tenant(), SuccessionPlan.status == "active"
        )
    )
    plans = result.scalars().all()
    positions = set(p.position_title for p in plans)
    readiness_dist = {
        "ready-now": sum(1 for p in plans if p.readiness == "ready-now"),
        "1-2-years": sum(1 for p in plans if p.readiness == "1-2-years"),
        "3-plus-years": sum(1 for p in plans if p.readiness == "3-plus-years"),
    }
    return {
        "total_positions": len(positions),
        "total_candidates": len(plans),
        "readiness_distribution": readiness_dist,
        "positions": list(positions),
    }
