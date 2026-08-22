"""M20 数据治理服务"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenant_context import get_current_tenant
from models.data_asset import CLASSIFICATIONS, DataAsset, LIFECYCLE_STATES

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _gen_asset_id(asset_type: str) -> str:
    return f"AST-{asset_type.upper().replace('_', '-')[:8]}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"


class DataGovernanceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(
        self,
        name,
        asset_type="dataset",
        business_name=None,
        source=None,
        owner=None,
        org=None,
        description=None,
        classification="internal",
        tags=None,
        lineage=None,
        sensitive=False,
        lifecycle_state="collecting",
    ) -> DataAsset:
        if classification not in CLASSIFICATIONS:
            raise ValueError(f"非法分类: {classification}")
        if lifecycle_state not in LIFECYCLE_STATES:
            raise ValueError(f"非法生命周期状态: {lifecycle_state}")
        a = DataAsset(
            asset_id=_gen_asset_id(asset_type),
            name=name,
            business_name=business_name or name,
            type=asset_type,
            source=source,
            owner=owner,
            org=org,
            description=description,
            classification=classification,
            tags=tags or [],
            lineage=lineage or {"upstream": [], "downstream": []},
            sensitive=sensitive,
            lifecycle_state=lifecycle_state,
            tenant_id=get_current_tenant(),
        )
        self.session.add(a)
        await self.session.commit()
        await self.session.refresh(a)
        return a

    async def get(self, asset_id: int) -> Optional[DataAsset]:
        return (
            await self.session.execute(
                select(DataAsset).where(
                    DataAsset.id == asset_id,
                    DataAsset.tenant_id == get_current_tenant(),
                )
            )
        ).scalar_one_or_none()

    async def update(self, asset_id: int, **fields) -> Optional[DataAsset]:
        a = await self.get(asset_id)
        if a is None:
            return None
        allowed = {
            "name",
            "business_name",
            "source",
            "owner",
            "org",
            "description",
            "classification",
            "tags",
            "annotations",
            "lineage",
            "quality_score",
            "lifecycle_state",
            "sensitive",
            "active",
        }
        for k, v in fields.items():
            if k in allowed and v is not None:
                if k == "classification" and v not in CLASSIFICATIONS:
                    raise ValueError(f"非法分类: {v}")
                if k == "lifecycle_state" and v not in LIFECYCLE_STATES:
                    raise ValueError(f"非法生命周期状态: {v}")
                setattr(a, k, v)
        await self.session.commit()
        await self.session.refresh(a)
        return a

    async def delete(self, asset_id: int) -> bool:
        a = await self.get(asset_id)
        if a is None:
            return False
        await self.session.delete(a)
        await self.session.commit()
        return True

    async def list_all(
        self,
        asset_type=None,
        classification=None,
        owner=None,
        lifecycle_state=None,
        keyword=None,
        page=1,
        page_size=20,
    ) -> Dict[str, Any]:
        tenant = get_current_tenant()
        conditions = [DataAsset.tenant_id == tenant]
        if asset_type:
            conditions.append(DataAsset.type == asset_type)
        if classification:
            conditions.append(DataAsset.classification == classification)
        if owner:
            conditions.append(DataAsset.owner == owner)
        if lifecycle_state:
            conditions.append(DataAsset.lifecycle_state == lifecycle_state)
        if keyword:
            like = f"%{keyword}%"
            conditions.append(
                or_(
                    DataAsset.name.ilike(like),
                    DataAsset.business_name.ilike(like),
                    DataAsset.description.ilike(like),
                )
            )
        base = select(DataAsset).where(and_(*conditions))
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
                    base.order_by(DataAsset.updated_at.desc())
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
            "assets": [self._to_dict(a) for a in rows],
        }

    async def record_usage(self, asset_id: int) -> Optional[DataAsset]:
        a = await self.get(asset_id)
        if a is None:
            return None
        stats = dict(a.usage_stats or {})
        stats["calls"] = int(stats.get("calls", 0)) + 1
        stats["last_accessed_at"] = _now().isoformat()
        a.usage_stats = stats
        await self.session.commit()
        await self.session.refresh(a)
        return a

    async def add_lineage(
        self, asset_id: int, direction: str, related: str
    ) -> Optional[DataAsset]:
        if direction not in ("upstream", "downstream"):
            raise ValueError("direction 必须为 upstream 或 downstream")
        a = await self.get(asset_id)
        if a is None:
            return None
        current = a.lineage or {}
        lineage = {
            "upstream": list(current.get("upstream") or []),
            "downstream": list(current.get("downstream") or []),
        }
        if related not in lineage[direction]:
            lineage[direction].append(related)
        a.lineage = lineage
        await self.session.commit()
        await self.session.refresh(a)
        return a

    async def summary(self) -> Dict[str, Any]:
        rows = (
            (
                await self.session.execute(
                    select(DataAsset).where(DataAsset.tenant_id == get_current_tenant())
                )
            )
            .scalars()
            .all()
        )
        result: Dict[str, Any] = {
            "total": len(rows),
            "by_type": {},
            "by_classification": {},
            "by_state": {},
        }
        for a in rows:
            result["by_type"][a.type] = result["by_type"].get(a.type, 0) + 1
            result["by_classification"][a.classification] = (
                result["by_classification"].get(a.classification, 0) + 1
            )
            result["by_state"][a.lifecycle_state] = (
                result["by_state"].get(a.lifecycle_state, 0) + 1
            )
        return result

    @staticmethod
    def _to_dict(a: DataAsset) -> Dict[str, Any]:
        return {
            "id": a.id,
            "asset_id": a.asset_id,
            "name": a.name,
            "business_name": a.business_name,
            "type": a.type,
            "source": a.source,
            "owner": a.owner,
            "org": a.org,
            "description": a.description,
            "classification": a.classification,
            "tags": a.tags or [],
            "lineage": a.lineage or {},
            "quality_score": a.quality_score,
            "usage_stats": a.usage_stats or {},
            "lifecycle_state": a.lifecycle_state,
            "sensitive": a.sensitive,
            "active": a.active,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
