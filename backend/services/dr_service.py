"""M29 容灾与业务连续性服务 (备份 / 校验 / 恢复 / DR 计划 / 演练 / 指标)"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.tenant_context import get_current_tenant
from models.dr_models import BackupJob, BackupSet, ContinuityMetric, DRPlan, Drill

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _backup_dir() -> str:
    d = getattr(get_settings(), "backup_dir", "./backups")
    os.makedirs(d, exist_ok=True)
    return d


def _db_file_path() -> Optional[str]:
    url = getattr(get_settings(), "database_url", "") or ""
    if not url.startswith("sqlite"):
        return None
    path = url.split(":///")[-1].split("?")[0]
    return path if os.path.exists(path) else None


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class DRService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_backup(
        self,
        name: str,
        scope: str = "database",
        backup_type: str = "full",
        job_id: Optional[int] = None,
    ) -> BackupSet:
        if scope == "database":
            src = _db_file_path()
            if src is None:
                raise ValueError(
                    "仅支持 SQLite 数据库备份 (PostgreSQL 请用外部备份工具)"
                )
        elif scope == "object_store":
            src = get_settings().attachment_dir
        else:
            raise ValueError(f"暂不支持该备份范围: {scope}")
        if not os.path.exists(src):
            raise ValueError(f"备份源不存在: {src}")
        d = _backup_dir()
        ts = _now().strftime("%Y%m%d%H%M%S")
        rel = f"{scope}_{ts}_{uuid.uuid4().hex[:6]}.bak"
        dst = os.path.join(d, rel)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        size = (
            sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(dst)
                for f in fs
            )
            if os.path.isdir(dst)
            else os.path.getsize(dst)
        )
        checksum = _sha256(dst) if not os.path.isdir(dst) else None
        bset = BackupSet(
            job_id=job_id,
            name=name or f"backup_{ts}",
            scope=scope,
            backup_type=backup_type,
            location=rel,
            size_bytes=size,
            checksum=checksum,
            status="completed",
            tenant_id=get_current_tenant(),
        )
        self.session.add(bset)
        await self.session.commit()
        await self.session.refresh(bset)
        if getattr(get_settings(), "backup_verify_enabled", True):
            await self.verify_backup(bset.id)
        return bset

    async def get_backup_set(self, backup_id: int) -> Optional[BackupSet]:
        return (
            await self.session.execute(
                select(BackupSet).where(
                    BackupSet.id == backup_id,
                    BackupSet.tenant_id == get_current_tenant(),
                )
            )
        ).scalar_one_or_none()

    async def list_backup_sets(
        self, scope: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        tenant = get_current_tenant()
        conditions = [BackupSet.tenant_id == tenant]
        if scope:
            conditions.append(BackupSet.scope == scope)
        base = select(BackupSet).where(and_(*conditions))
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
                    base.order_by(BackupSet.snapshot_time.desc())
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
            "backups": [self._bset_dict(b) for b in rows],
        }

    async def verify_backup(self, backup_id: int) -> Optional[BackupSet]:
        bset = await self.get_backup_set(backup_id)
        if bset is None:
            return None
        path = os.path.join(_backup_dir(), bset.location)
        if not os.path.exists(path):
            bset.verify_status = "missing"
        elif bset.checksum and _sha256(path) == bset.checksum:
            bset.verify_status = "verified"
        else:
            bset.verify_status = "verified_failed"
        bset.status = "verified" if bset.verify_status == "verified" else bset.status
        await self.session.commit()
        await self.session.refresh(bset)
        return bset

    async def restore_backup(
        self, backup_id: int, target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        bset = await self.verify_backup(backup_id)
        if bset is None:
            return {"error": "备份集不存在"}
        if bset.verify_status != "verified":
            return {"error": f"备份校验未通过 (status={bset.verify_status})"}
        src = os.path.join(_backup_dir(), bset.location)
        if not os.path.exists(src):
            return {"error": "备份文件缺失"}
        if not target_path:
            restore_dir = os.path.join(_backup_dir(), "restored")
            os.makedirs(restore_dir, exist_ok=True)
            target_path = os.path.join(restore_dir, f"restored_{bset.id}")
        if os.path.isdir(src):
            shutil.copytree(src, target_path, dirs_exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(src, target_path)
        bset.restore_test_status = "passed"
        await self.session.commit()
        return {"restored": True, "backup_id": backup_id, "target": target_path}

    async def create_job(
        self, name, scope="database", backup_type="full", schedule=None
    ) -> BackupJob:
        j = BackupJob(
            name=name,
            scope=scope,
            backup_type=backup_type,
            schedule=schedule,
            enabled=True,
            tenant_id=get_current_tenant(),
        )
        self.session.add(j)
        await self.session.commit()
        await self.session.refresh(j)
        return j

    async def list_jobs(self) -> List[Dict[str, Any]]:
        rows = (
            (
                await self.session.execute(
                    select(BackupJob)
                    .where(BackupJob.tenant_id == get_current_tenant())
                    .order_by(BackupJob.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": j.id,
                "name": j.name,
                "scope": j.scope,
                "backup_type": j.backup_type,
                "schedule": j.schedule,
                "enabled": j.enabled,
            }
            for j in rows
        ]

    async def create_plan(
        self,
        name,
        tier=3,
        rto_target_seconds=None,
        rpo_target_seconds=None,
        scenarios=None,
        steps=None,
        contacts=None,
    ) -> DRPlan:
        s = get_settings()
        p = DRPlan(
            name=name,
            tier=tier,
            rto_target_seconds=rto_target_seconds
            or getattr(s, "dr_rto_target_seconds", 300),
            rpo_target_seconds=rpo_target_seconds
            or getattr(s, "dr_rpo_target_seconds", 300),
            scenarios=scenarios or ["failover", "restore"],
            steps=steps or [],
            contacts=contacts or [],
            status="draft",
            tenant_id=get_current_tenant(),
        )
        self.session.add(p)
        await self.session.commit()
        await self.session.refresh(p)
        return p

    async def list_plans(self) -> List[Dict[str, Any]]:
        rows = (
            (
                await self.session.execute(
                    select(DRPlan)
                    .where(DRPlan.tenant_id == get_current_tenant())
                    .order_by(DRPlan.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [self._plan_dict(p) for p in rows]

    async def get_plan(self, plan_id: int) -> Optional[DRPlan]:
        return (
            await self.session.execute(
                select(DRPlan).where(
                    DRPlan.id == plan_id, DRPlan.tenant_id == get_current_tenant()
                )
            )
        ).scalar_one_or_none()

    async def publish_plan(self, plan_id: int) -> Optional[DRPlan]:
        p = await self.get_plan(plan_id)
        if p is None:
            return None
        p.status = "published"
        await self.session.commit()
        await self.session.refresh(p)
        return p

    async def create_drill(self, name, scenario="restore", plan_id=None) -> Drill:
        d = Drill(
            name=name,
            scenario=scenario,
            plan_id=plan_id,
            result="running",
            started_at=_now(),
            tenant_id=get_current_tenant(),
        )
        self.session.add(d)
        await self.session.commit()
        await self.session.refresh(d)
        return d

    async def run_drill(
        self, drill_id: int, measure_rto: int, measure_rpo: int
    ) -> Optional[Drill]:
        d = (
            await self.session.execute(
                select(Drill).where(
                    Drill.id == drill_id, Drill.tenant_id == get_current_tenant()
                )
            )
        ).scalar_one_or_none()
        if d is None:
            return None
        plan = await self.get_plan(d.plan_id) if d.plan_id else None
        rto_target = (
            plan.rto_target_seconds if plan else get_settings().dr_rto_target_seconds
        )
        rpo_target = (
            plan.rpo_target_seconds if plan else get_settings().dr_rpo_target_seconds
        )
        d.measured_rto_seconds = measure_rto
        d.measured_rpo_seconds = measure_rpo
        d.finished_at = _now()
        rto_pass = measure_rto <= rto_target
        rpo_pass = measure_rpo <= rpo_target
        d.result = "passed" if (rto_pass and rpo_pass) else "failed"
        d.report = {
            "scenario": d.scenario,
            "measured_rto_seconds": measure_rto,
            "rto_target": rto_target,
            "measured_rpo_seconds": measure_rpo,
            "rpo_target": rpo_target,
            "rto_pass": rto_pass,
            "rpo_pass": rpo_pass,
            "result": d.result,
        }
        await self.session.commit()
        await self.session.refresh(d)
        await self.record_metric("actual_rto", float(measure_rto), float(rto_target))
        await self.record_metric("actual_rpo", float(measure_rpo), float(rpo_target))
        return d

    async def list_drills(self) -> List[Dict[str, Any]]:
        rows = (
            (
                await self.session.execute(
                    select(Drill)
                    .where(Drill.tenant_id == get_current_tenant())
                    .order_by(Drill.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": d.id,
                "name": d.name,
                "scenario": d.scenario,
                "plan_id": d.plan_id,
                "result": d.result,
                "measured_rto_seconds": d.measured_rto_seconds,
                "measured_rpo_seconds": d.measured_rpo_seconds,
                "report": d.report,
            }
            for d in rows
        ]

    async def record_metric(
        self, name: str, value: float, target: Optional[float] = None
    ) -> ContinuityMetric:
        m = ContinuityMetric(
            name=name, value=value, target=target, tenant_id=get_current_tenant()
        )
        self.session.add(m)
        await self.session.commit()
        await self.session.refresh(m)
        return m

    async def metrics(self) -> Dict[str, Any]:
        tenant = get_current_tenant()
        latest = {}
        for name in ("actual_rto", "actual_rpo"):
            row = (
                await self.session.execute(
                    select(ContinuityMetric)
                    .where(
                        ContinuityMetric.tenant_id == tenant,
                        ContinuityMetric.name == name,
                    )
                    .order_by(ContinuityMetric.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            latest[name] = {"value": row.value, "target": row.target} if row else None
        bsets = (
            (
                await self.session.execute(
                    select(BackupSet).where(BackupSet.tenant_id == tenant)
                )
            )
            .scalars()
            .all()
        )
        backup_total = len(bsets)
        backup_ok = sum(
            1
            for b in bsets
            if b.status in ("completed", "verified")
            and b.verify_status != "verified_failed"
        )
        drills = (
            (
                await self.session.execute(
                    select(Drill).where(
                        Drill.tenant_id == tenant, Drill.result.isnot(None)
                    )
                )
            )
            .scalars()
            .all()
        )
        drill_total = len(drills)
        drill_pass = sum(1 for d in drills if d.result == "passed")
        return {
            "rto": latest.get("actual_rto"),
            "rpo": latest.get("actual_rpo"),
            "backup_success_rate": (
                round(backup_ok / backup_total, 4) if backup_total else None
            ),
            "backup_total": backup_total,
            "drill_pass_rate": (
                round(drill_pass / drill_total, 4) if drill_total else None
            ),
            "drill_total": drill_total,
        }

    @staticmethod
    def _bset_dict(b: BackupSet) -> Dict[str, Any]:
        return {
            "id": b.id,
            "job_id": b.job_id,
            "name": b.name,
            "scope": b.scope,
            "backup_type": b.backup_type,
            "location": b.location,
            "size_bytes": b.size_bytes,
            "checksum": b.checksum,
            "status": b.status,
            "verify_status": b.verify_status,
            "restore_test_status": b.restore_test_status,
            "snapshot_time": b.snapshot_time.isoformat() if b.snapshot_time else None,
        }

    @staticmethod
    def _plan_dict(p: DRPlan) -> Dict[str, Any]:
        return {
            "id": p.id,
            "name": p.name,
            "tier": p.tier,
            "rto_target_seconds": p.rto_target_seconds,
            "rpo_target_seconds": p.rpo_target_seconds,
            "scenarios": p.scenarios or [],
            "steps": p.steps or [],
            "contacts": p.contacts or [],
            "status": p.status,
        }
