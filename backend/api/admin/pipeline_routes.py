"""M28 数据管道与集成 — 管理 API"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.deps import get_audit_service, get_pipeline_service
from auth.rbac import Role, get_current_user_id, require_role
from core.rate_limit import rate_limit
from services.audit_service import AuditService
from services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/pipeline",
    tags=["admin-pipeline"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)


class SourceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    source_type: str = Field(default="file", max_length=32)
    conn_config: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class PipelineCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    source_id: Optional[int] = None
    mode: str = Field(default="batch", max_length=32)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    schedule_cron: Optional[str] = None


class RuleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=128)
    rule_type: str = Field(min_length=1, max_length=32)
    config: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class RuleTestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sample: List[Dict[str, Any]] = Field(min_length=1, max_length=200)


@router.get("/sources", response_model=Dict[str, Any])
async def list_sources(pipeline: PipelineService = Depends(get_pipeline_service)):
    return {"sources": await pipeline.list_sources()}


@router.post("/sources", response_model=Dict[str, Any], status_code=201)
async def create_source(
    request: Request,
    payload: SourceCreateRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    try:
        src = await pipeline.create_source(
            payload.name, payload.source_type, payload.conn_config, payload.description
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    await audit_service.log(
        actor_id=current_user_id,
        action="create_data_source",
        details={"source_id": src.id, "name": src.name},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await pipeline.session.commit()
    return {"id": src.id, "name": src.name, "source_type": src.source_type}


@router.post("/sources/{source_id}/test", response_model=Dict[str, Any])
async def test_source(
    source_id: int, pipeline: PipelineService = Depends(get_pipeline_service)
):
    return await pipeline.test_source(source_id)


@router.delete("/sources/{source_id}", response_model=Dict[str, Any])
async def delete_source(
    source_id: int, pipeline: PipelineService = Depends(get_pipeline_service)
):
    ok = await pipeline.delete_source(source_id)
    if not ok:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return {"deleted": True}


@router.get("/pipelines", response_model=Dict[str, Any])
async def list_pipelines(pipeline: PipelineService = Depends(get_pipeline_service)):
    return {"pipelines": await pipeline.list_pipelines()}


@router.post("/pipelines", response_model=Dict[str, Any], status_code=201)
async def create_pipeline(
    payload: PipelineCreateRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
):
    p = await pipeline.create_pipeline(
        payload.name,
        payload.source_id,
        payload.mode,
        payload.steps,
        payload.schedule_cron,
    )
    return {"id": p.id, "name": p.name}


@router.post("/pipelines/{pipeline_id}/run", response_model=Dict[str, Any])
@rate_limit("20/minute")
async def run_pipeline(
    request: Request,
    pipeline_id: int,
    pipeline: PipelineService = Depends(get_pipeline_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user_id: str = Depends(get_current_user_id),
):
    result = await pipeline.run_pipeline(pipeline_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    await audit_service.log(
        actor_id=current_user_id,
        action="run_pipeline",
        details={"pipeline_id": pipeline_id, "rows": result.get("rows_success")},
        ip_address=request.headers.get("x-forwarded-for"),
    )
    await pipeline.session.commit()
    return result


@router.get("/transform-rules", response_model=Dict[str, Any])
async def list_rules(pipeline: PipelineService = Depends(get_pipeline_service)):
    return {"rules": await pipeline.list_rules()}


@router.post("/transform-rules", response_model=Dict[str, Any], status_code=201)
async def create_rule(
    payload: RuleCreateRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
):
    try:
        r = await pipeline.create_rule(
            payload.name, payload.rule_type, payload.config, payload.description
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"id": r.id, "name": r.name, "rule_type": r.rule_type}


@router.post("/transform-rules/{rule_id}/test", response_model=Dict[str, Any])
async def test_rule(
    rule_id: int,
    payload: RuleTestRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
):
    return await pipeline.test_rule(rule_id, payload.sample)


@router.delete("/transform-rules/{rule_id}", response_model=Dict[str, Any])
async def delete_rule(
    rule_id: int, pipeline: PipelineService = Depends(get_pipeline_service)
):
    ok = await pipeline.delete_rule(rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="规则不存在")
    return {"deleted": True}


@router.get("/stats", response_model=Dict[str, Any])
async def sync_stats(pipeline: PipelineService = Depends(get_pipeline_service)):
    return await pipeline.sync_stats()


@router.get("/records", response_model=Dict[str, Any])
async def list_records(
    pipeline_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    pipeline: PipelineService = Depends(get_pipeline_service),
):
    return await pipeline.list_sync_records(pipeline_id, page, page_size)
