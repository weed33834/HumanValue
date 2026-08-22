"""admin 路由公共工具

收口各 admin 路由文件重复的辅助函数(gen_id / entity_to_dict / parse_iso_datetime
通用 helper),避免复制粘贴导致的签名漂移和行为不一致。
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from fastapi import HTTPException, status

# parse_iso_datetime 的哨兵: 表示"解析失败时抛 422 而不是返回默认值"
_RAISE = object()


def parse_iso_datetime(
    value: str,
    field_name: str = "datetime",
    *,
    default: Any = _RAISE,
) -> datetime:
    """解析 ISO 8601 日期时间字符串(全 admin 路由唯一实现)。

    兼容多种常见格式:
    - 带时区偏移: 2026-07-01T00:00:00+00:00（URL 中 + 需编码为 %2B）
    - Z 后缀（JS toISOString 等）: 2026-07-01T00:00:00Z
    - 无时区: 2026-07-01T00:00:00（按 UTC 处理）
    - 仅日期: 2026-07-01（按当日 00:00:00 UTC 处理）

    Args:
        value: 待解析字符串
        field_name: 报错时使用的字段名
        default: 传入时解析失败返回该默认值; 缺省则抛 HTTP 422

    Returns:
        带 UTC 时区的 datetime
    """
    raw = value.strip()
    # 显式归一 Z/z 后缀(小写 z 的兼容早于 Python 3.11 原生支持,予以保留)
    if raw.endswith("Z") or raw.endswith("z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        try:
            dt = datetime.fromisoformat(raw + "T00:00:00+00:00")
        except ValueError:
            if default is not _RAISE:
                return default
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field_name} 格式无效，需 ISO 8601（如 2026-07-01T00:00:00Z）",
            )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def gen_id(prefix: Optional[str] = None, hex_len: int = 32) -> str:
    """生成主键

    Args:
        prefix: 可选前缀(如 "wf" / "ct"),传入时返回 `{prefix}_{hex[:24]}`;
            None 时返回完整 uuid4 hex(32 字符,向后兼容历史调用)
        hex_len: hex 部分长度(prefix=None 时生效),默认 32

    Returns:
        主键字符串
    """
    h = uuid.uuid4().hex
    if prefix:
        return f"{prefix}_{h[:24]}"
    return h[:hex_len]


def entity_to_dict(
    entity: Any,
    fields: Iterable[str],
    *,
    iso_fields: Iterable[str] = (),
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """通用 ORM entity → dict 序列化器

    收口 custom_tools / workflows / feature_flags 三个路由文件中重复的
    `_entity_to_dict` 实现,统一 datetime 字段的 ISO 格式化行为。

    Args:
        entity: SQLAlchemy ORM 实例
        fields: 要提取的字段名列表
        iso_fields: fields 中需要转 ISO 格式字符串的 datetime 字段
        extra: 额外字段(如计算字段或跨表 join 结果),合并进返回 dict

    Returns:
        dict 形式的 entity 数据
    """
    iso_set = set(iso_fields)
    result: Dict[str, Any] = {}
    for f in fields:
        val = getattr(entity, f, None)
        if f in iso_set and isinstance(val, datetime):
            val = val.isoformat()
        result[f] = val
    if extra:
        result.update(extra)
    return result
