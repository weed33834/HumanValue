"""文本处理与算法工具库 (M18 底层基础能力)

关键词提取 (TF-IDF + TextRank) / 归一化 / 摘要 / 去重。纯 Python + 标准库。
"""

from __future__ import annotations

import hashlib
import html
import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u202a-\u202e\ufeff]")
_HTML_TAG = re.compile(r"<[^>]+>")
_TOKEN_RE = re.compile(r"[\u4e00-\u9fa5]+|[a-zA-Z][a-zA-Z0-9_]*|\d+(?:\.\d+)?")

_DEFAULT_STOPWORDS = frozenset(
    """的了我和也不就是在有这那都对于为与及等很么可以没有我们你们他们一个起来之而
    上上下中内同更最并但或因非常以及到还只已经被把让会能要要再与其然而着吧吗呢啊
    嗯哦嗯这个那个这些那些这样那样什么怎么如何什么什么请问是否可能可以应该需要
    关于相关根据通过作为利用按照因为由于如果那么因此所以然而不过例如比如还有其他""".split()
)


def normalize_text(text: str) -> str:
    """归一化: 去 HTML / 全半角 / 去零宽 / 空白折叠。"""
    if not text:
        return ""
    t = _HTML_TAG.sub(" ", text)
    t = html.unescape(t)
    t = unicodedata.normalize("NFKC", t)
    t = _ZERO_WIDTH.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def _bigram_tokens(text: str) -> List[str]:
    """中文 bigram 分词: 汉字切二元组, 其他按词。"""
    out: List[str] = []
    for t in _TOKEN_RE.findall(text or ""):
        if re.fullmatch(r"[\u4e00-\u9fa5]+", t):
            out.extend(t[i : i + 2] for i in range(max(1, len(t) - 1)))
        else:
            out.append(t.lower())
    return out


def extract_keywords_tfidf(text, top_k=5, stopwords=None) -> List[Dict[str, float]]:
    tokens = _bigram_tokens(normalize_text(text))
    stop = set(_DEFAULT_STOPWORDS) | set(stopwords or set())
    filtered = [t for t in tokens if t not in stop]
    if not filtered:
        return []
    counter = Counter(filtered)
    total = len(filtered)
    scored = []
    for word, freq in counter.items():
        weight = (freq / total) * (1.0 + math.log(max(total, 1) / (freq + 1)))
        if len(word) == 1:
            weight *= 0.5
        scored.append((word, weight))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [{"word": w, "weight": round(s, 6)} for w, s in scored[:top_k]]


def extract_keywords_textrank(
    text, top_k=5, window=5, stopwords=None, damping=0.85, max_iter=100
) -> List[Dict[str, float]]:
    tokens = _bigram_tokens(normalize_text(text))
    stop = set(_DEFAULT_STOPWORDS) | set(stopwords or set())
    filtered = [t for t in tokens if t not in stop]
    if not filtered:
        return []
    adj = defaultdict(lambda: defaultdict(int))
    nodes = set(filtered)
    for i, w in enumerate(filtered):
        for j in range(i + 1, min(i + window + 1, len(filtered))):
            w2 = filtered[j]
            if w != w2:
                adj[w][w2] += 1
                adj[w2][w] += 1
    scores = {n: 1.0 for n in nodes}
    for _ in range(max_iter):
        new = {}
        delta = 0.0
        for n in nodes:
            neigh = adj[n]
            total_out = sum(neigh.values()) or 1.0
            s = (1 - damping) + damping * sum(
                scores[nb] * (c / total_out) for nb, c in neigh.items()
            )
            new[n] = s
            delta += abs(s - scores[n])
        scores = new
        if delta < 1e-6:
            break
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{"word": w, "weight": round(s, 6)} for w, s in ranked[:top_k]]


def extract_keywords(
    text, top_k=5, method="hybrid", stopwords=None
) -> List[Dict[str, float]]:
    if method == "tfidf":
        return extract_keywords_tfidf(text, top_k, stopwords)
    if method == "textrank":
        return extract_keywords_textrank(text, top_k, stopwords=stopwords)
    tf = {
        r["word"]: r["weight"]
        for r in extract_keywords_tfidf(text, top_k * 2, stopwords)
    }
    tr = {
        r["word"]: r["weight"]
        for r in extract_keywords_textrank(text, top_k * 2, stopwords=stopwords)
    }
    merged = defaultdict(float)
    for w, s in tf.items():
        merged[w] += s
    for w, s in tr.items():
        merged[w] += s
    ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    return [{"word": w, "weight": round(s, 6)} for w, s in ranked[:top_k]]


def summarize_extractive(text, max_sentences=3, stopwords=None) -> str:
    clean = normalize_text(text)
    if not clean:
        return ""
    if len(clean) <= 300:
        return re.split(r"(?<=[。！？!?])", clean)[0].strip()[:300]
    sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])", clean) if s.strip()]
    if not sentences:
        return clean[:300]
    if len(sentences) <= max_sentences:
        return "".join(sentences)
    freq = Counter(_bigram_tokens(clean))
    stop = set(_DEFAULT_STOPWORDS) | set(stopwords or set())
    scored = []
    for idx, s in enumerate(sentences):
        toks = [t for t in _bigram_tokens(s) if t not in stop]
        score = sum(freq.get(t, 0) for t in toks) * (
            1.0 + 0.2 * (1 - idx / len(sentences))
        )
        if len(s) < 8 or len(s) > 120:
            score *= 0.6
        scored.append((idx, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    top_idx = sorted(i for i, _ in scored[:max_sentences])
    return "".join(sentences[i] for i in top_idx)


def fingerprint(text: str) -> str:
    return hashlib.md5(normalize_text(text).encode("utf-8")).hexdigest()


def _shingles(text: str, size: int) -> set:
    norm = re.sub(r"\s+", "", text)
    return (
        {norm}
        if len(norm) <= size
        else {norm[i : i + size] for i in range(len(norm) - size + 1)}
    )


def _jaccard(a: set, b: set) -> float:
    union = a | b
    return 0.0 if not union else len(a & b) / len(union)


def text_dedup(
    texts: Sequence[str], shingle_size: int = 3, threshold: float = 0.6
) -> List[str]:
    seen: set = set()
    kept: List[set] = []
    result: List[str] = []
    for t in texts:
        norm = normalize_text(t)
        if not norm:
            continue
        fp = fingerprint(norm)
        if fp in seen:
            continue
        sh = _shingles(norm, shingle_size)
        if any(_jaccard(sh, k) >= threshold for k in kept):
            continue
        seen.add(fp)
        kept.append(sh)
        result.append(t)
    return result
