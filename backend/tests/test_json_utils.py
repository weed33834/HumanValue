"""core/json_utils 专项测试: 容错解析与统一 LLM 调用 helper"""

import asyncio

import pytest

from core.json_utils import (
    call_llm_json,
    call_llm_text,
    find_json_object,
    safe_json_dict,
)


# ---------------------------------------------------------------------------
# find_json_object
# ---------------------------------------------------------------------------


class TestFindJsonObject:
    def test_plain_object(self):
        assert find_json_object('{"a": 1}') == {"a": 1}

    def test_plain_array(self):
        assert find_json_object("[1, 2, 3]") == [1, 2, 3]

    @pytest.mark.parametrize(
        "fenced",
        [
            '```json\n{"a": 1}\n```',
            "```\n{'a': 1}\n```".replace("'", '"'),
            '```JSON\n{"a": 1}\n```',
            '```json {"a": 1} ```',
        ],
    )
    def test_fenced_code_block(self, fenced):
        assert find_json_object(fenced) == {"a": 1}

    def test_prefix_and_suffix_noise(self):
        text = '好的，以下是结果：\n{"score": 88, "reason": "ok"}\n希望有帮助'
        assert find_json_object(text) == {"score": 88, "reason": "ok"}

    def test_nested_braces(self):
        text = '前缀 {"outer": {"inner": [1, 2]}, "n": null} 后缀'
        assert find_json_object(text) == {"outer": {"inner": [1, 2]}, "n": None}

    def test_empty_object_is_valid_not_none(self):
        """合法的 {} 必须与失败(None)可区分"""
        assert find_json_object("{}") == {}

    def test_top_level_array_in_noise(self):
        text = '结果: ["x", "y"] 完'
        assert find_json_object(text) == ["x", "y"]

    def test_invalid_returns_none(self):
        assert find_json_object("这不是 JSON") is None
        assert find_json_object("{broken: <<<}") is None

    def test_empty_and_none_input(self):
        assert find_json_object("") is None
        assert find_json_object(None) is None
        assert find_json_object("   ") is None


# ---------------------------------------------------------------------------
# safe_json_dict
# ---------------------------------------------------------------------------


class TestSafeJsonDict:
    def test_valid_dict_passthrough(self):
        assert safe_json_dict('{"k": "v"}') == {"k": "v"}

    def test_failure_returns_empty_dict(self):
        assert safe_json_dict("nope") == {}
        assert safe_json_dict(None) == {}
        assert safe_json_dict("") == {}

    def test_non_dict_json_returns_empty_dict(self):
        """顶层数组等非 dict 结构按历史语义返回 {}"""
        assert safe_json_dict("[1,2]") == {}

    def test_legacy_alias_exists(self):
        from agent._json_util import safe_json_parse

        assert safe_json_parse is safe_json_dict
        assert safe_json_parse('{"a":1}') == {"a": 1}


# ---------------------------------------------------------------------------
# call_llm_json / call_llm_text
# ---------------------------------------------------------------------------


class _FakeCompletion:
    def __init__(self, content):
        self.content = content


class _FakeProvider:
    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error

    async def chat_completion(self, messages):
        if self._error:
            raise RuntimeError(self._error)
        return _FakeCompletion(self._content)


class _FakeRouter:
    def __init__(self, provider):
        self._provider = provider

    async def get_provider_with_fallback(self):
        return self._provider, "L0"


class TestCallLlmJson:
    def test_success_parses_json(self):
        router = _FakeRouter(_FakeProvider('{"answer": 42}'))
        result = asyncio.run(call_llm_json(router, "sys", "user"))
        assert result == {"answer": 42}

    def test_unparseable_returns_raw(self):
        router = _FakeRouter(_FakeProvider("纯文本回答"))
        result = asyncio.run(call_llm_json(router, "sys"))
        assert result["_raw"] == "纯文本回答"

    def test_provider_error_returns_error_key(self):
        router = _FakeRouter(_FakeProvider(error="boom"))
        result = asyncio.run(call_llm_json(router, "sys"))
        assert "_error" in result and "boom" in result["_error"]

    def test_router_failure_returns_error_key(self):
        class _BadRouter:
            async def get_provider_with_fallback(self):
                raise RuntimeError("no provider")

        result = asyncio.run(call_llm_json(_BadRouter(), "sys"))
        assert "_error" in result


class TestCallLlmText:
    def test_success_returns_text(self):
        router = _FakeRouter(_FakeProvider("hello"))
        assert asyncio.run(call_llm_text(router, "s", "u")) == "hello"

    def test_none_content_returns_empty(self):
        router = _FakeRouter(_FakeProvider(None))
        assert asyncio.run(call_llm_text(router, "s")) == ""

    def test_provider_error_returns_empty(self):
        router = _FakeRouter(_FakeProvider(error="down"))
        assert asyncio.run(call_llm_text(router, "s")) == ""
