"""M14 企业治理服务 (MFA / 登录风控 / 公告 / 工单)"""

from __future__ import annotations

import datetime
import logging
import uuid
from datetime import datetime as dt, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.field_crypto import get_field_cipher
from core.tenant_context import get_current_tenant
from models.enterprise_models import (
    Announcement,
    AnnouncementRead,
    LoginAttempt,
    Ticket,
    TicketComment,
    UserMFA,
)

logger = logging.getLogger(__name__)

try:
    import pyotp  # type: ignore

    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    pyotp = None  # type: ignore[assignment, misc]


def _now() -> dt:
    return dt.now(timezone.utc)


def _iso(value: Optional[dt]) -> Optional[str]:
    return value.isoformat() if value else None


class MFAService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def is_supported(self) -> bool:
        return PYOTP_AVAILABLE

    async def get_binding(
        self, user_id: str, tenant_id: Optional[str] = None
    ) -> Optional[UserMFA]:
        tenant = tenant_id or get_current_tenant()
        return (
            await self.session.execute(
                select(UserMFA).where(
                    UserMFA.tenant_id == tenant, UserMFA.user_id == user_id
                )
            )
        ).scalar_one_or_none()

    async def _decrypt(self, b: UserMFA) -> str:
        try:
            return get_field_cipher().decrypt(b.secret)
        except Exception:
            return b.secret

    async def enroll(self, user_id: str, issuer: str = "HumanValue") -> Dict[str, Any]:
        if not PYOTP_AVAILABLE:
            raise RuntimeError("pyotp 未安装，无法启用 MFA")
        secret = pyotp.random_base32()
        encrypted = get_field_cipher().encrypt(secret)
        existing = await self.get_binding(user_id)
        if existing is not None:
            existing.secret = encrypted
            existing.enabled = False
            existing.issuer = issuer
        else:
            self.session.add(
                UserMFA(
                    user_id=user_id,
                    tenant_id=get_current_tenant(),
                    secret=encrypted,
                    issuer=issuer,
                    enabled=False,
                )
            )
        await self.session.commit()
        totp = pyotp.TOTP(secret)
        return {
            "secret": secret,
            "otpauth_uri": totp.provisioning_uri(name=user_id, issuer_name=issuer),
            "enabled": False,
            "mfa_supported": True,
        }

    async def verify(self, user_id: str, otp: str, persist: bool = True) -> bool:
        if not PYOTP_AVAILABLE:
            return False
        binding = await self.get_binding(user_id)
        if binding is None:
            return False
        if not pyotp.TOTP(await self._decrypt(binding)).verify(otp, valid_window=1):
            return False
        if persist:
            binding.enabled = True
            binding.last_verified_at = _now()
            await self.session.commit()
        return True

    async def is_enabled(self, user_id: str, tenant_id: Optional[str] = None) -> bool:
        b = await self.get_binding(user_id, tenant_id)
        return b is not None and bool(b.enabled)

    async def disable(self, user_id: str) -> bool:
        b = await self.get_binding(user_id)
        if b is None:
            return False
        await self.session.delete(b)
        await self.session.commit()
        return True

    async def status(self, user_id: str) -> Dict[str, Any]:
        b = await self.get_binding(user_id)
        return {
            "mfa_enabled": b is not None and bool(b.enabled),
            "mfa_supported": PYOTP_AVAILABLE,
            "issuer": b.issuer if b else "HumanValue",
            "last_verified_at": _iso(b.last_verified_at) if b else None,
        }


class LoginGuardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def record_attempt(
        self,
        email,
        success,
        ip_address=None,
        user_agent=None,
        reason=None,
        tenant_id=None,
    ) -> LoginAttempt:
        a = LoginAttempt(
            email=(email or "").lower(),
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            reason=reason,
            tenant_id=tenant_id or get_current_tenant(),
        )
        self.session.add(a)
        return a

    def _window(self) -> dt:
        return _now() - datetime.timedelta(minutes=self.settings.login_lock_minutes)

    async def is_locked(self, email: str, ip_address: Optional[str] = None) -> bool:
        threshold = self.settings.login_lock_threshold
        if threshold <= 0:
            return False
        tenant = get_current_tenant()
        stmt = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.tenant_id == tenant,
                LoginAttempt.email == email.lower(),
                LoginAttempt.success.is_(False),
                LoginAttempt.created_at >= self._window(),
            )
        )
        if int((await self.session.execute(stmt)).scalar() or 0) >= threshold:
            return True
        if ip_address and self.settings.login_ip_lock_threshold > 0:
            stmt2 = (
                select(func.count())
                .select_from(LoginAttempt)
                .where(
                    LoginAttempt.tenant_id == tenant,
                    LoginAttempt.ip_address == ip_address,
                    LoginAttempt.success.is_(False),
                    LoginAttempt.created_at >= self._window(),
                )
            )
            if (
                int((await self.session.execute(stmt2)).scalar() or 0)
                >= self.settings.login_ip_lock_threshold
            ):
                return True
        return False

    async def lockout_status(
        self, email: str, ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        tenant = get_current_tenant()
        stmt = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.tenant_id == tenant,
                LoginAttempt.email == email.lower(),
                LoginAttempt.success.is_(False),
                LoginAttempt.created_at >= self._window(),
            )
        )
        failures = int((await self.session.execute(stmt)).scalar() or 0)
        return {
            "email": email.lower(),
            "recent_failures": failures,
            "threshold": self.settings.login_lock_threshold,
            "locked": failures >= self.settings.login_lock_threshold,
            "lock_minutes": self.settings.login_lock_minutes,
        }

    async def list_attempts(
        self, email=None, ip_address=None, success=None, page=1, page_size=20
    ) -> Dict[str, Any]:
        tenant = get_current_tenant()
        conditions = [LoginAttempt.tenant_id == tenant]
        if email:
            conditions.append(LoginAttempt.email == email.lower())
        if ip_address:
            conditions.append(LoginAttempt.ip_address == ip_address)
        if success is not None:
            conditions.append(LoginAttempt.success == success)
        base = select(LoginAttempt).where(and_(*conditions))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar()
            or 0
        )
        rows = (
            (
                await self.session.execute(
                    base.order_by(LoginAttempt.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "attempts": [
                {
                    "id": a.id,
                    "email": a.email,
                    "ip_address": a.ip_address,
                    "user_agent": a.user_agent,
                    "success": a.success,
                    "reason": a.reason,
                    "created_at": _iso(a.created_at),
                }
                for a in rows
            ],
        }

    async def list_locked(self, page=1, page_size=20) -> Dict[str, Any]:
        tenant = get_current_tenant()
        threshold = self.settings.login_lock_threshold
        if threshold <= 0:
            return {"total": 0, "locked": []}
        agg = (
            select(LoginAttempt.email, func.count().label("f"))
            .where(
                LoginAttempt.tenant_id == tenant,
                LoginAttempt.success.is_(False),
                LoginAttempt.created_at >= self._window(),
            )
            .group_by(LoginAttempt.email)
            .having(func.count() >= threshold)
            .order_by(func.count().desc())
        )
        rows = (await self.session.execute(agg)).all()
        locked = [{"email": r[0], "failures": r[1]} for r in rows]
        start = (page - 1) * page_size
        return {"total": len(locked), "locked": locked[start : start + page_size]}


class AnnouncementService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        title,
        content,
        level="info",
        pinned=False,
        expires_at=None,
        created_by=None,
    ) -> Announcement:
        a = Announcement(
            title=title,
            content=content,
            level=level,
            pinned=pinned,
            active=True,
            expires_at=expires_at,
            created_by=created_by,
            tenant_id=get_current_tenant(),
        )
        self.session.add(a)
        await self.session.commit()
        await self.session.refresh(a)
        return a

    async def list_active_for_user(
        self, user_id: str, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        tenant = tenant_id or get_current_tenant()
        now = _now()
        anns = (
            (
                await self.session.execute(
                    select(Announcement)
                    .where(
                        Announcement.tenant_id == tenant,
                        Announcement.active.is_(True),
                        or_(
                            Announcement.expires_at.is_(None),
                            Announcement.expires_at >= now,
                        ),
                    )
                    .order_by(
                        Announcement.pinned.desc(), Announcement.published_at.desc()
                    )
                )
            )
            .scalars()
            .all()
        )
        out = []
        for a in anns:
            rc = int(
                (
                    await self.session.execute(
                        select(func.count())
                        .select_from(AnnouncementRead)
                        .where(
                            AnnouncementRead.announcement_id == a.id,
                            AnnouncementRead.user_id == user_id,
                            AnnouncementRead.tenant_id == tenant,
                        )
                    )
                ).scalar()
                or 0
            )
            out.append(
                {
                    "id": a.id,
                    "title": a.title,
                    "content": a.content,
                    "level": a.level,
                    "pinned": a.pinned,
                    "published_at": _iso(a.published_at),
                    "expires_at": _iso(a.expires_at),
                    "read": rc > 0,
                }
            )
        return out

    async def unread_count(self, user_id: str) -> int:
        return sum(1 for a in await self.list_active_for_user(user_id) if not a["read"])

    async def mark_read(self, announcement_id: int, user_id: str) -> bool:
        tenant = get_current_tenant()
        ex = (
            await self.session.execute(
                select(AnnouncementRead).where(
                    AnnouncementRead.announcement_id == announcement_id,
                    AnnouncementRead.user_id == user_id,
                    AnnouncementRead.tenant_id == tenant,
                )
            )
        ).scalar_one_or_none()
        if ex is not None:
            return True
        self.session.add(
            AnnouncementRead(
                announcement_id=announcement_id, user_id=user_id, tenant_id=tenant
            )
        )
        await self.session.commit()
        return True

    async def list_all(self, active_only=False, page=1, page_size=20) -> Dict[str, Any]:
        tenant = get_current_tenant()
        conditions = [Announcement.tenant_id == tenant]
        if active_only:
            conditions.append(Announcement.active.is_(True))
        base = select(Announcement).where(and_(*conditions))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar()
            or 0
        )
        rows = (
            (
                await self.session.execute(
                    base.order_by(Announcement.published_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "announcements": [
                {
                    "id": a.id,
                    "title": a.title,
                    "content": a.content,
                    "level": a.level,
                    "pinned": a.pinned,
                    "active": a.active,
                    "published_at": _iso(a.published_at),
                    "expires_at": _iso(a.expires_at),
                    "created_by": a.created_by,
                }
                for a in rows
            ],
        }

    async def update(self, announcement_id: int, **fields) -> Optional[Announcement]:
        a = (
            await self.session.execute(
                select(Announcement).where(Announcement.id == announcement_id)
            )
        ).scalar_one_or_none()
        if a is None:
            return None
        for k, v in fields.items():
            if (
                k in {"title", "content", "level", "pinned", "active", "expires_at"}
                and v is not None
            ):
                setattr(a, k, v)
        await self.session.commit()
        await self.session.refresh(a)
        return a

    async def delete(self, announcement_id: int) -> bool:
        a = (
            await self.session.execute(
                select(Announcement).where(Announcement.id == announcement_id)
            )
        ).scalar_one_or_none()
        if a is None:
            return False
        await self.session.delete(a)
        await self.session.commit()
        return True


TICKET_STATUSES = {"open", "in_progress", "resolved", "closed"}
TICKET_TRANSITIONS = {
    "open": {"in_progress", "resolved", "closed"},
    "in_progress": {"resolved", "closed", "open"},
    "resolved": {"closed", "open"},
    "closed": {"open"},
}


class TicketService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, subject, description, created_by, category="general", priority="medium"
    ) -> Ticket:
        t = Ticket(
            ticket_id=f"TIC-{_now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}",
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            status="open",
            created_by=created_by,
            tenant_id=get_current_tenant(),
        )
        self.session.add(t)
        await self.session.commit()
        await self.session.refresh(t)
        return t

    async def list_my(
        self, user_id: str, status=None, page=1, page_size=20
    ) -> Dict[str, Any]:
        tenant = get_current_tenant()
        conditions = [Ticket.tenant_id == tenant, Ticket.created_by == user_id]
        if status:
            conditions.append(Ticket.status == status)
        base = select(Ticket).where(and_(*conditions))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar()
            or 0
        )
        rows = (
            (
                await self.session.execute(
                    base.order_by(Ticket.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "tickets": [self._to_dict(t) for t in rows],
        }

    async def list_all(
        self, status=None, category=None, assignee=None, page=1, page_size=20
    ) -> Dict[str, Any]:
        tenant = get_current_tenant()
        conditions = [Ticket.tenant_id == tenant]
        if status:
            conditions.append(Ticket.status == status)
        if category:
            conditions.append(Ticket.category == category)
        if assignee:
            conditions.append(Ticket.assignee == assignee)
        base = select(Ticket).where(and_(*conditions))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar()
            or 0
        )
        rows = (
            (
                await self.session.execute(
                    base.order_by(Ticket.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "tickets": [self._to_dict(t) for t in rows],
        }

    async def get(
        self, ticket_id: int, user_id: Optional[str] = None, is_admin: bool = False
    ) -> Optional[Ticket]:
        t = (
            await self.session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ).scalar_one_or_none()
        if t is None:
            return None
        if not is_admin and t.created_by != user_id:
            return None
        return t

    async def change_status(
        self, ticket_id: int, new_status: str, actor: str
    ) -> Dict[str, Any]:
        if new_status not in TICKET_STATUSES:
            raise ValueError(f"非法状态: {new_status}")
        t = (
            await self.session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ).scalar_one_or_none()
        if t is None:
            return {"error": "工单不存在"}
        if new_status not in TICKET_TRANSITIONS.get(t.status, set()):
            return {"error": f"非法状态流转: {t.status} → {new_status}"}
        t.status = new_status
        t.resolved_at = _now() if new_status in ("resolved", "closed") else None
        await self.session.commit()
        return {"status": new_status, "ticket_id": t.id}

    async def assign(self, ticket_id: int, assignee: str) -> Optional[Ticket]:
        t = (
            await self.session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ).scalar_one_or_none()
        if t is None:
            return None
        t.assignee = assignee
        if t.status == "open":
            t.status = "in_progress"
        await self.session.commit()
        await self.session.refresh(t)
        return t

    async def add_comment(
        self, ticket_id: int, author: str, content: str, internal: bool = False
    ) -> Optional[TicketComment]:
        t = (
            await self.session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ).scalar_one_or_none()
        if t is None:
            return None
        c = TicketComment(
            ticket_id=ticket_id,
            author=author,
            content=content,
            internal=internal,
            tenant_id=get_current_tenant(),
        )
        self.session.add(c)
        await self.session.commit()
        await self.session.refresh(c)
        return c

    async def list_comments(
        self, ticket_id: int, is_admin: bool = False
    ) -> List[Dict[str, Any]]:
        stmt = select(TicketComment).where(TicketComment.ticket_id == ticket_id)
        if not is_admin:
            stmt = stmt.where(TicketComment.internal.is_(False))
        rows = (
            (await self.session.execute(stmt.order_by(TicketComment.created_at.asc())))
            .scalars()
            .all()
        )
        return [
            {
                "id": c.id,
                "author": c.author,
                "content": c.content,
                "internal": c.internal,
                "created_at": _iso(c.created_at),
            }
            for c in rows
        ]

    @staticmethod
    def _to_dict(t: Ticket) -> Dict[str, Any]:
        return {
            "id": t.id,
            "ticket_id": t.ticket_id,
            "subject": t.subject,
            "description": t.description,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "created_by": t.created_by,
            "assignee": t.assignee,
            "created_at": _iso(t.created_at),
            "updated_at": _iso(t.updated_at),
            "resolved_at": _iso(t.resolved_at),
        }
