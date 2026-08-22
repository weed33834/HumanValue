"""M14 企业级治理模型 (MFA / 登录风控 / 公告 / 工单)"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.models import DEFAULT_TENANT_ID


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class UserMFA(Base):
    __tablename__ = "user_mfa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    secret: Mapped[str] = mapped_column(String(256), nullable=False)
    issuer: Mapped[str] = mapped_column(
        String(128), nullable=False, default="HumanValue"
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uix_mfa_tenant_user"),
        Index("ix_mfa_tenant_enabled", "tenant_id", "enabled"),
    )


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    user_agent: Mapped[str] = mapped_column(String(256), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, index=True
    )

    __table_args__ = (
        Index("ix_login_tenant_email_time", "tenant_id", "email", "created_at"),
        Index("ix_login_tenant_ip_time", "tenant_id", "ip_address", "created_at"),
    )


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )

    __table_args__ = (
        Index("ix_ann_tenant_active", "tenant_id", "active"),
        Index("ix_ann_tenant_pinned", "tenant_id", "pinned"),
    )


class AnnouncementRead(Base):
    __tablename__ = "announcement_reads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    announcement_id: Mapped[int] = mapped_column(
        ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    __table_args__ = (
        UniqueConstraint(
            "announcement_id", "user_id", "tenant_id", name="uix_ann_read"
        ),
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="general")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="open", index=True
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    assignee: Mapped[str] = mapped_column(String(64), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_ticket_tenant_status", "tenant_id", "status"),
        Index("ix_ticket_tenant_creator", "tenant_id", "created_by"),
    )


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
