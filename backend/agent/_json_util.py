"""共享 JSON / LLM 调用工具 (Planner / Reflector / A2A 复用)

实现已收口至 core/json_utils.py(全仓唯一), 本模块仅保留兼容别名,
旧导入路径 `from agent._json_util import ...` 继续有效。
"""

from core.json_utils import call_llm_json, call_llm_text, safe_json_dict

# 历史名称兼容: safe_json_parse 即 safe_json_dict
safe_json_parse = safe_json_dict

__all__ = ["call_llm_json", "call_llm_text", "safe_json_parse", "safe_json_dict"]
