"""人才价值引擎 API (老板/管理者视角)"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from auth.rbac import Role, require_role
from services.talent_value_service import TalentValueService

logger = logging.getLogger(__name__)

# 老板/管理者/HR/管理员可见
router = APIRouter(
    prefix="/api/v1/talent-value",
    tags=["talent-value"],
    dependencies=[Depends(require_role(Role.BOSS, Role.MANAGER, Role.HR, Role.ADMIN))],
)


async def _get_svc(session: AsyncSession = Depends(get_db)):
    return TalentValueService(session)


@router.get("/classification", response_model=Dict[str, Any])
async def talent_classification(svc: TalentValueService = Depends(_get_svc)):
    """全员九宫格分类 + 处置策略。"""
    return await svc.talent_classification()


@router.get("/critical-dependency", response_model=Dict[str, Any])
async def critical_dependency(svc: TalentValueService = Depends(_get_svc)):
    """单点依赖/关键人风险。"""
    return await svc.critical_dependency()


@router.get("/pareto", response_model=Dict[str, Any])
async def pareto(svc: TalentValueService = Depends(_get_svc)):
    """二八价值集中度。"""
    return await svc.pareto_concentration()


@router.get("/efficiency", response_model=Dict[str, Any])
async def efficiency(svc: TalentValueService = Depends(_get_svc)):
    """人效/团队价值密度。"""
    return await svc.team_efficiency()


@router.get("/incentives", response_model=Dict[str, Any])
async def incentives(svc: TalentValueService = Depends(_get_svc)):
    """激励策略推荐。"""
    return await svc.incentive_recommendations()


@router.get("/market-competitiveness", response_model=Dict[str, Any])
async def market_competitiveness(svc: TalentValueService = Depends(_get_svc)):
    """市场价值对标 / 薪酬竞争力。"""
    return await svc.market_competitiveness()


@router.get("/succession-pipeline", response_model=Dict[str, Any])
async def succession_pipeline(svc: TalentValueService = Depends(_get_svc)):
    """继任梯队 / 领导力管道。"""
    return await svc.succession_pipeline()


@router.get("/burnout-warning", response_model=Dict[str, Any])
async def burnout_warning(svc: TalentValueService = Depends(_get_svc)):
    """明星倦怠预警 / 负荷均衡。"""
    return await svc.burnout_warning()


@router.get("/skill-fit", response_model=Dict[str, Any])
async def skill_fit(svc: TalentValueService = Depends(_get_svc)):
    """技能 / 岗位匹配度与再配置。"""
    return await svc.skill_fit()


@router.get("/strategy-review", response_model=Dict[str, Any])
async def strategy_review(svc: TalentValueService = Depends(_get_svc)):
    """季度策略复盘 / 类别迁移与 PIP 成效。"""
    return await svc.strategy_review()


@router.get("/system-types", response_model=Dict[str, Any])
async def system_types(svc: TalentValueService = Depends(_get_svc)):
    """全部人才体系类型 (淘汰制/培养制/晋升制/认证制/灵活用工) 及其差异。"""
    return await svc.system_types()


@router.get("/insights", response_model=Dict[str, Any])
async def insights(svc: TalentValueService = Depends(_get_svc)):
    """当前体系类型的引擎洞察与策略预览。"""
    return await svc.insights()
