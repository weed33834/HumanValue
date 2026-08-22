"""结构化输出校验 (M18 B.2/B.5)"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import jsonschema  # type: ignore

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    jsonschema = None  # type: ignore[assignment, misc]


def validate_json_schema(obj: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    if not schema:
        return True, []
    if JSONSCHEMA_AVAILABLE:
        try:
            jsonschema.validate(instance=obj, schema=schema)
            return True, []
        except jsonschema.ValidationError as e:
            return False, [e.message]
    # 无 jsonschema 时的基本检查
    errors: List[str] = []
    if not isinstance(obj, dict):
        return False, ["顶层必须是对象"]
    for req in schema.get("required", []):
        if req not in obj:
            errors.append(f"缺少必填字段: {req}")
    return (len(errors) == 0, errors)


class ValidationRule:
    def __init__(self, field: str, check: Callable[[Any], Optional[str]]):
        self.field = field
        self.check = check


class OutputValidator:
    def __init__(self, required: Optional[List[str]] = None):
        self.required = list(required or [])
        self.enum_checks: Dict[str, List[Any]] = {}
        self.regex_checks: Dict[str, str] = {}
        self.length_checks: Dict[str, Tuple[int, int]] = {}
        self.rules: List[ValidationRule] = []

    def require_enum(self, field: str, values: List[Any]) -> "OutputValidator":
        self.enum_checks[field] = values
        return self

    def require_regex(self, field: str, pattern: str) -> "OutputValidator":
        self.regex_checks[field] = pattern
        return self

    def require_length(
        self, field: str, min_len: int, max_len: int
    ) -> "OutputValidator":
        self.length_checks[field] = (min_len, max_len)
        return self

    def add_rule(self, rule: ValidationRule) -> "OutputValidator":
        self.rules.append(rule)
        return self

    def validate(self, obj: Any) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not isinstance(obj, dict):
            return False, ["输出必须是 JSON 对象"]
        for req in self.required:
            if req not in obj or obj[req] in (None, ""):
                errors.append(f"缺少必填字段: {req}")
        for field, values in self.enum_checks.items():
            if field in obj and obj[field] not in values:
                errors.append(f"字段 {field} 必须为 {values} 之一")
        for field, pattern in self.regex_checks.items():
            if (
                field in obj
                and isinstance(obj[field], str)
                and not re.search(pattern, obj[field])
            ):
                errors.append(f"字段 {field} 不符合格式 {pattern}")
        for field, (lo, hi) in self.length_checks.items():
            if (
                field in obj
                and isinstance(obj[field], (str, list, dict))
                and not (lo <= len(obj[field]) <= hi)
            ):
                errors.append(f"字段 {field} 长度需在 [{lo}, {hi}] 内")
        for rule in self.rules:
            if rule.field in obj:
                err = rule.check(obj[rule.field])
                if err:
                    errors.append(err)
        return (len(errors) == 0, errors)
