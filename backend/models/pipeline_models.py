"""M28 数据管道与集成模型"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.models import DEFAULT_TENANT_ID

SOURCE_TYPES = ("file", "api", "database", "kafka", "log")
PIPELINE_MODES = ("batch", "stream", "batch_stream")
RULE_TYPES = ("clean", "dedup", "mask", "normalize", "aggregate", "map")
SYNC_STATUSES = ("running", "success", "failed", "partial")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class DataSource(Base):
    __tablename__ = "pipeline_data_sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="file", index=True
    )
    conn_config: Mapped[dict] = mapped_column(JSON, default=dict)
    credentials_enc: Mapped[str] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="inactive", index=True
    )
    last_sync_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    description: Mapped[str] = mapped_column(String(512), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )


class Pipeline(Base):
    __tablename__ = "pipelines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="batch")
    source_id: Mapped[int] = mapped_column(nullable=True, index=True)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    schedule_cron: Mapped[str] = mapped_column(String(64), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run_id: Mapped[int] = mapped_column(nullable=True)
    last_run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
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


class TransformRule(Base):
    __tablename__ = "pipeline_transform_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )


class SyncRecord(Base):
    __tablename__ = "pipeline_sync_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pipeline_id: Mapped[int] = mapped_column(nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(nullable=True, index=True)
    batch_no: Mapped[str] = mapped_column(String(64), nullable=True)
    rows_total: Mapped[int] = mapped_column(default=0)
    rows_success: Mapped[int] = mapped_column(default=0)
    rows_failed: Mapped[int] = mapped_column(default=0)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="running", index=True
    )
    error: Mapped[str] = mapped_column(String(2048), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )


class DataQualityCheck(Base):
    __tablename__ = "pipeline_quality_checks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pipeline_id: Mapped[int] = mapped_column(nullable=False, index=True)
    sync_record_id: Mapped[int] = mapped_column(nullable=True)
    rule: Mapped[str] = mapped_column(String(256), nullable=False)
    threshold: Mapped[float] = mapped_column(default=0.0)
    actual: Mapped[float] = mapped_column(default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_level: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    message: Mapped[str] = mapped_column(String(1024), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
