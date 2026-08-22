"""会话分析看板 Admin API V2

路由前缀: /api/v1/admin/analytics-v2
权限: Role.ADMIN (router 级 dependencies)

对标 Langfuse Token 分析 / Dashboard，完整端点 (5 个):
- GET /token-trends    - Token 趋势（按 day/model/user/agent 分组）
- GET /latency-stats   - 延迟统计（P50/P95/P99）
- GET /error-rate      - 错误率统计
- GET /cost-breakdown  - 成本分解（按 model/user/agent 分组）
- GET /anomalies       - 异常用量检测（Z-score）
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.rbac import Role, require_role
from core.database import get_db
from core.tenant_context import get_current_tenant
from services.analytics_service_v2 import AnalyticsServiceV2

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/analytics-v2",
    tags=["admin-analytics-v2"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)

# 合法的分组维度
_TOKEN_GROUP_BY = {"day", "model", "user", "agent"}
_COST_GROUP_BY = {"model", "user", "agent"}

# ISO 时间解析已收口至 _common(全 admin 路由唯一实现), 以旧名导入保持调用点不变
from api.admin._common import parse_iso_datetime as _parse_datetime  # noqa: E402


@router.get("/token-trends", response_model=Dict[str, Any])
async def token_trends(
    session: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    start_date: str = Query(..., description="起始时间（ISO 8601）"),
    end_date: str = Query(..., description="结束时间（ISO 8601）"),
    group_by: str = Query(default="day", description="分组维度: day/model/user/agent"),
):
    """Token 趋势聚合统计"""
    if group_by not in _TOKEN_GROUP_BY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的 group_by: {group_by}, 可选: {sorted(_TOKEN_GROUP_BY)}",
        )
    start = _parse_datetime(start_date, "start_date")
    end = _parse_datetime(end_date, "end_date")
    service = AnalyticsServiceV2(session)
    return await service.get_token_trends(start, end, tenant_id, group_by=group_by)


@router.get("/latency-stats", response_model=Dict[str, Any])
async def latency_stats(
    session: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    start_date: str = Query(..., description="起始时间（ISO 8601）"),
    end_date: str = Query(..., description="结束时间（ISO 8601）"),
):
    """延迟分位统计（P50/P95/P99）"""
    start = _parse_datetime(start_date, "start_date")
    end = _parse_datetime(end_date, "end_date")
    service = AnalyticsServiceV2(session)
    return await service.get_latency_stats(start, end, tenant_id)


@router.get("/error-rate", response_model=Dict[str, Any])
async def error_rate(
    session: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    start_date: str = Query(..., description="起始时间（ISO 8601）"),
    end_date: str = Query(..., description="结束时间（ISO 8601）"),
):
    """错误率统计"""
    start = _parse_datetime(start_date, "start_date")
    end = _parse_datetime(end_date, "end_date")
    service = AnalyticsServiceV2(session)
    return await service.get_error_rate(start, end, tenant_id)


@router.get("/cost-breakdown", response_model=Dict[str, Any])
async def cost_breakdown(
    session: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
    start_date: str = Query(..., description="起始时间（ISO 8601）"),
    end_date: str = Query(..., description="结束时间（ISO 8601）"),
    group_by: str = Query(default="model", description="分组维度: model/user/agent"),
):
    """成本分解统计"""
    if group_by not in _COST_GROUP_BY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的 group_by: {group_by}, 可选: {sorted(_COST_GROUP_BY)}",
        )
    start = _parse_datetime(start_date, "start_date")
    end = _parse_datetime(end_date, "end_date")
    service = AnalyticsServiceV2(session)
    return await service.get_cost_breakdown(start, end, tenant_id, group_by=group_by)


@router.get("/anomalies", response_model=Dict[str, Any])
async def anomalies(
    session: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
):
    """异常用量检测（基于最近 7 天按天聚合 total_tokens 的 Z-score）"""
    service = AnalyticsServiceV2(session)
    return await service.detect_anomalies(tenant_id)
