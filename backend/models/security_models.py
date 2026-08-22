"""M25 AI 安全攻防与红队模型"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.models import DEFAULT_TENANT_ID

THREAT_TYPES = (
    "prompt_injection",
    "jailbreak",
    "data_poisoning",
    "model_extraction",
    "supply_chain",
    "agent_abuse",
)
SEVERITIES = ("low", "medium", "high", "critical")
VERDICTS = ("blocked", "flagged", "passed")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class ThreatCase(Base):
    __tablename__ = "security_threat_cases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    threat_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    attack_vector: Mapped[str] = mapped_column(String(256), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )


class SecurityEvent(Base):
    __tablename__ = "security_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    threat_case_id: Mapped[int] = mapped_column(nullable=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    verdict: Mapped[str] = mapped_column(
        String(16), nullable=False, default="flagged", index=True
    )
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    disposition: Mapped[str] = mapped_column(
        String(16), nullable=False, default="open", index=True
    )
    disposed_by: Mapped[str] = mapped_column(String(64), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )


class RedTeamRun(Base):
    __tablename__ = "security_redteam_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[str] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="running", index=True
    )
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    results: Mapped[list] = mapped_column(JSON, default=list)
    report_ref: Mapped[str] = mapped_column(String(256), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    finished_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
