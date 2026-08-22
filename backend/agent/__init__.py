"""Agent 核心模块包。

含 LangGraph 状态机、ReAct 循环、工具系统、多 Agent 协作，以及完整版能力：
- Planner (M3.8), Reflector (M3.9), MCP Server (M4.17), A2A (M6.15/16), Browser (M4.8)
"""

from agent.planner import PlannerAgent, create_planner_agent
from agent.reflector import ReflectorAgent, create_reflector_agent
from agent.mcp_server import (
    MCPServerManager,
    MinimalMCPServer,
    build_fastmcp_server,
    get_global_mcp_server_manager,
)
from agent.a2a_client import A2AClient, A2AError
from agent.a2a_server import create_a2a_router
from agent.browser_tool import (
    BrowserSession,
    build_browser_tools,
    close_browser_session,
    get_browser_session,
)

__all__ = [
    "PlannerAgent",
    "create_planner_agent",
    "ReflectorAgent",
    "create_reflector_agent",
    "MCPServerManager",
    "MinimalMCPServer",
    "build_fastmcp_server",
    "get_global_mcp_server_manager",
    "A2AClient",
    "A2AError",
    "create_a2a_router",
    "BrowserSession",
    "build_browser_tools",
    "get_browser_session",
    "close_browser_session",
]
