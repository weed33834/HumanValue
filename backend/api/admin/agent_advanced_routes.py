"""Agent 高级能力 Admin API — Planner / Reflector / MCP Server / Browser (M3.8/M3.9/M4.17/M4.8)"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.deps import get_app_state
from auth.rbac import Role, require_role
from core.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/agent-advanced",
    tags=["admin-agent-advanced"],
    dependencies=[Depends(require_role(Role.ADMIN))],
)


class PlannerRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task: str = Field(min_length=1, max_length=10000)
    context: Dict[str, Any] = Field(default_factory=dict)
    max_steps: int = Field(default=8, ge=1, le=20)
    max_replans: int = Field(default=2, ge=0, le=5)


class ReflectorRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task: str = Field(min_length=1, max_length=10000)
    criteria: str = Field(min_length=1, max_length=2000)
    context: Dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = Field(default=3, ge=1, le=8)
    pass_score: float = Field(default=80.0, ge=0.0, le=100.0)
    initial_draft: Optional[str] = None


class MCPToolCallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: str = Field(min_length=1, max_length=128)
    arguments: Dict[str, Any] = Field(default_factory=dict)


async def _resolve_app_tools(app_state) -> List[Any]:
    from agent.react_agent import build_all_tools

    return await build_all_tools(
        toolkit=getattr(app_state, "toolkit", None),
        settings=getattr(app_state, "settings", None),
    )


@router.post("/planner/run", response_model=Dict[str, Any])
@rate_limit("20/minute")
async def planner_run(
    request: Request, body: PlannerRunRequest, app_state=Depends(get_app_state)
):
    from agent.planner import create_planner_agent

    planner = create_planner_agent(
        model_router=app_state.model_router,
        tool_registry=app_state.tool_registry,
        max_steps=body.max_steps,
        max_replans=body.max_replans,
    )
    try:
        result = await planner.run(body.task, body.context)
        result["executor"] = "planner"
        return result
    except Exception as e:
        logger.exception("Planner run 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"Planner 执行失败: {e}")


@router.post("/planner/plan", response_model=Dict[str, Any])
@rate_limit("30/minute")
async def planner_plan_only(
    request: Request, body: PlannerRunRequest, app_state=Depends(get_app_state)
):
    from agent.planner import create_planner_agent

    planner = create_planner_agent(
        model_router=app_state.model_router,
        tool_registry=app_state.tool_registry,
        max_steps=body.max_steps,
        max_replans=body.max_replans,
    )
    try:
        steps = await planner.plan(body.task, body.context)
        return {"steps": [s.to_dict() for s in steps], "count": len(steps)}
    except Exception as e:
        logger.exception("Planner plan 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"规划失败: {e}")


@router.post("/reflector/run", response_model=Dict[str, Any])
@rate_limit("20/minute")
async def reflector_run(
    request: Request, body: ReflectorRunRequest, app_state=Depends(get_app_state)
):
    from agent.reflector import create_reflector_agent

    reflector = create_reflector_agent(
        model_router=app_state.model_router,
        max_iterations=body.max_iterations,
        pass_score=body.pass_score,
    )
    try:
        result = await reflector.reflect(
            body.task, body.criteria, body.context, body.initial_draft
        )
        result["executor"] = "reflector"
        return result
    except Exception as e:
        logger.exception("Reflector run 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"Reflector 执行失败: {e}")


@router.get("/mcp-server", response_model=Dict[str, Any])
async def mcp_server_info(app_state=Depends(get_app_state)):
    from agent.mcp_server import get_global_mcp_server_manager

    manager = get_global_mcp_server_manager()
    try:
        manager.set_tools(await _resolve_app_tools(app_state))
    except Exception as e:
        logger.warning("同步 MCP 工具集失败: %s", e)
    return manager.info()


@router.post("/mcp-server/call", response_model=Dict[str, Any])
@rate_limit("60/minute")
async def mcp_server_call(
    request: Request, body: MCPToolCallRequest, app_state=Depends(get_app_state)
):
    from agent.mcp_server import get_global_mcp_server_manager

    manager = get_global_mcp_server_manager()
    try:
        manager.set_tools(await _resolve_app_tools(app_state))
    except Exception as e:
        logger.warning("同步 MCP 工具集失败: %s", e)
    result = await manager.call_tool(body.tool_name, body.arguments)
    if result.get("isError"):
        raise HTTPException(status_code=400, detail=result)
    return result


@router.get("/browser/tools", response_model=Dict[str, Any])
async def browser_tools_info(app_state=Depends(get_app_state)):
    from agent.browser_tool import PLAYWRIGHT_AVAILABLE, build_browser_tools

    tools = build_browser_tools()
    return {
        "available": PLAYWRIGHT_AVAILABLE,
        "tool_count": len(tools),
        "tool_names": [getattr(t, "name", str(t)) for t in tools],
    }
