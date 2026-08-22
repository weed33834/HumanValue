"""Reflector — Evaluator-Optimizer 反思器 (M3.9)

生成 → LLM-as-judge 评审 → 不达标带反馈重生成, 直至通过或达最大迭代。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent._json_util import call_llm_json, call_llm_text
from core.model_router import ModelRouter

logger = logging.getLogger(__name__)


@dataclass
class ReflectIteration:
    index: int
    output: str
    score: float = 0.0
    passed: bool = False
    feedback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "output": self.output,
            "score": self.score,
            "passed": self.passed,
            "feedback": self.feedback,
        }


class ReflectorAgent:
    def __init__(
        self,
        model_router: ModelRouter,
        max_iterations: int = 3,
        pass_score: float = 80.0,
    ):
        self.model_router = model_router
        self.max_iterations = max(max_iterations, 1)
        self.pass_score = pass_score

    async def generate(
        self,
        task: str,
        criteria: str,
        context: Optional[dict] = None,
        feedback: Optional[str] = None,
    ) -> str:
        user_parts = [f"任务: {task}", f"评价标准: {criteria}"]
        if context:
            user_parts.append(
                f"上下文: {json.dumps(context, ensure_ascii=False, default=str)[:2000]}"
            )
        if feedback:
            user_parts.append(f"上一轮评审意见（请据此改进）:\n{feedback}")
        return await call_llm_text(
            self.model_router,
            "你是任务执行者。根据任务要求生成高质量结果, 直接给出文本（不要 JSON 包裹）。",
            "\n\n".join(user_parts),
        )

    async def evaluate(
        self, task: str, criteria: str, output: str, context: Optional[dict] = None
    ) -> Dict[str, Any]:
        result = await call_llm_json(
            self.model_router,
            '你是严格的评审专家。依据标准给候选输出评分(0-100)并给改进意见。输出严格 JSON: {"score": <整数>, "passed": <bool>, "feedback": "<意见>"}',
            f"任务: {task}\n标准: {criteria}\n候选输出:\n{output[:8000]}",
        )
        if "_error" in result:
            return {"score": 0.0, "passed": False, "feedback": str(result)}
        try:
            score = float(result.get("score", 0))
        except (TypeError, ValueError):
            score = 0.0
        passed = bool(result.get("passed", score >= self.pass_score))
        return {
            "score": min(100.0, max(0.0, score)),
            "passed": passed,
            "feedback": result.get("feedback", ""),
        }

    async def reflect(
        self,
        task: str,
        criteria: str,
        context: Optional[dict] = None,
        initial_draft: Optional[str] = None,
    ) -> Dict[str, Any]:
        iterations: List[ReflectIteration] = []
        draft = initial_draft
        last_feedback: Optional[str] = None
        for i in range(1, self.max_iterations + 1):
            if draft is None or (i > 1 and last_feedback):
                draft = await self.generate(task, criteria, context, last_feedback)
            if not draft:
                logger.warning("reflect 第 %d 轮生成失败", i)
                break
            verdict = await self.evaluate(task, criteria, draft, context)
            rec = ReflectIteration(
                index=i,
                output=draft,
                score=verdict.get("score", 0.0),
                passed=verdict.get("passed", False),
                feedback=verdict.get("feedback", ""),
            )
            iterations.append(rec)
            if rec.passed:
                return {
                    "output": draft,
                    "passed": True,
                    "score": rec.score,
                    "iterations": [r.to_dict() for r in iterations],
                    "attempts": i,
                    "error": None,
                }
            last_feedback = verdict.get("feedback")
        best = iterations[-1] if iterations else None
        return {
            "output": best.output if best else "",
            "passed": False,
            "score": best.score if best else 0.0,
            "iterations": [r.to_dict() for r in iterations],
            "attempts": len(iterations),
            "error": "达到最大迭代次数仍未通过评审" if iterations else "未产生有效输出",
        }


def create_reflector_agent(
    model_router: ModelRouter, max_iterations: int = 3, pass_score: float = 80.0
) -> ReflectorAgent:
    return ReflectorAgent(
        model_router=model_router, max_iterations=max_iterations, pass_score=pass_score
    )
