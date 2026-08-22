"""文本处理 API (M18: 关键词提取 / 摘要 / 去重 / 归一化 / JSON Schema 校验 / 错误码)"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from core.errors import error_codes_table
from core.output_validator import validate_json_schema
from core.rate_limit import rate_limit
from core.text_utils import (
    extract_keywords,
    fingerprint,
    normalize_text,
    summarize_extractive,
    text_dedup,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/text", tags=["text"])


class KeywordsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=2, max_length=100000)
    top_k: int = Field(default=5, ge=1, le=20)
    method: str = Field(default="hybrid")


class SummarizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=10, max_length=100000)
    max_sentences: int = Field(default=3, ge=1, le=10)


class DedupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texts: List[str] = Field(min_length=1, max_length=1000)
    threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class NormalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=100000)


class SchemaValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: Any = Field(description="待校验对象")
    json_schema: Dict[str, Any] = Field(description="JSON Schema")


@router.post("/keywords", response_model=Dict[str, Any])
@rate_limit("60/minute")
async def keywords(request: Request, payload: KeywordsRequest):
    return {
        "keywords": extract_keywords(
            payload.text, top_k=payload.top_k, method=payload.method
        ),
        "method": payload.method,
    }


@router.post("/summarize", response_model=Dict[str, Any])
async def summarize(payload: SummarizeRequest):
    summary = summarize_extractive(payload.text, max_sentences=payload.max_sentences)
    return {"summary": summary, "length": len(summary)}


@router.post("/dedup", response_model=Dict[str, Any])
async def dedup(payload: DedupRequest):
    result = text_dedup(payload.texts, threshold=payload.threshold)
    return {
        "input_count": len(payload.texts),
        "deduped_count": len(result),
        "removed": len(payload.texts) - len(result),
        "texts": result,
    }


@router.post("/normalize", response_model=Dict[str, Any])
async def normalize(payload: NormalizeRequest):
    return {"normalized": normalize_text(payload.text)}


@router.post("/fingerprint", response_model=Dict[str, Any])
async def fingerprint_endpoint(payload: NormalizeRequest):
    return {"fingerprint": fingerprint(payload.text)}


@router.post("/validate-schema", response_model=Dict[str, Any])
async def validate_schema(payload: SchemaValidateRequest):
    ok, errors = validate_json_schema(payload.value, payload.json_schema)
    return {"valid": ok, "errors": errors}


@router.get("/error-codes", response_model=Dict[str, Any])
async def list_error_codes():
    return {"total": len(error_codes_table()), "codes": error_codes_table()}
