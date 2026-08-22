"""共享 JSON / LLM 调用工具 (Planner / Reflector / A2A 复用)

容错解析 LLM 输出 + 统一 LLM 调用 helper。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from core.model_router import ModelRouter
from core.providers.base import ChatMessage

logger = logging.getLogger(__name__)


def safe_json_parse(content: Optional[str]) -> dict:
    """容错 JSON 解析: 去除 markdown 代码块 / 截取 JSON 片段。"""
    if not content:
        return {}
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        try:
            return json.loads(text[first : last + 1])
        except Exception:
            pass
    return {}


async def call_llm_json(
    model_router: ModelRouter,
    system_prompt: str,
    user_prompt: str = "",
    temperature: Optional[float] = None,
) -> dict:
    """统一 LLM 调用, 返回解析后的 JSON dict。失败返回 {"_error": ...}。"""
    try:
        provider, _tier = await model_router.get_provider_with_fallback()
    except Exception as e:
        logger.warning("model_router 获取 provider 失败: %s", e)
        return {"_error": f"provider unavailable: {e}"}
    messages: List[ChatMessage] = []
    if system_prompt:
        messages.append(ChatMessage(role="system", content=system_prompt))
    if user_prompt:
        messages.append(ChatMessage(role="user", content=user_prompt))
    try:
        completion = await provider.chat_completion(messages=messages)
        parsed = safe_json_parse(completion.content)
        if not parsed:
            return {"_raw": completion.content}
        return parsed
    except Exception as e:
        logger.warning("LLM 调用失败: %s", e)
        return {"_error": f"llm call failed: {e}"}


async def call_llm_text(
    model_router: ModelRouter,
    system_prompt: str,
    user_prompt: str = "",
    temperature: Optional[float] = None,
) -> str:
    """统一 LLM 调用, 返回原始文本。"""
    try:
        provider, _tier = await model_router.get_provider_with_fallback()
    except Exception as e:
        logger.warning("model_router 获取 provider 失败: %s", e)
        return ""
    messages: List[ChatMessage] = []
    if system_prompt:
        messages.append(ChatMessage(role="system", content=system_prompt))
    if user_prompt:
        messages.append(ChatMessage(role="user", content=user_prompt))
    try:
        completion = await provider.chat_completion(messages=messages)
        return completion.content or ""
    except Exception as e:
        logger.warning("LLM 调用失败: %s", e)
        return ""
