"""M20 数据治理 / M23 LLM 缓存 — 管理 API"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.deps import get_data_governance_service
from auth.rbac import Role, require_role
from core.rate_limit import rate_limit
from services.data_governance_service import DataGovernanceService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-data-governance"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)
cache_router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-llm-cache"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)


class AssetRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=256)
    type: str = Field(default="dataset", max_length=32)
    business_name: Optional[str] = None
    source: Optional[str] = None
    owner: Optional[str] = None
    org: Optional[str] = None
    description: Optional[str] = None
    classification: str = Field(default="internal", max_length=32)
    tags: List[str] = Field(default_factory=list)
    lineage: Optional[Dict[str, Any]] = None
    sensitive: bool = False
    lifecycle_state: str = Field(default="collecting", max_length=32)


class AssetUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = None
    business_name: Optional[str] = None
    source: Optional[str] = None
    owner: Optional[str] = None
    org: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[str] = None
    tags: Optional[List[str]] = None
    lineage: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None
    lifecycle_state: Optional[str] = None
    sensitive: Optional[bool] = None
    active: Optional[bool] = None


class LineageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    direction: str = Field(description="upstream | downstream")
    related: str = Field(min_length=1, max_length=256)


@router.get("/data-governance/summary", response_model=Dict[str, Any])
async def asset_summary(
    governance: DataGovernanceService = Depends(get_data_governance_service),
):
    return await governance.summary()


@router.get("/data-governance/assets", response_model=Dict[str, Any])
async def list_assets(
    asset_type: Optional[str] = None,
    classification: Optional[str] = None,
    owner: Optional[str] = None,
    lifecycle_state: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    governance: DataGovernanceService = Depends(get_data_governance_service),
):
    return await governance.list_all(
        asset_type=asset_type,
        classification=classification,
        owner=owner,
        lifecycle_state=lifecycle_state,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )


@router.post("/data-governance/assets", response_model=Dict[str, Any], status_code=201)
@rate_limit("60/minute")
async def register_asset(
    request: Request,
    payload: AssetRegisterRequest,
    governance: DataGovernanceService = Depends(get_data_governance_service),
):
    try:
        return DataGovernanceService._to_dict(
            await governance.register(
                payload.name,
                payload.type,
                payload.business_name,
                payload.source,
                payload.owner,
                payload.org,
                payload.description,
                payload.classification,
                payload.tags,
                payload.lineage,
                payload.sensitive,
                payload.lifecycle_state,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/data-governance/assets/{asset_id}", response_model=Dict[str, Any])
async def get_asset(
    asset_id: int,
    governance: DataGovernanceService = Depends(get_data_governance_service),
):
    a = await governance.get(asset_id)
    if a is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    return DataGovernanceService._to_dict(a)


@router.put("/data-governance/assets/{asset_id}", response_model=Dict[str, Any])
async def update_asset(
    asset_id: int,
    payload: AssetUpdateRequest,
    governance: DataGovernanceService = Depends(get_data_governance_service),
):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=422, detail="无更新字段")
    try:
        a = await governance.update(asset_id, **fields)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if a is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    return DataGovernanceService._to_dict(a)


@router.delete("/data-governance/assets/{asset_id}", response_model=Dict[str, Any])
async def delete_asset(
    asset_id: int,
    governance: DataGovernanceService = Depends(get_data_governance_service),
):
    ok = await governance.delete(asset_id)
    if not ok:
        raise HTTPException(status_code=404, detail="资产不存在")
    return {"deleted": True, "asset_id": asset_id}


@router.post(
    "/data-governance/assets/{asset_id}/lineage", response_model=Dict[str, Any]
)
async def add_lineage(
    asset_id: int,
    payload: LineageRequest,
    governance: DataGovernanceService = Depends(get_data_governance_service),
):
    try:
        a = await governance.add_lineage(asset_id, payload.direction, payload.related)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if a is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    return DataGovernanceService._to_dict(a)


@router.post("/data-governance/assets/{asset_id}/usage", response_model=Dict[str, Any])
async def record_usage(
    asset_id: int,
    governance: DataGovernanceService = Depends(get_data_governance_service),
):
    a = await governance.record_usage(asset_id)
    if a is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    return DataGovernanceService._to_dict(a)


@cache_router.get("/llm-cache/stats", response_model=Dict[str, Any])
async def llm_cache_stats():
    from core.llm_cache import get_global_llm_cache

    return await get_global_llm_cache().stats()


@cache_router.post("/llm-cache/clear", response_model=Dict[str, Any])
async def llm_cache_clear():
    from core.llm_cache import get_global_llm_cache

    return {"cleared": await get_global_llm_cache().clear()}


@cache_router.get("/llm-cache/config", response_model=Dict[str, Any])
async def llm_cache_config():
    from core.config import get_settings

    s = get_settings()
    return {
        "enabled": bool(getattr(s, "llm_cache_enabled", False)),
        "ttl_seconds": getattr(s, "llm_cache_ttl", 600),
        "max_size": getattr(s, "llm_cache_max_size", 1000),
        "similarity_threshold": getattr(s, "llm_cache_similarity_threshold", 0.95),
    }
