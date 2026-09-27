"""
Lightweight, dependency-free similarity scoring for the prototype.

This intentionally uses simple lexical overlap (Jaccard over stemmed-ish
tokens) rather than a real embedding model, so the scaffold runs with no
GPU/API dependency. Swap `score()` for a real embedding call (e.g. the
Anthropic API or a local sentence-transformer) before this leaves demo
status — see README.md.
"""

import re

_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "with",
    "by", "is", "are", "that", "this", "as", "from", "using", "based",
    "into", "each", "such", "than", "when", "while", "not", "be", "at",
}


def _tokens(text: str) -> set:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return round(inter / union, 4) if union else 0.0


def best_matches(query_text: str, patents: list, top_k: int = 3, min_score: float = 0.08):
    """Return the top_k seed patents most lexically similar to query_text."""
    scored = []
    for p in patents:
        combined = f"{p['title']} {p['abstract']}"
        s = jaccard(query_text, combined)
        if s >= min_score:
            scored.append((s, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]
