"""Planner — Plan-and-Execute 规划器 (M3.8)

Plan-and-Execute: 任务拆解为步骤 → 逐步执行 → 中途 replan。
复用 core.model_router + core.providers.base + agent._json_util。
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from agent._json_util import call_llm_json, call_llm_text
from agent.tool_registry import ToolRegistry
from core.model_router import ModelRouter

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    description: str = ""
    depends_on: List[str] = field(default_factory=list)
    mode: str = "auto"  # tool | llm | auto
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = field(default_factory=dict)
    output: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _normalize_steps(raw: Any) -> List[PlanStep]:
    """规范化为 PlanStep 列表, 并把序号依赖解析为真实 id。"""
    steps: List[PlanStep] = []
    if isinstance(raw, dict):
        raw = raw.get("steps") or raw.get("plan") or []
    if not isinstance(raw, list):
        return steps
    for item in raw:
        if isinstance(item, str):
            steps.append(PlanStep(description=item))
            continue
        if not isinstance(item, dict):
            continue
        mode = item.get("mode", "auto")
        if mode not in ("tool", "llm", "auto"):
            mode = "auto"
        steps.append(
            PlanStep(
                description=item.get("description", ""),
                depends_on=list(item.get("depends_on") or []),
                mode=mode,
                tool_name=item.get("tool_name"),
                tool_args=dict(item.get("tool_args") or {}),
            )
        )
    for idx, step in enumerate(steps):
        resolved: List[str] = []
        for dep in step.depends_on:
            dep_s = str(dep).strip()
            if dep_s in ("", "first"):
                continue
            try:
                ref = int(dep_s)
            except ValueError:
                if dep_s in {s.id for s in steps}:
                    resolved.append(dep_s)
                continue
            if 1 <= ref <= len(steps) and ref - 1 < idx:
                resolved.append(steps[ref - 1].id)
        step.depends_on = resolved
    return steps


class PlannerAgent:
    def __init__(
        self,
        model_router: ModelRouter,
        tool_registry: Optional[ToolRegistry] = None,
        max_steps: int = 8,
        max_replans: int = 2,
    ):
        self.model_router = model_router
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.max_replans = max_replans

    async def plan(self, task: str, context: Optional[dict] = None) -> List[PlanStep]:
        ctx = json.dumps(context or {}, ensure_ascii=False, default=str)[:2000]
        system_prompt = (
            "你是任务规划专家。请把用户给定的复杂任务拆解为有序的、可执行的步骤清单。\n"
            "规则:\n1. 每步描述明确、原子化\n2. 通过 depends_on 表达依赖 (填前一步序号, 首步留空)\n"
            "3. mode 取值 'tool'/'llm'/'auto'\n4. 需工具时给出 tool_name 与 tool_args\n"
            f"5. 步骤数尽量精简 (<= {self.max_steps})\n"
            '输出严格 JSON: {"steps": [{"description": "...", "depends_on": [], "mode": "auto", "tool_name": null, "tool_args": {}}]}'
        )
        result = await call_llm_json(
            self.model_router, system_prompt, f"任务: {task}\n上下文: {ctx}"
        )
        if "_error" in result or "_raw" in result:
            logger.warning("plan 解析失败: %s", result)
            return []
        return _normalize_steps(result.get("steps"))

    async def _execute_tool_step(self, step: PlanStep, context: dict) -> Optional[str]:
        if self.tool_registry is None:
            return None
        name = step.tool_name
        args = step.tool_args or {}
        if not name:
            names = await self._available_tool_names()
            if not names:
                return None
            picked = await call_llm_json(
                self.model_router,
                "你是工具调度器。从可用工具挑选最合适一个。可用工具: "
                + ", ".join(names),
                f"步骤: {step.description}",
            )
            name = picked.get("tool_name")
            args = picked.get("args") or {}
            if not name:
                return None
        result = await self.tool_registry.execute_tool(name, args)
        if result.get("error"):
            return f"[工具 {name} 失败] {result['error']}"
        return result.get("output")

    async def _available_tool_names(self) -> List[str]:
        if self.tool_registry is None:
            return []
        try:
            tools = await self.tool_registry.resolve()
            return [getattr(t, "name", "") for t in tools if getattr(t, "name", "")]
        except Exception:
            return []

    async def _execute_llm_step(self, step: PlanStep, task: str, context: dict) -> str:
        return await call_llm_text(
            self.model_router,
            "你是任务执行助手。完成下面这一步, 输出结构化结果文本。",
            f"原始任务: {task}\n当前步骤: {step.description}\n上下文: {json.dumps(context, ensure_ascii=False, default=str)[:2000]}",
        )

    async def execute(
        self, plan: List[PlanStep], task: str, context: Optional[dict] = None
    ) -> Dict[str, Any]:
        context = context or {}
        done: Dict[str, PlanStep] = {}
        for step in plan:
            deps_missing = [d for d in step.depends_on if d not in done]
            if deps_missing and deps_missing != ["first"]:
                step.error = f"依赖未满足: {deps_missing}"
                done[step.id] = step
                continue
            try:
                if step.mode == "tool":
                    out = await self._execute_tool_step(step, context)
                    step.output = out or step.error or "工具执行不可用"
                    if out is None:
                        step.error = "工具执行不可用"
                elif step.mode == "llm":
                    step.output = await self._execute_llm_step(step, task, context)
                else:
                    out = await self._execute_tool_step(step, context)
                    step.output = (
                        out
                        if out is not None
                        else await self._execute_llm_step(step, task, context)
                    )
            except Exception as e:
                logger.warning("执行步骤 %s 异常: %s", step.id, e)
                step.error = str(e)
            done[step.id] = step
        return {"steps": [s.to_dict() for s in plan]}

    async def replan(
        self,
        task: str,
        remaining: List[PlanStep],
        executed: List[PlanStep],
        context: Optional[dict] = None,
    ) -> List[PlanStep]:
        system_prompt = (
            "你是执行反思专家。部分步骤已执行。评估剩余步骤是否合理, 需要时调整。\n"
            '输出严格 JSON: {"keep": true, "revised_steps": [{"description": "...", "depends_on": [], "mode": "auto", "tool_name": null, "tool_args": {}}]}'
        )
        user_prompt = (
            f"任务: {task}\n已执行: {json.dumps([s.to_dict() for s in executed], ensure_ascii=False)}\n"
            f"剩余: {json.dumps([s.to_dict() for s in remaining], ensure_ascii=False)}"
        )
        result = await call_llm_json(self.model_router, system_prompt, user_prompt)
        if "_error" in result or "_raw" in result or result.get("keep") is True:
            return remaining
        revised = _normalize_steps(result.get("revised_steps"))
        return revised or remaining

    async def run(self, task: str, context: Optional[dict] = None) -> Dict[str, Any]:
        context = context or {}
        plan = await self.plan(task, context)
        if not plan:
            return {
                "plan": [],
                "results": {},
                "replans": 0,
                "final_answer": "",
                "error": "规划失败",
            }
        replans = 0
        cursor = 0
        executed_all: List[PlanStep] = []
        while cursor < len(plan):
            batch = plan[cursor : min(cursor + self.max_steps, len(plan))]
            result = await self.execute(batch, task, context)
            executed_all.extend(
                PlanStep(**s) for s in result["steps"] if s.get("output") is not None
            )
            cursor += len(batch)
            if cursor < len(plan) and replans < self.max_replans:
                revised = await self.replan(task, plan[cursor:], executed_all, context)
                replans += 1
                if revised != plan[cursor:]:
                    plan = plan[:cursor] + revised
        outputs = [f"[步骤 {s.id}] {s.output}" for s in plan if s.output]
        return {
            "plan": [s.to_dict() for s in plan],
            "results": {s.id: s.output for s in plan},
            "replans": replans,
            "final_answer": "\n\n".join(outputs),
            "error": None,
        }


def create_planner_agent(
    model_router: ModelRouter,
    tool_registry: Optional[ToolRegistry] = None,
    max_steps: int = 8,
    max_replans: int = 2,
) -> PlannerAgent:
    return PlannerAgent(
        model_router=model_router,
        tool_registry=tool_registry,
        max_steps=max_steps,
        max_replans=max_replans,
    )
