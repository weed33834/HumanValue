"""
人才管理核心路由 — 目标管理 / 行动项 / 个人发展计划 / 1:1 会议 / PIP 绩效改进

端点前缀: /api/v1/talent
权限: Boss / Manager / HR / Admin 可访问（Boss 全量，Manager 仅直属下属）
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from auth.rbac import Role, get_current_user_id, require_role
from core.database import get_db
from core.tenant_context import get_current_tenant
from models.talent_models import (
    ActionItem,
    DevelopmentPlan,
    Goal,
    OneOnOneMeeting,
    PerformanceImprovementPlan,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/talent", tags=["talent-management"])

_MAX_TEXT = 5000


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def _tenant() -> str:
    return get_current_tenant() or "default"


# ============================================================
# Pydantic Schemas
# ============================================================


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    owner_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    description: Optional[str] = None
    goal_type: str = Field(default="individual", max_length=32)
    parent_goal_id: Optional[str] = None
    period: str = Field(min_length=1, max_length=32)
    key_results: List[Dict[str, Any]] = Field(default_factory=list, max_length=20)


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(default=None, max_length=256)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=32)
    progress: Optional[float] = Field(default=None, ge=0, le=100)
    key_results: Optional[List[Dict[str, Any]]] = Field(default=None, max_length=20)


class ActionItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: str = Field(min_length=1, max_length=64)
    evaluation_id: Optional[str] = None
    title: str = Field(min_length=1, max_length=256)
    description: Optional[str] = None
    category: str = Field(default="development", max_length=64)
    priority: str = Field(default="medium", max_length=16)
    due_date: Optional[datetime] = None


class ActionItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Optional[str] = Field(default=None, max_length=16)
    priority: Optional[str] = Field(default=None, max_length=16)
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class IDPCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: str = Field(min_length=1, max_length=64)
    evaluation_id: Optional[str] = None
    title: str = Field(min_length=1, max_length=256)
    development_goal: str = Field(min_length=1, max_length=5000)
    focus_areas: List[str] = Field(default_factory=list, max_length=20)
    timeline_start: Optional[datetime] = None
    timeline_end: Optional[datetime] = None
    milestones: List[Dict[str, Any]] = Field(default_factory=list, max_length=30)
    resources: List[Dict[str, Any]] = Field(default_factory=list, max_length=20)


class IDPUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = None
    development_goal: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    resources: Optional[List[Dict[str, Any]]] = None
    progress: Optional[float] = Field(default=None, ge=0, le=100)
    status: Optional[str] = None


class OneOnOneCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: str = Field(min_length=1, max_length=64)
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=240)
    agenda_items: List[Dict[str, Any]] = Field(default_factory=list, max_length=20)


class OneOnOneUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Optional[str] = None
    agenda_items: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    action_summary: Optional[str] = None
    meeting_date: Optional[datetime] = None


class PIPCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: str = Field(min_length=1, max_length=64)
    evaluation_id: Optional[str] = None
    reason: str = Field(min_length=1, max_length=5000)
    improvement_goals: List[Dict[str, Any]] = Field(default_factory=list, max_length=10)
    milestones: List[Dict[str, Any]] = Field(default_factory=list, max_length=20)
    start_date: datetime
    end_date: datetime
    review_frequency: str = Field(default="weekly", max_length=32)


class PIPUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Optional[str] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    outcome_notes: Optional[str] = None


# ============================================================
# 目标管理 (OKR)
# ============================================================


@router.post("/goals", response_model=Dict[str, Any])
async def create_goal(
    payload: GoalCreate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建目标"""
    goal = Goal(
        goal_id=_new_id("goal"),
        owner_id=payload.owner_id,
        title=payload.title,
        description=payload.description,
        goal_type=payload.goal_type,
        parent_goal_id=payload.parent_goal_id,
        period=payload.period,
        key_results=payload.key_results,
        tenant_id=_tenant(),
    )
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return {"goal_id": goal.goal_id, "status": "created"}


