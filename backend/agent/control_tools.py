"""Agent 控制工具 (Control Tools) — 让对话界面能完成程序调用与更改

把业务服务封装为 LangChain 工具，Agent(对话)通过 function-calling 即可：
- 查询人才价值分析 (九宫格/关键人/二八/人效/激励/薪酬/继任/倦怠/技能/复盘/体系类型)
- 运营操作: 公告(创建/列表) / 工单(创建/流转) / 数据资产 / 数据管道(运行/统计) /
  容灾(备份/指标) / 登录风控(锁定/解锁) / 安全态势
- 系统帮助: 我能做什么

安全: 由 settings.control_tools_enabled 控制 (默认开启); 每个工具自开 DB 会话并遵循租户隔离。
"""

from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def _load_control_tools() -> List[Any]:
    """构建控制工具列表 (LangChain @tool, 异步)。

    settings.control_tools_enabled=False 时返回空列表。
    """
    try:
        from core.config import get_settings

        if not bool(getattr(get_settings(), "control_tools_enabled", True)):
            logger.info("control_tools_enabled=false, 控制工具不可用")
            return []
    except Exception:
        pass

    try:
        from langchain_core.tools import tool
    except ImportError:
        logger.warning("langchain_core 未安装, 控制工具不可用")
        return []

    async def _run_with_session(fn):
        """开独立 DB 会话执行服务调用。"""
        from core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            return await fn(session)

    # ================= 人才价值分析 =================

    @tool
    async def talent_value_analysis(
        analysis: str, system_type: Optional[str] = None
    ) -> str:
        """查询人才价值分析 (老板/管理者视角)。

        Args:
            analysis: 分析类型, 可选 classification(九宫格) / critical(关键人) / pareto(二八集中度) /
                      efficiency(人效) / incentive(激励策略) / market(薪酬竞争力) / succession(继任梯队) /
                      burnout(倦怠预警) / skill(技能匹配) / strategy(季度复盘) / system(体系类型)
            system_type: 可选, 临时指定体系类型 (enterprise_elimination / academic_cultivation / 等), 空用默认
        """
        from services.talent_value_service import TalentValueService

        async def _do(session):
            svc = TalentValueService(session)
            if analysis == "system":
                data = await svc.system_types()
            elif analysis == "critical":
                data = await svc.critical_dependency()
            elif analysis == "pareto":
                data = await svc.pareto_concentration()
            elif analysis == "efficiency":
                data = await svc.team_efficiency()
            elif analysis == "incentive":
                data = await svc.incentive_recommendations()
            elif analysis == "market":
                data = await svc.market_competitiveness()
            elif analysis == "succession":
                data = await svc.succession_pipeline()
            elif analysis == "burnout":
                data = await svc.burnout_warning()
            elif analysis == "skill":
                data = await svc.skill_fit()
            elif analysis == "strategy":
                data = await svc.strategy_review()
            else:
                data = await svc.talent_classification()
            return json.dumps(data, ensure_ascii=False, default=str)[:4000]

        return await _run_with_session(_do)

    # ================= 公告 =================

    @tool
    async def create_announcement(
        title: str, content: str, level: str = "info", pinned: bool = False
    ) -> str:
        """创建平台公告 (全体用户可见)。

        Args:
            title: 公告标题
            content: 公告内容
            level: info / warning / important
            pinned: 是否置顶
        """
        from services.enterprise_service import AnnouncementService

        async def _do(session):
            svc = AnnouncementService(session)
            a = await svc.create(title, content, level, pinned, None, "agent")
            return f"已创建公告 #{a.id} 《{a.title}》"

        return await _run_with_session(_do)

    @tool
    async def list_announcements() -> str:
        """列出平台公告。"""
        from services.enterprise_service import AnnouncementService

        async def _do(session):
            svc = AnnouncementService(session)
            d = await svc.list_all()
            return json.dumps(d, ensure_ascii=False, default=str)[:3000]

        return await _run_with_session(_do)

    # ================= 工单 =================

    @tool
    async def create_ticket(
        subject: str,
        description: str,
        category: str = "general",
        priority: str = "medium",
    ) -> str:
        """提交支持工单。

        Args:
            subject: 工单标题
            description: 问题描述
            category: general / bug / access / billing / other
            priority: low / medium / high / urgent
        """
        from services.enterprise_service import TicketService

        async def _do(session):
            svc = TicketService(session)
            t = await svc.create(subject, description, "agent", category, priority)
            return f"已创建工单 {t.ticket_id} (状态: {t.status})"

        return await _run_with_session(_do)

    @tool
    async def change_ticket_status(ticket_id: int, status: str) -> str:
        """变更工单状态 (open / in_progress / resolved / closed)。

        Args:
            ticket_id: 工单数字 id
            status: 目标状态
        """
        from services.enterprise_service import TicketService

        async def _do(session):
            svc = TicketService(session)
            r = await svc.change_status(ticket_id, status, "agent")
            return json.dumps(r, ensure_ascii=False)

        return await _run_with_session(_do)

    # ================= 数据资产 =================

    @tool
    async def list_data_assets() -> str:
        """列出数据资产目录。"""
        from services.data_governance_service import DataGovernanceService

        async def _do(session):
            svc = DataGovernanceService(session)
            d = await svc.list_all(page_size=20)
            return json.dumps(d, ensure_ascii=False, default=str)[:3000]

        return await _run_with_session(_do)

    @tool
    async def data_asset_summary() -> str:
        """数据资产总览 (按类型/分类/状态)。"""
        from services.data_governance_service import DataGovernanceService

        async def _do(session):
            svc = DataGovernanceService(session)
            return json.dumps(await svc.summary(), ensure_ascii=False)

        return await _run_with_session(_do)

    # ================= 数据管道 =================

    @tool
    async def list_pipelines() -> str:
        """列出数据管道。"""
        from services.pipeline_service import PipelineService

        async def _do(session):
            svc = PipelineService(session)
            return json.dumps(
                {"pipelines": await svc.list_pipelines()},
                ensure_ascii=False,
                default=str,
            )[:3000]

        return await _run_with_session(_do)

    @tool
    async def run_pipeline(pipeline_id: int) -> str:
        """运行数据管道 (提取→转换→质量→统计)。

        Args:
            pipeline_id: 管道 id
        """
        from services.pipeline_service import PipelineService

        async def _do(session):
            svc = PipelineService(session)
            r = await svc.run_pipeline(pipeline_id)
            return json.dumps(r, ensure_ascii=False, default=str)[:3000]

        return await _run_with_session(_do)

    @tool
    async def pipeline_stats() -> str:
        """数据管道同步统计。"""
        from services.pipeline_service import PipelineService

        async def _do(session):
            svc = PipelineService(session)
            return json.dumps(await svc.sync_stats(), ensure_ascii=False, default=str)

        return await _run_with_session(_do)

    # ================= 容灾 =================

    @tool
    async def create_backup(scope: str = "database") -> str:
        """创建数据库备份。

        Args:
            scope: database / object_store
        """
        from services.dr_service import DRService

        async def _do(session):
            svc = DRService(session)
            b = await svc.create_backup("agent-备份", scope=scope)
            return f"备份完成 #{b.id} status={b.status} verify={b.verify_status}"

        return await _run_with_session(_do)

    @tool
    async def dr_metrics() -> str:
        """容灾连续性指标 (RTO/RPO/备份成功率/演练通过率)。"""
        from services.dr_service import DRService

        async def _do(session):
            svc = DRService(session)
            return json.dumps(await svc.metrics(), ensure_ascii=False)

        return await _run_with_session(_do)

    # ================= 登录风控 =================

    @tool
    async def login_lockouts() -> str:
        """当前被暴力破解锁定的账号列表。"""
        from services.enterprise_service import LoginGuardService

        async def _do(session):
            svc = LoginGuardService(session)
            return json.dumps(await svc.list_locked(), ensure_ascii=False, default=str)

        return await _run_with_session(_do)

    @tool
    async def unlock_account(email: str) -> str:
        """解除账号登录锁定。

        Args:
            email: 被锁定的邮箱
        """

        async def _do(session):
            from sqlalchemy import delete as sa_delete
            from models.enterprise_models import LoginAttempt
            from core.tenant_context import get_current_tenant

            stmt = sa_delete(LoginAttempt).where(
                LoginAttempt.tenant_id == get_current_tenant(),
                LoginAttempt.email == email.lower(),
                LoginAttempt.success.is_(False),
            )
            await session.execute(stmt)
            await session.commit()
            return f"已解锁 {email}"

        return await _run_with_session(_do)

    # ================= 安全态势 =================

    @tool
    async def security_overview() -> str:
        """AI 安全态势总览 (攻击事件/拦截率/类型分布)。"""
        from services.security_service import SecurityService

        async def _do(session):
            svc = SecurityService(session)
            return json.dumps(await svc.overview(), ensure_ascii=False)

        return await _run_with_session(_do)

    # ================= 系统帮助 =================

    @tool
    async def assistant_capabilities() -> str:
        """介绍 AI 助手能在对话中完成哪些操作 (能力清单)。"""
        return (
            "HumanValue AI 助手可在对话中完成:\n"
            "1. 人才价值分析: talent_value_analysis (九宫格/关键人/二八/人效/激励/薪酬/继任/倦怠/技能/复盘/体系类型)\n"
            "2. 运营管理: create_announcement(公告) / create_ticket(工单) / change_ticket_status\n"
            "3. 数据治理: list_data_assets / data_asset_summary\n"
            "4. 数据管道: list_pipelines / run_pipeline / pipeline_stats\n"
            "5. 容灾: create_backup / dr_metrics\n"
            "6. 安全: security_overview / login_lockouts / unlock_account\n"
            "7. 知识: 搜索知识库/员工历史/联网检索/文件与浏览器工具\n"
            "直接对我说需求即可, 例如: '分析一下关键人风险' / '创建一个公告: 明天维护' / '跑一下管道 1'"
        )

    return [
        talent_value_analysis,
        create_announcement,
        list_announcements,
        create_ticket,
        change_ticket_status,
        list_data_assets,
        data_asset_summary,
        list_pipelines,
        run_pipeline,
        pipeline_stats,
        create_backup,
        dr_metrics,
        login_lockouts,
        unlock_account,
        security_overview,
        assistant_capabilities,
    ]
