"""LLM 输出 JSON 容错解析 + 统一 LLM 调用 helper (全仓唯一实现)

此前同一容错解析逻辑在 agent/_json_util、agent/multi_agent、agent/skills、
services/graph_rag_service 等处存在 4+ 份拷贝,失败语义分裂(返回 {} / None),
且个别拷贝已出现能力退化。本模块为唯一权威实现,其余模块一律委托至此。

两种失败语义并存是有意设计:
- find_json_object: 解析失败返回 None——调用方需要区分"解析出的空对象"与"没解析出来"
- safe_json_dict:    失败/空输入统一返回 {}——调用方只关心拿不拿得到字段
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, List, Optional

from core.model_router import ModelRouter
from core.providers.base import ChatMessage

logger = logging.getLogger(__name__)


def _strip_code_fence(text: str) -> str:
    """剥离 markdown 代码块围栏

    兼容两种形态(与历史各处实现行为对齐并补齐单行场景):
    - 多行: ```json\\n{...}\\n```
    - 单行: ```json {...} ```
    """
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    # 单行围栏优先(正则整体匹配, 内容里不含连续 ``` 时最稳)
    inline = re.match(r"```[a-zA-Z]*\s*(.+?)\s*```$", stripped, re.DOTALL)
    if inline:
        return inline.group(1).strip()
    # 多行围栏: 去掉首行语言标记行与末尾围栏行
    lines = stripped.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def find_json_object(content: Optional[str]) -> Optional[Any]:
    """从容错解析中提取 JSON 值; 失败返回 None。

    解析顺序:
    1. 整段直接 json.loads(含围栏剥离后的纯文本)
    2. 截取第一个 { 到最后一个 } 的片段重试
    3. 截取第一个 [ 到最后一个 ] 的片段重试(兼容模型直接返回数组)

    注意: 合法解析出的空对象 {} 会原样返回,与 None(失败)可区分。
    """
    if not content:
        return None
    text = _strip_code_fence(content)
    for candidate in (text, *_slice_candidates(text)):
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    return None


def _slice_candidates(text: str) -> List[str]:
    """产出花括号/方括号截取候选(供 find_json_object 重试)"""
    candidates: List[str] = []
    first_obj, last_obj = text.find("{"), text.rfind("}")
    if first_obj >= 0 and last_obj > first_obj:
        candidates.append(text[first_obj : last_obj + 1])
    first_arr, last_arr = text.find("["), text.rfind("]")
    if first_arr >= 0 and last_arr > first_arr:
        candidates.append(text[first_arr : last_arr + 1])
    return candidates


def safe_json_dict(content: Optional[str]) -> dict:
    """容错 JSON 解析的 dict 版本: 失败/非 dict 一律返回 {}。

    兼容历史 safe_json_parse 语义; 若 LLM 返回顶层数组等非 dict 结构,
    同样返回 {}(需要数组的场景请用 find_json_object 自行处理)。
    """
    parsed = find_json_object(content)
    return parsed if isinstance(parsed, dict) else {}


# 兼容别名: agent 内部(planner/reflector/a2a)沿用旧名
safe_json_parse = safe_json_dict


async def call_llm_json(
    model_router: ModelRouter,
    system_prompt: str,
    user_prompt: str = "",
) -> dict:
    """统一 LLM 调用并解析 JSON, 失败返回 {"_error": ...} / {"_raw": ...}。

    - provider 获取失败或调用异常 → {"_error": "<msg>"}
    - 调用成功但解析不出 JSON   → {"_raw": <原文>}, 供调用方做文本回退
    """
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
        # 与历史实现保持逐字等价: 空 dict 视为解析失败回传原文
        # (已知边界: LLM 合法返回 "{}" 时会落入 _raw 分支,如需区分请用 find_json_object)
        parsed = safe_json_dict(completion.content)
        if not parsed:
            return {"_raw": completion.content or ""}
        return parsed
    except Exception as e:
        logger.warning("LLM 调用失败: %s", e)
        return {"_error": f"llm call failed: {e}"}


async def call_llm_text(
    model_router: ModelRouter,
    system_prompt: str,
    user_prompt: str = "",
) -> str:
    """统一 LLM 调用, 返回原始文本; 失败返回空串。"""
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
