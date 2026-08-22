#!/usr/bin/env python3
"""HumanValue 后端质量门禁 (防复发)

运行:
    python scripts/check_backend_quality.py

覆盖此前在开发/测试中反复出现的缺陷, 提供「一键自检」:
  1. 全量 py_compile (语法错误)
  2. FastAPI 路由签名: request 参数必须带 `: Request` 注解, 且 fastapi 已导入 Request
  3. @rate_limit 处理函数必须含 request/response 参数 (slowapi 硬性要求)
  4. 依赖完备性: 可选核心依赖 (pyotp/playwright/langchain/langgraph) 是否存在
  5. FIELD_ENCRYPTION_KEY 长度校验 (32 字节: base64 44 字符 或 hex 64 字符)

任一项失败 exit non-zero (供 CI 卡点)。
"""

from __future__ import annotations

import ast
import os
import py_compile
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent

REQUIRED_OPTIONAL = {
    "pyotp": "MFA 双因子 (C.3)",
    "langchain_core": "Agent ReAct/Skill",
    "langgraph": "评估工作流",
    "chromadb": "向量记忆",
}

# 需要 request 参数的装饰器 (slowapi 等)
_REQUIRE_REQUEST_DEPS = {"rate_limit"}

errors: list[str] = []
warnings: list[str] = []


def check_syntax() -> None:
    """1. 全量编译检查。"""
    for py in BACKEND.rglob("*.py"):
        if "node_modules" in str(py) or ".venv" in str(py):
            continue
        try:
            py_compile.compile(str(py), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"语法错误 {py.name}: {e}")


def _fastapi_imports_have_request(src: str) -> bool:
    """解析 fastapi import 中是否含 Request。"""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "fastapi":
            if any(a.name == "Request" for a in node.names):
                return True
            if node.names and node.names[0].name == "*":
                return True
    return False


def check_route_signatures() -> None:
    """2+3. 校验路由处理函数签名。"""
    route_files = list(BACKEND.glob("api/**/*.py"))
    route_files += list(BACKEND.glob("api/*.py"))
    seen = set()
    for f in route_files:
        if f in seen:
            continue
        seen.add(f)
        src = f.read_text(encoding="utf-8")
        has_request_import = _fastapi_imports_have_request(src)
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            errors.append(f"解析失败 {f.name}: {e}")
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # 是否是路由处理函数: 上方有 @router.* 装饰器
            is_route = any(
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and d.func.attr in ("get", "post", "put", "delete", "patch")
                for d in node.decorator_list
            )
            has_rate_limit = any(
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Name)
                and d.func.id in _REQUIRE_REQUEST_DEPS
                for d in node.decorator_list
            )
            # 提取 request 参数
            request_arg = None
            for a in node.args.args:
                if a.arg == "request":
                    request_arg = a
                    break
            if request_arg is not None:
                # 必须有 Request 注解
                if request_arg.annotation is None:
                    errors.append(
                        f"{f.name}:{node.lineno} 处理函数 {node.name} 的 request 参数缺 Request 注解 (会误判为查询参数)"
                    )
                elif (
                    isinstance(request_arg.annotation, ast.Name)
                    and request_arg.annotation.id == "Request"
                ):
                    if not has_request_import:
                        errors.append(
                            f"{f.name}:{node.lineno} 使用 Request 但 fastapi 未导入 Request"
                        )
            if has_rate_limit and request_arg is None:
                # slowapi 需要 request/response; 若无 request 参数但可能用了 response
                has_response = any(
                    a.arg in ("response", "websocket") for a in node.args.args
                )
                if not has_response:
                    errors.append(
                        f"{f.name}:{node.lineno} @rate_limit 处理函数 {node.name} 缺 request/response 参数 (slowapi 要求)"
                    )


def check_dependencies() -> None:
    """4. 可选核心依赖存在性。"""
    for mod, label in REQUIRED_OPTIONAL.items():
        try:
            __import__(mod)
        except ImportError:
            warnings.append(f"可选依赖缺失: {mod} ({label}) — 对应功能将降级")


def check_field_key() -> None:
    """5. FIELD_ENCRYPTION_KEY 长度校验。"""
    key = os.environ.get("FIELD_ENCRYPTION_KEY", "")
    if not key:
        warnings.append("FIELD_ENCRYPTION_KEY 未设置 — 敏感字段将明文存储 (仅限开发)")
        return
    # base64(32B)=44 字符; hex(32B)=64 字符
    if len(key) in (44, 64) and all(c in "0123456789abcdefABCDEF+/=" for c in key):
        return
    errors.append(
        "FIELD_ENCRYPTION_KEY 不是 32 字节密钥 (需 44 字符 base64 或 64 字符 hex)"
    )


def main() -> int:
    print("== HumanValue 后端质量门禁 ==")
    check_syntax()
    check_route_signatures()
    check_dependencies()
    check_field_key()

    if errors:
        print(f"\n[FAIL] {len(errors)} 个错误:")
        for e in errors:
            print("  -", e)
    else:
        print("\n[OK] 无错误 (语法/路由签名/密钥校验通过)")

    if warnings:
        print(f"\n[WARN] {len(warnings)} 个警告:")
        for w in warnings:
            print("  -", w)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
