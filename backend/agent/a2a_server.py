"""A2A (Agent2Agent) 协议 — 服务器 (M6.16)

Agent Card + JSON-RPC 端点 (tasks/send/get/cancel/list)。
任务默认由 PlannerAgent 执行。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

_A2A_PROTOCOL_VERSION = "0.1.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStore:
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}

    def create(
        self, task_id: str, message: str, context: Optional[dict]
    ) -> Dict[str, Any]:
        task = {
            "taskId": task_id,
            "message": {"role": "user", "content": message},
            "context": context,
            "status": {"state": "working", "createdAt": _now_iso()},
            "artifacts": [],
            "messages": [],
        }
        self._tasks[task_id] = task
        return task

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def set_state(self, task_id: str, state: str) -> Optional[Dict[str, Any]]:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        task["status"] = {"state": state, "updatedAt": _now_iso()}
        return task

    def set_artifact(
        self, task_id: str, artifact: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        task.setdefault("artifacts", []).append(artifact)
        return task


async def _default_executor(task_text: str, context: Optional[dict]):
    from core.model_router import ModelRouter
    from agent.planner import create_planner_agent

    model_router = ModelRouter()
    planner = create_planner_agent(model_router)
    try:
        run_result = await planner.run(task_text, context)
        if run_result.get("final_answer"):
            return {"output": run_result["final_answer"]}
    except Exception:
        pass
    from agent._json_util import call_llm_text

    out = await call_llm_text(
        model_router, "你是 HumanValue 智能体, 请完成任务并给出清晰结果。", task_text
    )
    return {"output": out}


def create_a2a_router(
    agent_name: str = "HumanValue-Agent",
    agent_description: str = "HumanValue 人才价值分析智能体 (A2A 服务)",
    skills: Optional[list] = None,
    executor: Optional[Callable[[str, Optional[dict]], Any]] = None,
) -> APIRouter:
    router = APIRouter()
    store = TaskStore()
    skills = skills or [
        {"id": "research", "name": "research", "description": "多步调研与综合分析"},
        {
            "id": "talent-analysis",
            "name": "talent-analysis",
            "description": "人才价值/成长/风险评估",
        },
    ]

    async def _execute_and_store(
        task_id: str, text: str, context: Optional[dict]
    ) -> None:
        try:
            result = await (
                executor(text, context)
                if executor
                else _default_executor(text, context)
            )
        except Exception as e:
            logger.exception("A2A 任务 %s 执行失败", task_id)
            store.set_state(task_id, "failed")
            store.set_artifact(
                task_id,
                {
                    "name": "error",
                    "description": str(e),
                    "parts": [{"text": f"Task execution failed: {e}"}],
                },
            )
            return
        store.set_artifact(
            task_id,
            {
                "name": "output",
                "description": "最终结果",
                "parts": [{"text": result.get("output", str(result))}],
            },
        )
        store.set_state(task_id, "completed")

    @router.get("/.well-known/agent.json", include_in_schema=False)
    async def agent_card():
        return {
            "name": agent_name,
            "description": agent_description,
            "protocolVersion": _A2A_PROTOCOL_VERSION,
            "skills": skills,
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
                "stateTransitionHistory": True,
            },
            "url": "/a2a",
        }

    @router.post("/a2a")
    async def a2a_endpoint(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                },
            )
        req_id = body.get("id")
        method = body.get("method")
        params = body.get("params") or {}
        try:
            if method == "tasks/send":
                spec = params.get("task") or {}
                task_id = spec.get("taskId") or str(uuid.uuid4())
                message = (spec.get("message") or {}).get("content", "")
                context = spec.get("context")
                store.create(task_id, message, context)
                import asyncio

                asyncio.create_task(_execute_and_store(task_id, message, context))
                result = store.get(task_id)
            elif method == "tasks/get":
                task = store.get(params.get("taskId"))
                if task is None:
                    raise KeyError("task not found")
                result = task
            elif method == "tasks/cancel":
                task = store.set_state(params.get("taskId"), "canceled")
                if task is None:
                    raise KeyError("task not found")
                result = task
            elif method == "tasks/list":
                result = {"tasks": list(store._tasks.values())}
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}",
                        },
                    }
                )
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})
        except KeyError:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params"},
                }
            )
        except Exception as e:
            logger.exception("A2A %s 处理异常", method)
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)},
                }
            )

    return router
