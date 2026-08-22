"""M14 企业治理 — 管理侧 API (登录风控 / 公告 / 工单管理)"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.deps import (
    get_announcement_service,
    get_audit_service,
    get_login_guard_service,
    get_ticket_service,
)
from auth.rbac import Role, get_current_user_id, require_role
from core.rate_limit import rate_limit
from core.tenant_context import get_current_tenant
from services.audit_service import AuditService
from services.enterprise_service import (
    AnnouncementService,
    LoginGuardService,
    TicketService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/enterprise",
    tags=["admin-enterprise"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)


@router.get("/login-attempts", response_model=Dict[str, Any])
async def list_login_attempts(
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    success: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    login_guard: LoginGuardService = Depends(get_login_guard_service),
):
    return await login_guard.list_attempts(
        email=email,
        ip_address=ip_address,
        success=success,
        page=page,
        page_size=page_size,
    )


@router.get("/login-lockouts", response_model=Dict[str, Any])
async def list_login_lockouts(
    page: int = 1,
    page_size: int = 20,
    login_guard: LoginGuardService = Depends(get_login_guard_service),
):
    return await login_guard.list_locked(page=page, page_size=page_size)


@router.post("/unlock", response_model=Dict[str, Any])
async def unlock_email(
    payload: Dict[str, str],
    request: Request,
    login_guard: LoginGuardService = Depends(get_login_guard_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    email = (payload.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="email 必填")
    from sqlalchemy import delete as sa_delete
    from models.enterprise_models import LoginAttempt

    stmt = sa_delete(LoginAttempt).where(
        LoginAttempt.tenant_id == get_current_tenant(),
        LoginAttempt.email == email,
        LoginAttempt.success.is_(False),
    )
    await login_guard.session.execute(stmt)
    await login_guard.session.commit()
    await audit_service.log(
        actor_id=current_user_id,
        action="unlock_account",
        details={"email": email},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await login_guard.session.commit()
    return {"unlocked": True, "email": email}


class AnnouncementCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=256)
    content: str = Field(min_length=1)
    level: str = Field(default="info", max_length=16)
    pinned: bool = False
    expires_at: Optional[datetime] = None


class AnnouncementUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = None
    content: Optional[str] = None
    level: Optional[str] = None
    pinned: Optional[bool] = None
    active: Optional[bool] = None
    expires_at: Optional[datetime] = None


@router.get("/announcements", response_model=Dict[str, Any])
async def list_announcements(
    active_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    announcement_service: AnnouncementService = Depends(get_announcement_service),
):
    return await announcement_service.list_all(active_only, page, page_size)


@router.post("/announcements", response_model=Dict[str, Any], status_code=201)
@rate_limit("30/minute")
async def create_announcement(
    request: Request,
    payload: AnnouncementCreateRequest,
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    ann = await announcement_service.create(
        payload.title,
        payload.content,
        payload.level,
        payload.pinned,
        payload.expires_at,
        current_user_id,
    )
    await audit_service.log(
        actor_id=current_user_id,
        action="create_announcement",
        details={"announcement_id": ann.id, "title": ann.title},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await announcement_service.session.commit()
    return {"id": ann.id, "title": ann.title}


@router.put("/announcements/{announcement_id}", response_model=Dict[str, Any])
async def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdateRequest,
    request: Request,
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=422, detail="无更新字段")
    ann = await announcement_service.update(announcement_id, **fields)
    if ann is None:
        raise HTTPException(status_code=404, detail="公告不存在")
    await audit_service.log(
        actor_id=current_user_id,
        action="update_announcement",
        details={"announcement_id": ann.id, "changed": fields},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await announcement_service.session.commit()
    return {"id": ann.id, "updated": True}


@router.delete("/announcements/{announcement_id}", response_model=Dict[str, Any])
async def delete_announcement(
    announcement_id: int,
    request: Request,
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    ok = await announcement_service.delete(announcement_id)
    if not ok:
        raise HTTPException(status_code=404, detail="公告不存在")
    await audit_service.log(
        actor_id=current_user_id,
        action="delete_announcement",
        details={"announcement_id": announcement_id},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await announcement_service.session.commit()
    return {"deleted": True, "announcement_id": announcement_id}


class TicketStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(min_length=1, max_length=16)


class TicketAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assignee: str = Field(min_length=1, max_length=64)


class TicketInternalCommentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=4000)
    internal: bool = True


@router.get("/tickets", response_model=Dict[str, Any])
async def list_tickets(
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    assignee: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    ticket_service: TicketService = Depends(get_ticket_service),
):
    return await ticket_service.list_all(
        status=status_filter,
        category=category,
        assignee=assignee,
        page=page,
        page_size=page_size,
    )


@router.get("/tickets/{ticket_id}", response_model=Dict[str, Any])
async def get_ticket(
    ticket_id: int, ticket_service: TicketService = Depends(get_ticket_service)
):
    t = await ticket_service.get(ticket_id, is_admin=True)
    if t is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return {
        **TicketService._to_dict(t),
        "comments": await ticket_service.list_comments(ticket_id, is_admin=True),
    }


@router.put("/tickets/{ticket_id}/status", response_model=Dict[str, Any])
async def change_ticket_status(
    ticket_id: int,
    payload: TicketStatusRequest,
    request: Request,
    ticket_service: TicketService = Depends(get_ticket_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        result = await ticket_service.change_status(
            ticket_id, payload.status, current_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    await audit_service.log(
        actor_id=current_user_id,
        action="ticket_status_change",
        details={"ticket_id": ticket_id, "status": payload.status},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await ticket_service.session.commit()
    return result


@router.post("/tickets/{ticket_id}/assign", response_model=Dict[str, Any])
async def assign_ticket(
    ticket_id: int,
    payload: TicketAssignRequest,
    ticket_service: TicketService = Depends(get_ticket_service),
):
    t = await ticket_service.assign(ticket_id, payload.assignee)
    if t is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return {"ticket_id": t.id, "assignee": t.assignee, "status": t.status}


@router.post("/tickets/{ticket_id}/comments", response_model=Dict[str, Any])
async def add_internal_comment(
    ticket_id: int,
    payload: TicketInternalCommentRequest,
    ticket_service: TicketService = Depends(get_ticket_service),
    user_id: str = Depends(get_current_user_id),
):
    t = await ticket_service.get(ticket_id, is_admin=True)
    if t is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    c = await ticket_service.add_comment(
        ticket_id, user_id, payload.content, internal=payload.internal
    )
    return {"comment_id": c.id, "internal": c.internal}
