"""M28 数据管道与集成服务 (数据源 / 转换规则 / 管道运行 / 统计)"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenant_context import get_current_tenant
from models.pipeline_models import (
    SOURCE_TYPES,
    DataQualityCheck,
    DataSource,
    Pipeline,
    SyncRecord,
    TransformRule,
)

logger = logging.getLogger(__name__)

_RULE_TYPES = ("clean", "dedup", "mask", "normalize", "aggregate", "map")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_source(
        self, name, source_type="file", conn_config=None, description=None
    ) -> DataSource:
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"非法数据源类型: {source_type}")
        cred = None
        config = dict(conn_config or {})
        credentials = config.pop("credentials", None)
        if credentials:
            from core.field_crypto import get_field_cipher

            cred = get_field_cipher().encrypt(
                json.dumps(credentials, ensure_ascii=False)
            )
        src = DataSource(
            name=name,
            source_type=source_type,
            conn_config=config,
            credentials_enc=cred,
            status="inactive",
            description=description,
            tenant_id=get_current_tenant(),
        )
        self.session.add(src)
        await self.session.commit()
        await self.session.refresh(src)
        return src

    async def list_sources(self) -> List[Dict[str, Any]]:
        rows = (
            (
                await self.session.execute(
                    select(DataSource)
                    .where(DataSource.tenant_id == get_current_tenant())
                    .order_by(DataSource.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": s.id,
                "name": s.name,
                "source_type": s.source_type,
                "conn_config": s.conn_config or {},
                "status": s.status,
                "last_sync_at": s.last_sync_at.isoformat() if s.last_sync_at else None,
                "description": s.description,
            }
            for s in rows
        ]

    async def get_source(self, source_id: int) -> Optional[DataSource]:
        return (
            await self.session.execute(
                select(DataSource).where(
                    DataSource.id == source_id,
                    DataSource.tenant_id == get_current_tenant(),
                )
            )
        ).scalar_one_or_none()

    async def delete_source(self, source_id: int) -> bool:
        s = await self.get_source(source_id)
        if s is None:
            return False
        await self.session.delete(s)
        await self.session.commit()
        return True

    async def test_source(self, source_id: int) -> Dict[str, Any]:
        s = await self.get_source(source_id)
        if s is None:
            return {"connected": False, "error": "数据源不存在"}
        try:
            records = await self._extract(s)
            return {
                "connected": True,
                "sample_count": len(records),
                "sample": records[:3],
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def _extract(self, src: DataSource) -> List[Dict[str, Any]]:
        cfg = src.conn_config or {}
        if src.source_type == "file":
            path = cfg.get("path")
            if not path or not os.path.exists(path):
                raise ValueError(f"文件不存在: {path}")
            ext = os.path.splitext(path)[1].lower()
            if ext in (".json", ".jsonl"):
                records = []
                with open(path, "r", encoding="utf-8") as f:
                    if ext == ".jsonl":
                        records = [json.loads(l) for l in f if l.strip()]
                    else:
                        data = json.load(f)
                        records = data if isinstance(data, list) else [data]
                return records
            if ext == ".csv":
                import csv

                with open(path, newline="", encoding="utf-8") as f:
                    return [dict(r) for r in csv.DictReader(f)]
            raise ValueError(f"不支持的文件类型: {ext}")
        if src.source_type == "api":
            import httpx

            resp = httpx.get(cfg.get("url", ""), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else [data]
        raise ValueError(f"暂不支持该类型数据源的在线提取: {src.source_type}")

    async def create_rule(
        self, name, rule_type, config=None, description=None
    ) -> TransformRule:
        if rule_type not in _RULE_TYPES:
            raise ValueError(f"非法规则类型: {rule_type}")
        r = TransformRule(
            name=name,
            rule_type=rule_type,
            config=config or {},
            enabled=True,
            description=description,
            tenant_id=get_current_tenant(),
        )
        self.session.add(r)
        await self.session.commit()
        await self.session.refresh(r)
        return r

    async def list_rules(self) -> List[Dict[str, Any]]:
        rows = (
            (
                await self.session.execute(
                    select(TransformRule)
                    .where(TransformRule.tenant_id == get_current_tenant())
                    .order_by(TransformRule.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": r.id,
                "name": r.name,
                "rule_type": r.rule_type,
                "config": r.config or {},
                "enabled": r.enabled,
                "description": r.description,
            }
            for r in rows
        ]

    async def delete_rule(self, rule_id: int) -> bool:
        r = (
            await self.session.execute(
                select(TransformRule).where(TransformRule.id == rule_id)
            )
        ).scalar_one_or_none()
        if r is None:
            return False
        await self.session.delete(r)
        await self.session.commit()
        return True

    def apply_rule(
        self, rule: TransformRule, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        cfg = rule.config or {}
        if rule.rule_type == "clean":
            field = cfg.get("field")
            return [
                r
                for r in records
                if not (
                    field
                    and (r.get(field) is None or str(r.get(field, "")).strip() == "")
                )
            ]
        if rule.rule_type == "dedup":
            key = cfg.get("key", "id")
            seen, out = set(), []
            for r in records:
                k = str(r.get(key, ""))
                if k and k not in seen:
                    seen.add(k)
                    out.append(r)
            return out
        if rule.rule_type == "mask":
            field = cfg.get("field")
            pattern = cfg.get("pattern", r"\d{11}")
            replacement = cfg.get("replacement", "***")
            if not field:
                return records
            out = []
            for r in records:
                r2 = dict(r)
                if isinstance(r2.get(field), str):
                    r2[field] = re.sub(pattern, replacement, r2[field])
                out.append(r2)
            return out
        if rule.rule_type == "normalize":
            field = cfg.get("field")
            if not field:
                return records
            out = []
            for r in records:
                r2 = dict(r)
                if isinstance(r2.get(field), str):
                    r2[field] = r2[field].strip().lower()
                out.append(r2)
            return out
        if rule.rule_type == "map":
            mapping = cfg.get("mapping") or {}
            return [{mapping.get(k, k): v for k, v in r.items()} for r in records]
        return records

    async def test_rule(
        self, rule_id: int, sample: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        r = (
            await self.session.execute(
                select(TransformRule).where(TransformRule.id == rule_id)
            )
        ).scalar_one_or_none()
        if r is None:
            return {"error": "规则不存在"}
        result = self.apply_rule(r, sample)
        return {
            "input_count": len(sample),
            "output_count": len(result),
            "output": result[:20],
        }

    async def create_pipeline(
        self, name, source_id=None, mode="batch", steps=None, schedule_cron=None
    ) -> Pipeline:
        p = Pipeline(
            name=name,
            source_id=source_id,
            mode=mode,
            steps=steps or [],
            schedule_cron=schedule_cron,
            enabled=True,
            tenant_id=get_current_tenant(),
        )
        self.session.add(p)
        await self.session.commit()
        await self.session.refresh(p)
        return p

    async def list_pipelines(self) -> List[Dict[str, Any]]:
        rows = (
            (
                await self.session.execute(
                    select(Pipeline)
                    .where(Pipeline.tenant_id == get_current_tenant())
                    .order_by(Pipeline.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": p.id,
                "name": p.name,
                "mode": p.mode,
                "source_id": p.source_id,
                "steps": p.steps or [],
                "schedule_cron": p.schedule_cron,
                "enabled": p.enabled,
                "last_run_at": p.last_run_at.isoformat() if p.last_run_at else None,
            }
            for p in rows
        ]

    async def get_pipeline(self, pipeline_id: int) -> Optional[Pipeline]:
        return (
            await self.session.execute(
                select(Pipeline).where(
                    Pipeline.id == pipeline_id,
                    Pipeline.tenant_id == get_current_tenant(),
                )
            )
        ).scalar_one_or_none()

    async def run_pipeline(self, pipeline_id: int) -> Dict[str, Any]:
        pipe = await self.get_pipeline(pipeline_id)
        if pipe is None:
            return {"error": "管道不存在"}
        src = await self.get_source(pipe.source_id) if pipe.source_id else None
        if src is None:
            return {"error": "管道缺少数据源"}
        start = _now()
        t0 = time.time()
        record = SyncRecord(
            pipeline_id=pipeline_id,
            source_id=pipe.source_id,
            batch_no=f"B-{start.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}",
            status="running",
            start_time=start,
            tenant_id=get_current_tenant(),
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        try:
            records = await self._extract(src)
            total = len(records)
            rule_ids = [
                int(s.get("rule_id"))
                for s in (pipe.steps or [])
                if s.get("step_type") == "transform" and s.get("rule_id")
            ]
            if rule_ids:
                rules = [
                    r
                    for r in (
                        await self.session.execute(
                            select(TransformRule).where(TransformRule.id.in_(rule_ids))
                        )
                    )
                    .scalars()
                    .all()
                    if r.enabled
                ]
                for rule in rules:
                    records = self.apply_rule(rule, records)
            success = len(records)
            checks = []
            for q in [s for s in (pipe.steps or []) if s.get("step_type") == "quality"]:
                field = (q.get("config") or {}).get("field")
                threshold = float((q.get("config") or {}).get("threshold", 0.05))
                if field and records:
                    null_count = sum(
                        1
                        for r in records
                        if r.get(field) is None or str(r.get(field, "")).strip() == ""
                    )
                    actual = null_count / len(records)
                else:
                    actual = 0.0
                passed = actual <= threshold
                c = DataQualityCheck(
                    pipeline_id=pipeline_id,
                    sync_record_id=record.id,
                    rule=f"字段 {field or 'n/a'} 空值率",
                    threshold=threshold,
                    actual=round(actual, 4),
                    passed=passed,
                    alert_level="warning" if not passed else "info",
                    message="通过" if passed else f"空值率 {actual:.2%} 超阈值",
                    tenant_id=get_current_tenant(),
                )
                self.session.add(c)
                checks.append(c)
            record.rows_total = total
            record.rows_success = success
            record.rows_failed = total - success
            record.duration_ms = int((time.time() - t0) * 1000)
            record.end_time = _now()
            record.status = "success" if success == total else "partial"
            pipe.last_run_id = record.id
            pipe.last_run_at = _now()
            src.status = "active"
            src.last_sync_at = _now()
            await self.session.commit()
            return {
                "pipeline_id": pipeline_id,
                "sync_record_id": record.id,
                "rows_total": total,
                "rows_success": success,
                "rows_failed": total - success,
                "duration_ms": record.duration_ms,
                "status": record.status,
                "quality_checks": [
                    {
                        "rule": c.rule,
                        "passed": c.passed,
                        "actual": c.actual,
                        "threshold": c.threshold,
                    }
                    for c in checks
                ],
                "sample_output": records[:5],
            }
        except Exception as e:
            logger.exception("管道执行失败 pipeline_id=%s", pipeline_id)
            record.status = "failed"
            record.error = str(e)
            record.end_time = _now()
            record.duration_ms = int((time.time() - t0) * 1000)
            await self.session.commit()
            return {"pipeline_id": pipeline_id, "status": "failed", "error": str(e)}

    async def sync_stats(self) -> Dict[str, Any]:
        rows = (
            (
                await self.session.execute(
                    select(SyncRecord).where(
                        SyncRecord.tenant_id == get_current_tenant()
                    )
                )
            )
            .scalars()
            .all()
        )
        total = len(rows)
        ok = sum(1 for r in rows if r.status in ("success", "partial"))
        by_pipeline: Dict[int, Dict[str, Any]] = {}
        for r in rows:
            agg = by_pipeline.setdefault(
                r.pipeline_id, {"runs": 0, "rows": 0, "ok": 0, "failed": 0}
            )
            agg["runs"] += 1
            agg["rows"] += r.rows_total or 0
            agg["ok" if r.status in ("success", "partial") else "failed"] += 1
        return {
            "total_runs": total,
            "success_runs": ok,
            "failed_runs": total - ok,
            "success_rate": round(ok / total, 4) if total else None,
            "total_rows": sum(r.rows_total or 0 for r in rows),
            "avg_duration_ms": (
                int(sum(r.duration_ms or 0 for r in rows) / total) if total else 0
            ),
            "by_pipeline": by_pipeline,
        }

    async def list_sync_records(
        self, pipeline_id=None, page=1, page_size=20
    ) -> Dict[str, Any]:
        tenant = get_current_tenant()
        conditions = [SyncRecord.tenant_id == tenant]
        if pipeline_id:
            conditions.append(SyncRecord.pipeline_id == pipeline_id)
        base = select(SyncRecord).where(and_(*conditions))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar()
            or 0
        )
        rows = (
            (
                await self.session.execute(
                    base.order_by(SyncRecord.start_time.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "records": [
                {
                    "id": r.id,
                    "pipeline_id": r.pipeline_id,
                    "batch_no": r.batch_no,
                    "rows_total": r.rows_total,
                    "rows_success": r.rows_success,
                    "rows_failed": r.rows_failed,
                    "duration_ms": r.duration_ms,
                    "status": r.status,
                    "error": r.error,
                }
                for r in rows
            ],
        }
