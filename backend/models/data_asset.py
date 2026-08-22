"""M20 数据资产模型"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.models import DEFAULT_TENANT_ID

ASSET_TYPES = (
    "dataset",
    "eval_set",
    "knowledge_base",
    "chat_log",
    "trace",
    "metric",
    "prompt_asset",
    "document",
)
CLASSIFICATIONS = ("internal", "confidential", "sensitive", "public")
LIFECYCLE_STATES = ("collecting", "processing", "ready", "archived", "destroyed")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class DataAsset(Base):
    __tablename__ = "data_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    business_name: Mapped[str] = mapped_column(String(256), nullable=True)
    type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="dataset", index=True
    )
    source: Mapped[str] = mapped_column(String(128), nullable=True)
    owner: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    org: Mapped[str] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    classification: Mapped[str] = mapped_column(
        String(32), nullable=False, default="internal", index=True
    )
    tags: Mapped[list] = mapped_column(JSON, default=list)
    annotations: Mapped[dict] = mapped_column(JSON, default=dict)
    lineage: Mapped[dict] = mapped_column(JSON, default=dict)
    quality_score: Mapped[float] = mapped_column(default=0.0)
    usage_stats: Mapped[dict] = mapped_column(JSON, default=dict)
    lifecycle_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="collecting", index=True
    )
    sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TENANT_ID, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        Index("ix_asset_tenant_type", "tenant_id", "type"),
        Index("ix_asset_tenant_class", "tenant_id", "classification"),
        Index("ix_asset_tenant_state", "tenant_id", "lifecycle_state"),
    )
