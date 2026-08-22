"""A2A 公开端点 (M6.16) — Agent Card + JSON-RPC。"""

from __future__ import annotations

from fastapi import APIRouter

from agent.a2a_server import create_a2a_router

router = create_a2a_router(
    agent_name="HumanValue-Agent",
    agent_description="HumanValue 人才价值分析智能体。提供多步调研、综合分析、人才价值/成长/风险评估能力 (A2A)。",
    skills=[
        {"id": "research", "name": "research", "description": "多步调研与综合分析"},
        {
            "id": "talent-analysis",
            "name": "talent-analysis",
            "description": "人才价值/成长/风险评估",
        },
        {
            "id": "plan-execute",
            "name": "plan-execute",
            "description": "Plan-and-Execute 任务规划与执行",
        },
    ],
)
