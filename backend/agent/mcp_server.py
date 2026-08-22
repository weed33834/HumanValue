"""MCP (Model Context Protocol) 服务器 (M4.17) — 把 agent 工具暴露为 MCP 服务器

内置轻量 JSON-RPC MCP 服务器 (不依赖外部 SDK) + 可选官方 FastMCP 包装。
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore

    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False
    FastMCP = None  # type: ignore[assignment, misc]


class MinimalMCPServer:
    """内置轻量 JSON-RPC MCP 服务器, 实现 initialize / tools/list / tools/call。"""

    PROTOCOL_VERSION = "2025-03-26"

    def __init__(
        self, server_name: str = "humanvalue-tools", tools: Optional[List[Any]] = None
    ):
        self.server_name = server_name
        self.tools = tools or []

    def _input_schema(self, tool: Any) -> Dict[str, Any]:
        args_schema = getattr(tool, "args_schema", None)
        schema: Dict[str, Any] = {"type": "object", "properties": {}}
        if args_schema is not None:
            try:
                schema = args_schema.model_json_schema()
            except Exception:
                pass
        return schema

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.server_name, "version": "1.0.0"},
                }
            elif method == "tools/list":
                result = {
                    "tools": [
                        {
                            "name": getattr(t, "name", ""),
                            "description": getattr(t, "description", "") or "",
                            "inputSchema": self._input_schema(t),
                        }
                        for t in self.tools
                        if getattr(t, "name", "")
                    ]
                }
            elif method == "tools/call":
                name = params.get("name")
                args = params.get("arguments") or {}
                tool = next(
                    (t for t in self.tools if getattr(t, "name", "") == name), None
                )
                if tool is None:
                    result = {
                        "isError": True,
                        "content": [
                            {"type": "text", "text": f"Tool '{name}' not found"}
                        ],
                    }
                else:
                    try:
                        out = await tool.ainvoke(args)
                        text = (
                            out
                            if isinstance(out, str)
                            else json.dumps(out, ensure_ascii=False, default=str)
                        )
                        result = {
                            "isError": False,
                            "content": [{"type": "text", "text": text}],
                        }
                    except Exception as e:
                        result = {
                            "isError": True,
                            "content": [{"type": "text", "text": f"Error: {e}"}],
                        }
            elif method in ("notifications/initialized", "initialized"):
                return (
                    {}
                    if req_id is None
                    else {"jsonrpc": "2.0", "id": req_id, "result": {"ok": True}}
                )
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as e:
            logger.exception("MCP 请求处理异常: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": f"Internal error: {e}"},
            }

    async def run_stdio(self) -> None:
        logger.info("MCP server '%s' 启动 (stdio)", self.server_name)
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                continue
            resp = await self.handle_request(req)
            if resp:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()


def build_fastmcp_server(
    server_name: str = "humanvalue-tools", tools: Optional[List[Any]] = None
):
    """用官方 FastMCP 包装 (需 `mcp` 包)。"""
    if not MCP_SDK_AVAILABLE or FastMCP is None:
        logger.warning("mcp SDK 未安装, 使用 MinimalMCPServer 替代")
        return None
    server = FastMCP(server_name)
    for t in tools or []:
        name = getattr(t, "name", None)
        if not name:
            continue

        @server.tool()
        async def _wrapped(tool=t, **kwargs: Any) -> str:
            result = await tool.ainvoke(kwargs)
            return (
                result
                if isinstance(result, str)
                else json.dumps(result, ensure_ascii=False, default=str)
            )

        try:
            _wrapped.name = name
            _wrapped.__name__ = name
        except Exception:
            pass
    return server


class MCPServerManager:
    """MCP 服务器管理器: 从 LangChain 工具构建, 提供列表 / 调用。"""

    def __init__(self, server_name: str = "humanvalue-tools"):
        self.server_name = server_name
        self._tools: List[Any] = []
        self._server = MinimalMCPServer(server_name=server_name)

    @property
    def sdk_available(self) -> bool:
        return MCP_SDK_AVAILABLE

    def set_tools(self, tools: List[Any]) -> None:
        self._tools = tools
        self._server.tools = tools

    def get_tool_names(self) -> List[str]:
        return [getattr(t, "name", "") for t in self._tools if getattr(t, "name", "")]

    def info(self) -> Dict[str, Any]:
        return {
            "server_name": self.server_name,
            "sdk_available": self.sdk_available,
            "transport": (
                "stdio (内置 JSON-RPC) / FastMCP"
                if self.sdk_available
                else "stdio (内置 JSON-RPC)"
            ),
            "tool_count": len(self._tools),
            "tool_names": self.get_tool_names(),
            "protocol_version": MinimalMCPServer.PROTOCOL_VERSION,
        }

    def minimal_server(self) -> MinimalMCPServer:
        return self._server

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self._server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        return resp.get("result", resp)


_global_mcp_server_manager: Optional[MCPServerManager] = None


def get_global_mcp_server_manager() -> MCPServerManager:
    global _global_mcp_server_manager
    if _global_mcp_server_manager is None:
        _global_mcp_server_manager = MCPServerManager()
    return _global_mcp_server_manager