@router.get("/goals", response_model=Dict[str, Any])
async def list_goals(
    owner_id: Optional[str] = None,
    period: Optional[str] = None,
    goal_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询目标列表"""
    conditions = [Goal.tenant_id == _tenant()]
    if owner_id:
        conditions.append(Goal.owner_id == owner_id)
    if period:
        conditions.append(Goal.period == period)
    if goal_type:
        conditions.append(Goal.goal_type == goal_type)
    if status_filter:
        conditions.append(Goal.status == status_filter)
    result = await session.execute(
        select(Goal).where(and_(*conditions)).order_by(Goal.created_at.desc())
    )
    goals = result.scalars().all()
    return {
        "items": [
            {
                "goal_id": g.goal_id,
                "owner_id": g.owner_id,
                "title": g.title,
                "description": g.description,
                "goal_type": g.goal_type,
                "parent_goal_id": g.parent_goal_id,
                "period": g.period,
                "status": g.status,
                "progress": g.progress,
                "key_results": g.key_results,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in goals
        ],
        "total": len(goals),
    }


@router.get("/goals/{goal_id}", response_model=Dict[str, Any])
async def get_goal(
    goal_id: str,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """获取目标详情"""
    result = await session.execute(
        select(Goal).where(Goal.goal_id == goal_id, Goal.tenant_id == _tenant())
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标不存在")
    return {
        "goal_id": goal.goal_id,
        "owner_id": goal.owner_id,
        "title": goal.title,
        "description": goal.description,
        "goal_type": goal.goal_type,
        "parent_goal_id": goal.parent_goal_id,
        "period": goal.period,
        "status": goal.status,
        "progress": goal.progress,
        "key_results": goal.key_results,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
        "updated_at": goal.updated_at.isoformat() if goal.updated_at else None,
    }


@router.patch("/goals/{goal_id}", response_model=Dict[str, Any])
async def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """更新目标"""
    result = await session.execute(
        select(Goal).where(Goal.goal_id == goal_id, Goal.tenant_id == _tenant())
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(goal, k, v)
    await session.commit()
    return {"goal_id": goal_id, "status": "updated"}


@router.delete("/goals/{goal_id}", response_model=Dict[str, Any])
async def delete_goal(
    goal_id: str,
    role: Role = Depends(require_role(Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """删除目标"""
    result = await session.execute(
        select(Goal).where(Goal.goal_id == goal_id, Goal.tenant_id == _tenant())
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标不存在")
    await session.delete(goal)
    await session.commit()
    return {"goal_id": goal_id, "status": "deleted"}


# ============================================================
# 行动项追踪
# ============================================================


@router.post("/action-items", response_model=Dict[str, Any])
async def create_action_item(
    payload: ActionItemCreate,
    request: Request,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建行动项"""
    actor_id = await get_current_user_id(request)
    item = ActionItem(
        action_id=_new_id("act"),
        evaluation_id=payload.evaluation_id,
        employee_id=payload.employee_id,
        assigned_by=actor_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        due_date=payload.due_date,
        tenant_id=_tenant(),
    )
    session.add(item)
    await session.commit()
    return {"action_id": item.action_id, "status": "created"}


@router.get("/action-items", response_model=Dict[str, Any])
async def list_action_items(
    employee_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询行动项列表"""
    conditions = [ActionItem.tenant_id == _tenant()]
    if employee_id:
        conditions.append(ActionItem.employee_id == employee_id)
    if status_filter:
        conditions.append(ActionItem.status == status_filter)
    if category:
        conditions.append(ActionItem.category == category)
    result = await session.execute(
        select(ActionItem)
        .where(and_(*conditions))
        .order_by(ActionItem.created_at.desc())
    )
    items = result.scalars().all()
    return {
        "items": [
            {
                "action_id": a.action_id,
                "evaluation_id": a.evaluation_id,
                "employee_id": a.employee_id,
                "assigned_by": a.assigned_by,
                "title": a.title,
                "description": a.description,
                "category": a.category,
                "priority": a.priority,
                "status": a.status,
                "due_date": a.due_date.isoformat() if a.due_date else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                "notes": a.notes,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in items
        ],
        "total": len(items),
    }


@router.patch("/action-items/{action_id}", response_model=Dict[str, Any])
async def update_action_item(
    action_id: str,
    payload: ActionItemUpdate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """更新行动项状态"""
    result = await session.execute(
        select(ActionItem).where(
            ActionItem.action_id == action_id, ActionItem.tenant_id == _tenant()
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="行动项不存在"
        )
    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("status") == "completed" and not item.completed_at:
        update_data["completed_at"] = datetime.now(timezone.utc)
    for k, v in update_data.items():
        setattr(item, k, v)
    await session.commit()
    return {"action_id": action_id, "status": "updated"}


@router.delete("/action-items/{action_id}", response_model=Dict[str, Any])
async def delete_action_item(
    action_id: str,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """删除行动项"""
    result = await session.execute(
        select(ActionItem).where(
            ActionItem.action_id == action_id, ActionItem.tenant_id == _tenant()
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="行动项不存在"
        )
    await session.delete(item)
    await session.commit()
    return {"action_id": action_id, "status": "deleted"}


@router.get("/action-items/summary", response_model=Dict[str, Any])
async def action_items_summary(
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """行动项概览统计"""
    result = await session.execute(
        select(ActionItem).where(ActionItem.tenant_id == _tenant())
    )
    items = result.scalars().all()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    summary = {
        "total": len(items),
        "pending": sum(1 for i in items if i.status == "pending"),
        "in_progress": sum(1 for i in items if i.status == "in_progress"),
        "completed": sum(1 for i in items if i.status == "completed"),
        "overdue": sum(
            1
            for i in items
            if i.status != "completed"
            and i.due_date
            and i.due_date.replace(tzinfo=None) < now
        ),
    }
    summary["completion_rate"] = round(
        summary["completed"] / max(summary["total"], 1) * 100, 1
    )
    return summary


# ============================================================
# 个人发展计划 (IDP)
# ============================================================


@router.post("/idps", response_model=Dict[str, Any])
async def create_idp(
    payload: IDPCreate,
    request: Request,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建个人发展计划"""
    actor_id = await get_current_user_id(request)
    plan = DevelopmentPlan(
        plan_id=_new_id("idp"),
        employee_id=payload.employee_id,
        evaluation_id=payload.evaluation_id,
        title=payload.title,
        development_goal=payload.development_goal,
        focus_areas=payload.focus_areas,
        timeline_start=payload.timeline_start,
        timeline_end=payload.timeline_end,
        milestones=payload.milestones,
        resources=payload.resources,
        created_by=actor_id,
        tenant_id=_tenant(),
    )
    session.add(plan)
    await session.commit()
    return {"plan_id": plan.plan_id, "status": "created"}


@router.get("/idps", response_model=Dict[str, Any])
async def list_idps(
    employee_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询发展计划列表"""
    conditions = [DevelopmentPlan.tenant_id == _tenant()]
    if employee_id:
        conditions.append(DevelopmentPlan.employee_id == employee_id)
    if status_filter:
        conditions.append(DevelopmentPlan.status == status_filter)
    result = await session.execute(
        select(DevelopmentPlan)
        .where(and_(*conditions))
        .order_by(DevelopmentPlan.created_at.desc())
    )
    plans = result.scalars().all()
    return {
        "items": [
            {
                "plan_id": p.plan_id,
                "employee_id": p.employee_id,
                "evaluation_id": p.evaluation_id,
                "title": p.title,
                "development_goal": p.development_goal,
                "focus_areas": p.focus_areas,
                "timeline_start": (
                    p.timeline_start.isoformat() if p.timeline_start else None
                ),
                "timeline_end": p.timeline_end.isoformat() if p.timeline_end else None,
                "milestones": p.milestones,
                "resources": p.resources,
                "progress": p.progress,
                "status": p.status,
                "created_by": p.created_by,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in plans
        ],
        "total": len(plans),
    }


@router.get("/idps/{plan_id}", response_model=Dict[str, Any])
async def get_idp(
    plan_id: str,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """获取发展计划详情"""
    result = await session.execute(
        select(DevelopmentPlan).where(
            DevelopmentPlan.plan_id == plan_id, DevelopmentPlan.tenant_id == _tenant()
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="发展计划不存在"
        )
    return {
        "plan_id": plan.plan_id,
        "employee_id": plan.employee_id,
        "evaluation_id": plan.evaluation_id,
        "title": plan.title,
        "development_goal": plan.development_goal,
        "focus_areas": plan.focus_areas,
        "timeline_start": (
            plan.timeline_start.isoformat() if plan.timeline_start else None
        ),
        "timeline_end": plan.timeline_end.isoformat() if plan.timeline_end else None,
        "milestones": plan.milestones,
        "resources": plan.resources,
        "progress": plan.progress,
        "status": plan.status,
        "created_by": plan.created_by,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


@router.patch("/idps/{plan_id}", response_model=Dict[str, Any])
async def update_idp(
    plan_id: str,
    payload: IDPUpdate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """更新发展计划"""
    result = await session.execute(
        select(DevelopmentPlan).where(
            DevelopmentPlan.plan_id == plan_id, DevelopmentPlan.tenant_id == _tenant()
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="发展计划不存在"
        )
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(plan, k, v)
    await session.commit()
    return {"plan_id": plan_id, "status": "updated"}


# ============================================================
# 1:1 会议管理
# ============================================================


@router.post("/one-on-ones", response_model=Dict[str, Any])
async def create_one_on_one(
    payload: OneOnOneCreate,
    request: Request,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建 1:1 会议"""
    actor_id = await get_current_user_id(request)
    meeting = OneOnOneMeeting(
        meeting_id=_new_id("1on1"),
        manager_id=actor_id,
        employee_id=payload.employee_id,
        scheduled_at=payload.scheduled_at,
        duration_min=payload.duration_minutes,
        agenda=payload.agenda_items,
        tenant_id=_tenant(),
    )
    session.add(meeting)
    await session.commit()
    return {"meeting_id": meeting.meeting_id, "status": "created"}


@router.get("/one-on-ones", response_model=Dict[str, Any])
async def list_one_on_ones(
    employee_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询 1:1 会议列表"""
    conditions = [OneOnOneMeeting.tenant_id == _tenant()]
    if employee_id:
        conditions.append(OneOnOneMeeting.employee_id == employee_id)
    if status_filter:
        conditions.append(OneOnOneMeeting.status == status_filter)
    result = await session.execute(
        select(OneOnOneMeeting)
        .where(and_(*conditions))
        .order_by(OneOnOneMeeting.scheduled_at.desc())
        .limit(min(limit, 200))
    )
    meetings = result.scalars().all()
    return {
        "items": [
            {
                "meeting_id": m.meeting_id,
                "manager_id": m.manager_id,
                "employee_id": m.employee_id,
                "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
                "duration_minutes": m.duration_min,
                "status": m.status,
                "agenda_items": m.agenda,
                "notes": m.notes,
                "action_summary": m.action_items,
                "ai_suggested_topics": m.ai_suggested_topics,
                "meeting_date": m.meeting_date.isoformat() if m.meeting_date else None,
            }
            for m in meetings
        ],
        "total": len(meetings),
    }


@router.patch("/one-on-ones/{meeting_id}", response_model=Dict[str, Any])
async def update_one_on_one(
    meeting_id: str,
    payload: OneOnOneUpdate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """更新 1:1 会议（记录笔记、完成、添加行动项）"""
    result = await session.execute(
        select(OneOnOneMeeting).where(
            OneOnOneMeeting.meeting_id == meeting_id,
            OneOnOneMeeting.tenant_id == _tenant(),
        )
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在")
    update_data = payload.model_dump(exclude_unset=True)
    # 前端字段名 → DB 字段名映射
    field_map = {"agenda_items": "agenda", "action_summary": "action_items"}
    for k, v in update_data.items():
        db_field = field_map.get(k, k)
        setattr(meeting, db_field, v)
    await session.commit()
    return {"meeting_id": meeting_id, "status": "updated"}


# ============================================================
# PIP 绩效改进计划
# ============================================================


@router.post("/pips", response_model=Dict[str, Any])
async def create_pip(
    payload: PIPCreate,
    request: Request,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """创建绩效改进计划"""
    actor_id = await get_current_user_id(request)
    pip = PerformanceImprovementPlan(
        pip_id=_new_id("pip"),
        employee_id=payload.employee_id,
        manager_id=actor_id,
        evaluation_id=payload.evaluation_id,
        reason=payload.reason,
        improvement_goals=payload.improvement_goals,
        milestones=payload.milestones,
        start_date=payload.start_date,
        end_date=payload.end_date,
        review_frequency=payload.review_frequency,
        tenant_id=_tenant(),
    )
    session.add(pip)
    await session.commit()
    return {"pip_id": pip.pip_id, "status": "created"}


@router.get("/pips", response_model=Dict[str, Any])
async def list_pips(
    employee_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """查询 PIP 列表"""
    conditions = [PerformanceImprovementPlan.tenant_id == _tenant()]
    if employee_id:
        conditions.append(PerformanceImprovementPlan.employee_id == employee_id)
    if status_filter:
        conditions.append(PerformanceImprovementPlan.status == status_filter)
    result = await session.execute(
        select(PerformanceImprovementPlan)
        .where(and_(*conditions))
        .order_by(PerformanceImprovementPlan.created_at.desc())
    )
    pips = result.scalars().all()
    return {
        "items": [
            {
                "pip_id": p.pip_id,
                "employee_id": p.employee_id,
                "manager_id": p.manager_id,
                "evaluation_id": p.evaluation_id,
                "reason": p.reason,
                "improvement_goals": p.improvement_goals,
                "milestones": p.milestones,
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "end_date": p.end_date.isoformat() if p.end_date else None,
                "review_frequency": p.review_frequency,
                "status": p.status,
                "outcome_notes": p.outcome_notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pips
        ],
        "total": len(pips),
    }


@router.get("/pips/{pip_id}", response_model=Dict[str, Any])
async def get_pip(
    pip_id: str,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """获取 PIP 详情"""
    result = await session.execute(
        select(PerformanceImprovementPlan).where(
            PerformanceImprovementPlan.pip_id == pip_id,
            PerformanceImprovementPlan.tenant_id == _tenant(),
        )
    )
    pip = result.scalar_one_or_none()
    if not pip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PIP 不存在")
    return {
        "pip_id": pip.pip_id,
        "employee_id": pip.employee_id,
        "manager_id": pip.manager_id,
        "evaluation_id": pip.evaluation_id,
        "reason": pip.reason,
        "improvement_goals": pip.improvement_goals,
        "milestones": pip.milestones,
        "start_date": pip.start_date.isoformat() if pip.start_date else None,
        "end_date": pip.end_date.isoformat() if pip.end_date else None,
        "review_frequency": pip.review_frequency,
        "status": pip.status,
        "outcome_notes": pip.outcome_notes,
        "created_at": pip.created_at.isoformat() if pip.created_at else None,
        "updated_at": pip.updated_at.isoformat() if pip.updated_at else None,
    }


@router.patch("/pips/{pip_id}", response_model=Dict[str, Any])
async def update_pip(
    pip_id: str,
    payload: PIPUpdate,
    role: Role = Depends(require_role(Role.MANAGER, Role.HR, Role.ADMIN, Role.BOSS)),
    session: AsyncSession = Depends(get_db),
):
    """更新 PIP 状态、里程碑或结果"""
    result = await session.execute(
        select(PerformanceImprovementPlan).where(
            PerformanceImprovementPlan.pip_id == pip_id,
            PerformanceImprovementPlan.tenant_id == _tenant(),
        )
    )
    pip = result.scalar_one_or_none()
    if not pip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PIP 不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(pip, k, v)
    await session.commit()
    return {"pip_id": pip_id, "status": "updated"}
