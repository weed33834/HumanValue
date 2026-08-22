"""统一错误码体系 (M19 A)"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException

_DOC_BASE = "https://gitcode.com/badhope/HumanValue/tree/main/"

ERROR_CODES: Dict[str, Dict[str, Any]] = {
    "E-AUTH-1001": {
        "message": "登录失败，邮箱或密码错误",
        "http_status": 401,
        "module": "AUTH",
        "doc": "docs/error-codes.md",
    },
    "E-AUTH-1002": {
        "message": "登录尝试过多，账号已临时锁定，请稍后再试",
        "http_status": 423,
        "module": "AUTH",
        "doc": "docs/error-codes.md",
    },
    "E-AUTH-1003": {
        "message": "需要双因子验证",
        "http_status": 403,
        "module": "AUTH",
        "doc": "docs/error-codes.md",
    },
    "E-AUTH-1004": {
        "message": "双因子验证码错误",
        "http_status": 401,
        "module": "AUTH",
        "doc": "docs/error-codes.md",
    },
    "E-AUTH-1005": {
        "message": "管理员账号必须启用双因子认证后才能登录",
        "http_status": 403,
        "module": "AUTH",
        "doc": "docs/error-codes.md",
    },
    "E-PERM-2001": {
        "message": "无权执行该操作",
        "http_status": 403,
        "module": "PERM",
        "doc": "docs/error-codes.md",
    },
    "E-VALID-3001": {
        "message": "参数校验失败",
        "http_status": 422,
        "module": "VALID",
        "doc": "docs/error-codes.md",
    },
    "E-VALID-3002": {
        "message": "输出结构校验失败",
        "http_status": 422,
        "module": "VALID",
        "doc": "docs/error-codes.md",
    },
    "E-LLM-4001": {
        "message": "模型调用失败",
        "http_status": 502,
        "module": "LLM",
        "doc": "docs/error-codes.md",
    },
    "E-LLM-4002": {
        "message": "模型未配置或不可用",
        "http_status": 503,
        "module": "LLM",
        "doc": "docs/error-codes.md",
    },
    "E-TOOL-5001": {
        "message": "工具执行失败",
        "http_status": 502,
        "module": "TOOL",
        "doc": "docs/error-codes.md",
    },
    "E-TOOL-5002": {
        "message": "工具不存在",
        "http_status": 404,
        "module": "TOOL",
        "doc": "docs/error-codes.md",
    },
    "E-RAG-6001": {
        "message": "知识库检索失败",
        "http_status": 502,
        "module": "RAG",
        "doc": "docs/error-codes.md",
    },
    "E-TASK-7001": {
        "message": "任务状态流转不合法",
        "http_status": 400,
        "module": "TASK",
        "doc": "docs/error-codes.md",
    },
    "E-SYS-8001": {
        "message": "系统内部错误",
        "http_status": 500,
        "module": "SYS",
        "doc": "docs/error-codes.md",
    },
    "E-SYS-8002": {
        "message": "功能未实现或依赖缺失",
        "http_status": 501,
        "module": "SYS",
        "doc": "docs/error-codes.md",
    },
    "E-NET-9001": {
        "message": "网络请求失败",
        "http_status": 502,
        "module": "NET",
        "doc": "docs/error-codes.md",
    },
}


class AppError(Exception):
    def __init__(
        self,
        code: str,
        user_message: Optional[str] = None,
        http_status: Optional[int] = None,
        detail: Optional[Dict[str, Any]] = None,
        doc: Optional[str] = None,
    ):
        self.code = code
        meta = ERROR_CODES.get(code, {})
        self.user_message = user_message or meta.get("message", "发生错误")
        self.http_status = http_status or meta.get("http_status", 500)
        self.module = meta.get("module", "SYS")
        self.doc = doc or meta.get("doc")
        self.detail = detail or {}
        self.message = self._compose()
        super().__init__(self.message)

    def _compose(self) -> str:
        parts = [self.user_message, f"错误码 {self.code}"]
        if self.doc:
            parts.append(f"[查看排查指南]({_DOC_BASE}{self.doc})")
        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.user_message,
            "http_status": self.http_status,
            "detail": self.detail,
        }

    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=self.http_status, detail=self.to_dict())


def error_codes_table() -> Dict[str, Dict[str, Any]]:
    return {
        code: {
            "message": m.get("message"),
            "http_status": m.get("http_status"),
            "module": m.get("module"),
            "doc": m.get("doc"),
        }
        for code, m in ERROR_CODES.items()
    }


def register_error_code(
    code: str,
    message: str,
    http_status: int = 500,
    module: str = "SYS",
    doc: Optional[str] = None,
) -> None:
    if code in ERROR_CODES:
        raise ValueError(f"错误码重复登记: {code}")
    ERROR_CODES[code] = {
        "message": message,
        "http_status": http_status,
        "module": module,
        "doc": doc,
    }
