"""M25 AI 安全攻防与红队 — 管理 API"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.deps import get_audit_service, get_security_service
from auth.rbac import Role, get_current_user_id, require_role
from core.rate_limit import rate_limit
from services.audit_service import AuditService
from services.security_service import SecurityService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/security",
    tags=["admin-security"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)


class ThreatCaseCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    threat_type: str = Field(min_length=1, max_length=32)
    payload: str = Field(min_length=1)
    severity: str = Field(default="medium", max_length=16)
    attack_vector: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RedTeamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    case_ids: Optional[List[int]] = None
    scope: Optional[str] = None


class DisposeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    disposition: str = Field(min_length=1, max_length=16)


@router.get("/overview", response_model=Dict[str, Any])
async def security_overview(security: SecurityService = Depends(get_security_service)):
    return await security.overview()


@router.post("/threat-cases/seed", response_model=Dict[str, Any])
async def seed_cases(security: SecurityService = Depends(get_security_service)):
    return {"inserted": await security.seed_default_cases()}


@router.get("/threat-cases", response_model=Dict[str, Any])
async def list_cases(
    threat_type: Optional[str] = None,
    severity: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    security: SecurityService = Depends(get_security_service),
):
    return await security.list_cases(threat_type, severity, keyword, page, page_size)


@router.post("/threat-cases", response_model=Dict[str, Any], status_code=201)
@rate_limit("30/minute")
async def create_case(
    request: Request,
    payload: ThreatCaseCreateRequest,
    security: SecurityService = Depends(get_security_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    case = await security.create_case(
        payload.name,
        payload.threat_type,
        payload.payload,
        payload.severity,
        payload.attack_vector,
        payload.tags,
    )
    await audit_service.log(
        actor_id=current_user_id,
        action="create_threat_case",
        details={"case_id": case.id, "name": case.name},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await security.session.commit()
    return {"id": case.id, "name": case.name, "threat_type": case.threat_type}


@router.delete("/threat-cases/{case_id}", response_model=Dict[str, Any])
async def delete_case(
    case_id: int, security: SecurityService = Depends(get_security_service)
):
    ok = await security.delete_case(case_id)
    if not ok:
        raise HTTPException(status_code=404, detail="威胁用例不存在")
    return {"deleted": True}


@router.get("/events", response_model=Dict[str, Any])
async def list_events(
    verdict: Optional[str] = None,
    event_type: Optional[str] = None,
    disposition: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    security: SecurityService = Depends(get_security_service),
):
    return await security.list_events(verdict, event_type, disposition, page, page_size)


@router.post("/events/{event_id}/dispose", response_model=Dict[str, Any])
async def dispose_event(
    event_id: int,
    payload: DisposeRequest,
    security: SecurityService = Depends(get_security_service),
    user_id: str = Depends(get_current_user_id),
):
    try:
        e = await security.dispose_event(event_id, payload.disposition, user_id)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
    if e is None:
        raise HTTPException(status_code=404, detail="安全事件不存在")
    return {"event_id": e.event_id, "disposition": e.disposition}


@router.get("/redteam/runs", response_model=Dict[str, Any])
async def list_redteam_runs(security: SecurityService = Depends(get_security_service)):
    return {"runs": await security.list_redteam_runs()}


@router.post("/redteam/run", response_model=Dict[str, Any])
@rate_limit("5/minute")
async def run_redteam(
    request: Request,
    payload: RedTeamRequest,
    security: SecurityService = Depends(get_security_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    result = await security.run_redteam(payload.name, payload.case_ids, payload.scope)
    await audit_service.log(
        actor_id=current_user_id,
        action="run_redteam",
        details={"run_id": result.get("run_id"), "summary": result.get("summary")},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await security.session.commit()
    return result
