"""M29 容灾与业务连续性 — 管理 API"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.deps import get_audit_service, get_db, get_dr_service
from auth.rbac import Role, get_current_user_id, require_role
from core.rate_limit import rate_limit
from services.audit_service import AuditService
from services.dr_service import DRService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/dr",
    tags=["admin-dr"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)


class BackupCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    scope: str = Field(default="database", max_length=32)
    backup_type: str = Field(default="full", max_length=32)


class RestoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_path: Optional[str] = Field(default=None, max_length=512)


class PlanCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    tier: int = Field(default=3, ge=1, le=6)
    rto_target_seconds: Optional[int] = None
    rpo_target_seconds: Optional[int] = None
    scenarios: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    contacts: List[Dict[str, Any]] = Field(default_factory=list)


class DrillCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    scenario: str = Field(default="restore", max_length=32)
    plan_id: Optional[int] = None


class DrillRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    measure_rto_seconds: int = Field(ge=0)
    measure_rpo_seconds: int = Field(ge=0)


@router.get("/metrics", response_model=Dict[str, Any])
async def continuity_metrics(dr: DRService = Depends(get_dr_service)):
    return await dr.metrics()


@router.get("/backups", response_model=Dict[str, Any])
async def list_backups(
    scope: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    dr: DRService = Depends(get_dr_service),
):
    return await dr.list_backup_sets(scope, page, page_size)


@router.post("/backups", response_model=Dict[str, Any], status_code=201)
@rate_limit("10/minute")
async def create_backup(
    request: Request,
    payload: BackupCreateRequest,
    dr: DRService = Depends(get_dr_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        bset = await dr.create_backup(payload.name, payload.scope, payload.backup_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    await audit_service.log(
        actor_id=current_user_id,
        action="create_backup",
        details={"backup_id": bset.id, "scope": bset.scope},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await dr.session.commit()
    return DRService._bset_dict(bset)


@router.post("/backups/{backup_id}/verify", response_model=Dict[str, Any])
async def verify_backup(backup_id: int, dr: DRService = Depends(get_dr_service)):
    bset = await dr.verify_backup(backup_id)
    if bset is None:
        raise HTTPException(status_code=404, detail="备份集不存在")
    return DRService._bset_dict(bset)


@router.post("/backups/{backup_id}/restore", response_model=Dict[str, Any])
@rate_limit("5/minute")
async def restore_backup(
    request: Request,
    backup_id: int,
    payload: RestoreRequest,
    dr: DRService = Depends(get_dr_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    result = await dr.restore_backup(backup_id, payload.target_path)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    await audit_service.log(
        actor_id=current_user_id,
        action="restore_backup",
        details={"backup_id": backup_id, "target": result.get("target")},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await dr.session.commit()
    return result


@router.get("/jobs", response_model=Dict[str, Any])
async def list_jobs(dr: DRService = Depends(get_dr_service)):
    return {"jobs": await dr.list_jobs()}


@router.get("/plans", response_model=Dict[str, Any])
async def list_plans(dr: DRService = Depends(get_dr_service)):
    return {"plans": await dr.list_plans()}


@router.post("/plans", response_model=Dict[str, Any], status_code=201)
async def create_plan(
    request: Request,
    payload: PlanCreateRequest,
    dr: DRService = Depends(get_dr_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    plan = await dr.create_plan(
        payload.name,
        payload.tier,
        payload.rto_target_seconds,
        payload.rpo_target_seconds,
        payload.scenarios,
        payload.steps,
        payload.contacts,
    )
    await audit_service.log(
        actor_id=current_user_id,
        action="create_dr_plan",
        details={"plan_id": plan.id, "name": plan.name},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await dr.session.commit()
    return DRService._plan_dict(plan)


@router.post("/plans/{plan_id}/publish", response_model=Dict[str, Any])
async def publish_plan(plan_id: int, dr: DRService = Depends(get_dr_service)):
    plan = await dr.publish_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="DR 计划不存在")
    return DRService._plan_dict(plan)


@router.get("/drills", response_model=Dict[str, Any])
async def list_drills(dr: DRService = Depends(get_dr_service)):
    return {"drills": await dr.list_drills()}


@router.post("/drills", response_model=Dict[str, Any], status_code=201)
async def create_drill(
    payload: DrillCreateRequest, dr: DRService = Depends(get_dr_service)
):
    d = await dr.create_drill(payload.name, payload.scenario, payload.plan_id)
    return {"id": d.id, "name": d.name, "scenario": d.scenario}


@router.post("/drills/{drill_id}/run", response_model=Dict[str, Any])
async def run_drill(
    request: Request,
    drill_id: int,
    payload: DrillRunRequest,
    dr: DRService = Depends(get_dr_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    d = await dr.run_drill(
        drill_id, payload.measure_rto_seconds, payload.measure_rpo_seconds
    )
    if d is None:
        raise HTTPException(status_code=404, detail="演练不存在")
    await audit_service.log(
        actor_id=current_user_id,
        action="run_drill",
        details={"drill_id": d.id, "result": d.result},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await dr.session.commit()
    return {
        "id": d.id,
        "result": d.result,
        "measured_rto_seconds": d.measured_rto_seconds,
        "measured_rpo_seconds": d.measured_rpo_seconds,
        "report": d.report,
    }
