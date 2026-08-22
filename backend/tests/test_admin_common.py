"""api/admin/_common 公共工具测试: gen_id / entity_to_dict / parse_iso_datetime"""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from api.admin._common import entity_to_dict, gen_id, parse_iso_datetime


class TestGenId:
    def test_no_prefix_returns_full_hex(self):
        value = gen_id()
        assert len(value) == 32
        int(value, 16)  # 必须是合法 hex

    def test_with_prefix(self):
        value = gen_id("wf")
        assert value.startswith("wf_")
        assert len(value) == len("wf_") + 24

    def test_uniqueness(self):
        assert gen_id() != gen_id()


class _FakeEntity:
    def __init__(self):
        self.id = "abc"
        self.name = "n1"
        self.created_at = datetime(2026, 8, 22, tzinfo=timezone.utc)


class TestEntityToDict:
    def test_basic_fields_and_iso(self):
        e = _FakeEntity()
        out = entity_to_dict(e, ["id", "name", "created_at"], iso_fields=["created_at"])
        assert out["id"] == "abc"
        assert out["created_at"] == "2026-08-22T00:00:00+00:00"

    def test_extra_merge(self):
        e = _FakeEntity()
        out = entity_to_dict(e, ["id"], extra={"count": 3})
        assert out["count"] == 3

    def test_missing_field_defaults_none(self):
        e = _FakeEntity()
        out = entity_to_dict(e, ["nonexistent"])
        assert out["nonexistent"] is None


class TestParseIsoDatetime:
    def test_z_suffix(self):
        dt = parse_iso_datetime("2026-07-01T00:00:00Z", "start_date")
        assert dt.tzinfo is not None
        assert dt.year == 2026 and dt.month == 7

    def test_offset(self):
        dt = parse_iso_datetime("2026-07-01T00:00:00+08:00", "d")
        assert dt.utcoffset().total_seconds() == 8 * 3600

    def test_naive_treated_as_utc(self):
        dt = parse_iso_datetime("2026-07-01T00:00:00", "d")
        assert dt.tzinfo == timezone.utc

    def test_date_only(self):
        dt = parse_iso_datetime("2026-07-01", "d")
        assert (dt.hour, dt.minute) == (0, 0)
        assert dt.tzinfo == timezone.utc

    def test_invalid_raises_422(self):
        with pytest.raises(HTTPException) as exc:
            parse_iso_datetime("not-a-date", "start_date")
        assert exc.value.status_code == 422
        assert "start_date" in exc.value.detail

    def test_default_on_failure(self):
        sentinel = datetime(2000, 1, 1, tzinfo=timezone.utc)
        result = parse_iso_datetime("bad", "d", default=sentinel)
        assert result is sentinel

    def test_lowercase_z_suffix(self):
        dt = parse_iso_datetime("2026-07-01T00:00:00z", "d")
        assert dt.tzinfo is not None
