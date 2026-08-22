"""A2A (Agent2Agent) 协议 — 客户端 (M6.15)

Agent Card 发现 + JSON-RPC 任务提交/查询/取消, 基于 httpx。
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class A2AError(Exception):
    pass


class A2AClient:
    def __init__(self, timeout: float = 30.0, headers: Optional[Dict[str, str]] = None):
        self.timeout = timeout
        self.headers = headers or {}

    async def discover(self, card_url: str) -> Dict[str, Any]:
        url = card_url.rstrip("/")
        if not url.endswith(".json"):
            url = url + "/.well-known/agent.json"
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers=self.headers
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            raise A2AError(f"Agent Card 发现失败 ({url}): {e}") from e

    async def _rpc(
        self, base_url: str, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = base_url.rstrip("/")
        if not url.endswith("/a2a"):
            url = url + "/a2a"
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers=self.headers
            ) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                body = resp.json()
        except Exception as e:
            raise A2AError(f"A2A RPC 失败 ({method} @ {url}): {e}") from e
        if "error" in body:
            raise A2AError(
                f"A2A 远程错误: {json.dumps(body['error'], ensure_ascii=False)}"
            )
        return body.get("result", body)

    async def send_task(
        self,
        base_url: str,
        task_message: str,
        task_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "task": {
                "taskId": task_id or str(uuid.uuid4()),
                "message": {"role": "user", "content": task_message},
            }
        }
        if context is not None:
            params["task"]["context"] = context
        if metadata is not None:
            params["task"]["metadata"] = metadata
        return await self._rpc(base_url, "tasks/send", params)

    async def get_task(self, base_url: str, task_id: str) -> Dict[str, Any]:
        return await self._rpc(base_url, "tasks/get", {"taskId": task_id})

    async def cancel_task(self, base_url: str, task_id: str) -> Dict[str, Any]:
        return await self._rpc(base_url, "tasks/cancel", {"taskId": task_id})

    async def run_task(
        self,
        base_url: str,
        task_message: str,
        context: Optional[Dict[str, Any]] = None,
        poll_interval: float = 0.5,
        max_wait: float = 120.0,
    ) -> Dict[str, Any]:
        import asyncio

        task = await self.send_task(base_url, task_message, context=context)
        task_id = task.get("taskId")
        if not task_id:
            raise A2AError("send_task 响应缺少 taskId")
        waited = 0.0
        terminal = {"completed", "failed", "canceled", "cancelled"}
        while waited < max_wait:
            if (task.get("status") or {}).get("state", "") in terminal:
                return task
            await asyncio.sleep(poll_interval)
            waited += poll_interval
            task = await self.get_task(base_url, task_id)
        raise A2AError(f"任务轮询超时 (>{max_wait}s)")
