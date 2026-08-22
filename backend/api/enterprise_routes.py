"""M14 企业治理 — 用户侧 API (MFA / 公告 / 工单)"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.deps import get_announcement_service, get_mfa_service, get_ticket_service
from auth.rbac import get_current_user_id
from core.rate_limit import rate_limit
from services.enterprise_service import AnnouncementService, MFAService, TicketService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["enterprise"])


class MFAEnrollRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    issuer: str = Field(default="HumanValue", max_length=128)


class MFAVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    otp: str = Field(min_length=6, max_length=16)


@router.post("/auth/mfa/enroll", response_model=Dict[str, Any])
async def mfa_enroll(
    payload: MFAEnrollRequest,
    mfa_service: MFAService = Depends(get_mfa_service),
    user_id: str = Depends(get_current_user_id),
):
    if not mfa_service.is_supported():
        raise HTTPException(
            status_code=501, detail="pyotp 未安装，MFA 不可用 (pip install pyotp)"
        )
    return await mfa_service.enroll(user_id, issuer=payload.issuer)


@router.post("/auth/mfa/verify", response_model=Dict[str, Any])
async def mfa_verify(
    payload: MFAVerifyRequest,
    mfa_service: MFAService = Depends(get_mfa_service),
    user_id: str = Depends(get_current_user_id),
):
    if not await mfa_service.verify(user_id, payload.otp, persist=True):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    return {"mfa_enabled": True}


@router.post("/auth/mfa/disable", response_model=Dict[str, Any])
async def mfa_disable(
    mfa_service: MFAService = Depends(get_mfa_service),
    user_id: str = Depends(get_current_user_id),
):
    await mfa_service.disable(user_id)
    return {"mfa_enabled": False}


@router.get("/auth/mfa/status", response_model=Dict[str, Any])
async def mfa_status(
    mfa_service: MFAService = Depends(get_mfa_service),
    user_id: str = Depends(get_current_user_id),
):
    return await mfa_service.status(user_id)


@router.get("/announcements", response_model=Dict[str, Any])
async def list_announcements(
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    user_id: str = Depends(get_current_user_id),
):
    return {"announcements": await announcement_service.list_active_for_user(user_id)}


@router.get("/announcements/unread-count", response_model=Dict[str, Any])
async def unread_announcements(
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    user_id: str = Depends(get_current_user_id),
):
    return {"unread_count": await announcement_service.unread_count(user_id)}


@router.post("/announcements/{announcement_id}/read", response_model=Dict[str, Any])
async def mark_announcement_read(
    announcement_id: int,
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    user_id: str = Depends(get_current_user_id),
):
    await announcement_service.mark_read(announcement_id, user_id)
    return {"read": True, "announcement_id": announcement_id}


class TicketCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(min_length=2, max_length=256)
    description: str = Field(min_length=5, max_length=8000)
    category: str = Field(default="general", max_length=32)
    priority: str = Field(default="medium", max_length=16)


class TicketCommentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=4000)


@router.post("/tickets", response_model=Dict[str, Any], status_code=201)
@rate_limit("20/minute")
async def create_ticket(
    request: Request,
    payload: TicketCreateRequest,
    ticket_service: TicketService = Depends(get_ticket_service),
    user_id: str = Depends(get_current_user_id),
):
    return TicketService._to_dict(
        await ticket_service.create(
            payload.subject,
            payload.description,
            user_id,
            payload.category,
            payload.priority,
        )
    )


@router.get("/tickets/me", response_model=Dict[str, Any])
async def my_tickets(
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    ticket_service: TicketService = Depends(get_ticket_service),
    user_id: str = Depends(get_current_user_id),
):
    return await ticket_service.list_my(user_id, status_filter, page, page_size)


@router.get("/tickets/{ticket_id}", response_model=Dict[str, Any])
async def get_ticket(
    ticket_id: int,
    ticket_service: TicketService = Depends(get_ticket_service),
    user_id: str = Depends(get_current_user_id),
):
    t = await ticket_service.get(ticket_id, user_id=user_id, is_admin=False)
    if t is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return TicketService._to_dict(t)


@router.post("/tickets/{ticket_id}/comments", response_model=Dict[str, Any])
async def add_ticket_comment(
    ticket_id: int,
    payload: TicketCommentRequest,
    ticket_service: TicketService = Depends(get_ticket_service),
    user_id: str = Depends(get_current_user_id),
):
    t = await ticket_service.get(ticket_id, user_id=user_id, is_admin=False)
    if t is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    c = await ticket_service.add_comment(ticket_id, user_id, payload.content)
    return {"comment_id": c.id, "created_at": c.created_at.isoformat()}


@router.get("/tickets/{ticket_id}/comments", response_model=Dict[str, Any])
async def list_ticket_comments(
    ticket_id: int,
    ticket_service: TicketService = Depends(get_ticket_service),
    user_id: str = Depends(get_current_user_id),
):
    t = await ticket_service.get(ticket_id, user_id=user_id, is_admin=False)
    if t is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return {"comments": await ticket_service.list_comments(ticket_id, is_admin=False)}
