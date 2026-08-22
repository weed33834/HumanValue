"""M29 容灾与业务连续性模型"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.models import DEFAULT_TENANT_ID

BACKUP_SCOPES = ("database", "object_store", "config", "model")
BACKUP_TYPES = ("full", "incremental", "differential")
BACKUP_SET_STATUSES = ("running", "completed", "failed", "verified", "verified_failed")
DRILL_SCENARIOS = ("failover", "restore", "data_loss", "region_down")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class BackupJob(Base):
    __tablename__ = "backup_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[str] = mapped_column(
        String(32), nullable=False, default="database", index=True
    )
    backup_type: Mapped[str] = mapped_column(String(32), nullable=False, default="full")
    schedule: Mapped[str] = mapped_column(String(64), nullable=True)
    retention_days: Mapped[int] = mapped_column(nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )


class BackupSet(Base):
    __tablename__ = "backup_sets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[str] = mapped_column(
        String(32), nullable=False, default="database", index=True
    )
    backup_type: Mapped[str] = mapped_column(String(32), nullable=False, default="full")
    location: Mapped[str] = mapped_column(String(256), nullable=False)
    size_bytes: Mapped[int] = mapped_column(default=0)
    checksum: Mapped[str] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="running", index=True
    )
    verify_status: Mapped[str] = mapped_column(String(32), nullable=True)
    restore_test_status: Mapped[str] = mapped_column(String(32), nullable=True)
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )


class DRPlan(Base):
    __tablename__ = "dr_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    tier: Mapped[int] = mapped_column(default=3)
    rto_target_seconds: Mapped[int] = mapped_column(default=300)
    rpo_target_seconds: Mapped[int] = mapped_column(default=300)
    scenarios: Mapped[list] = mapped_column(JSON, default=list)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    contacts: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft", index=True
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )


class Drill(Base):
    __tablename__ = "dr_drills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scenario: Mapped[str] = mapped_column(String(32), nullable=False, default="restore")
    plan_id: Mapped[int] = mapped_column(nullable=True, index=True)
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    result: Mapped[str] = mapped_column(String(32), nullable=True)
    measured_rto_seconds: Mapped[int] = mapped_column(nullable=True)
    measured_rpo_seconds: Mapped[int] = mapped_column(nullable=True)
    report: Mapped[dict] = mapped_column(JSON, default=dict)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )


class ContinuityMetric(Base):
    __tablename__ = "dr_continuity_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(nullable=False)
    target: Mapped[float] = mapped_column(nullable=True)
    period: Mapped[str] = mapped_column(String(32), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
