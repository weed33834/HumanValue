"""LLM 响应缓存 (M23) — 精确哈希 + 可选语义"""

from __future__ import annotations

import hashlib
import inspect
import json
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    key: str
    content: str
    model: str
    created_at: float
    expires_at: float
    semantic_key: Optional[str] = None

    def expired(self, now: float) -> bool:
        return now > self.expires_at


class LLMResponseCache:
    def __init__(
        self,
        ttl_seconds: int = 600,
        max_size: int = 1000,
        embedding_fn: Optional[Callable[[str], Any]] = None,
        similarity_threshold: float = 0.95,
    ):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.embedding_fn = embedding_fn
        self.similarity_threshold = similarity_threshold
        self._cache: "OrderedDict[str, CacheEntry]" = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.near_hits = 0

    @staticmethod
    def messages_key(
        messages: Any, model: str, response_format: Optional[dict] = None
    ) -> str:
        norm = _normalize_messages(messages)
        payload = json.dumps(
            {"messages": norm, "model": model, "response_format": response_format},
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def _embed(self, text: str) -> Optional[List[float]]:
        try:
            result = self.embedding_fn(text)
            if inspect.isawaitable(result):
                result = await result
            return result
        except Exception as e:
            logger.debug("embedding 调用失败: %s", e)
            return None

    async def get(
        self, messages: Any, model: str, response_format: Optional[dict] = None
    ) -> Optional[str]:
        now = time.time()
        key = self.messages_key(messages, model, response_format)
        with self._lock:
            entry = self._cache.get(key)
            if entry is not None:
                if entry.expired(now):
                    self._cache.pop(key, None)
                else:
                    self._cache.move_to_end(key)
                    self.hits += 1
                    return entry.content
            if self.embedding_fn:
                sem_key = _messages_to_text(messages)
                if sem_key:
                    target = await self._embed(sem_key)
                    if target:
                        best = None
                        for k, e in list(self._cache.items()):
                            if e.expired(now) or not e.semantic_key:
                                continue
                            other = await self._embed(e.semantic_key)
                            if not other:
                                continue
                            sim = _cosine(target, other)
                            if sim >= self.similarity_threshold and (
                                best is None or sim > best[1]
                            ):
                                best = (k, sim)
                        if best:
                            self._cache.move_to_end(best[0])
                            self.near_hits += 1
                            self.hits += 1
                            return self._cache[best[0]].content
            self.misses += 1
            return None

    async def set(
        self,
        messages: Any,
        model: str,
        content: str,
        response_format: Optional[dict] = None,
    ) -> None:
        now = time.time()
        key = self.messages_key(messages, model, response_format)
        entry = CacheEntry(
            key=key,
            content=content,
            model=model,
            created_at=now,
            expires_at=now + self.ttl_seconds,
            semantic_key=_messages_to_text(messages) if self.embedding_fn else None,
        )
        with self._lock:
            self._cache[key] = entry
            self._cache.move_to_end(key)
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    async def clear(self) -> int:
        with self._lock:
            n = len(self._cache)
            self._cache.clear()
            self.hits = self.misses = self.near_hits = 0
            return n

    async def stats(self) -> Dict[str, Any]:
        now = time.time()
        with self._lock:
            total = self.hits + self.misses
            return {
                "enabled": True,
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "near_hits": self.near_hits,
                "hit_rate": round(self.hits / total, 4) if total else 0.0,
            }


def _normalize_messages(messages: Any) -> List[Dict[str, Any]]:
    out = []
    if not messages:
        return out
    if not isinstance(messages, (list, tuple)):
        messages = [messages]
    for m in messages:
        if isinstance(m, dict):
            out.append({"role": m.get("role"), "content": m.get("content")})
        else:
            out.append(
                {
                    "role": getattr(m, "role", None),
                    "content": getattr(m, "content", None),
                }
            )
    return out


def _messages_to_text(messages: Any) -> str:
    parts = []
    for m in _normalize_messages(messages):
        c = m.get("content")
        if isinstance(c, list):
            parts.extend(
                str(p.get("text", ""))
                for p in c
                if isinstance(p, dict) and p.get("type") == "text"
            )
        elif c:
            parts.append(str(c))
    return " ".join(parts)


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


_global_cache: Optional[LLMResponseCache] = None


def get_global_llm_cache() -> LLMResponseCache:
    global _global_cache
    if _global_cache is None:
        from core.config import get_settings

        s = get_settings()
        _global_cache = LLMResponseCache(
            ttl_seconds=getattr(s, "llm_cache_ttl", 600),
            max_size=getattr(s, "llm_cache_max_size", 1000),
            similarity_threshold=getattr(s, "llm_cache_similarity_threshold", 0.95),
        )
    return _global_cache
