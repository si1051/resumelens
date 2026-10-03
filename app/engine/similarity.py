"""Keyword similarity between resume and JD, plus important JD terms the resume lacks."""

from __future__ import annotations

import math
import re
from collections import Counter

try:  # scikit-learn gives better tokenisation and n-grams when available
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as _SK_STOP
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:  # pragma: no cover - exercised only without sklearn
    TfidfVectorizer = None
    _SK_STOP = frozenset()

_EXTRA_STOP = {
    "experience", "work", "working", "team", "teams", "years", "year", "ability", "strong", "skills",
    "knowledge", "including", "role", "candidate", "job", "position", "company", "using", "use", "plus",
    "preferred", "required", "requirements", "responsibilities", "qualifications", "excellent", "good",
    "understanding", "new", "build", "building", "help", "looking", "join", "opportunity", "will", "able",
    "related", "field", "degree", "bachelor", "master", "equivalent", "etc", "similar", "environment",
    "across", "within", "make", "high", "quality", "solutions", "solution", "business", "best",
    # common job-posting filler that says nothing about the actual stack
    "professional", "designing", "design", "hands", "habits", "tooling", "tools", "developing", "develop",
    "implementing", "implement", "writing", "write", "proven", "familiarity", "familiar", "exposure", "deep",
    "passion", "passionate", "fast", "paced", "collaborative", "communication", "written", "verbal", "problem",
    "solving", "minimum", "nice", "technical", "technologies", "technology", "software", "engineering",
    "engineer", "engineers", "systems", "services", "applications", "application", "platform", "production",
    "scale", "large", "modern", "world", "class", "hands-on", "self", "starter", "growth", "impact",
}
STOP_WORDS = frozenset(_SK_STOP) | _EXTRA_STOP
_TOKEN = re.compile(r"[a-z][a-z0-9+#.]*[a-z0-9+#]|[a-z]")


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOP_WORDS and len(t) > 1]


def cosine_similarity(a: str, b: str) -> float:
    """Cosine similarity of TF-IDF vectors (0..1)."""
    if not a.strip() or not b.strip():
        return 0.0
    if TfidfVectorizer is not None:
        vec = TfidfVectorizer(stop_words=list(STOP_WORDS), ngram_range=(1, 2), sublinear_tf=True,
                              token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9+#.]*[a-zA-Z0-9+#]\b")
        try:
            m = vec.fit_transform([a, b])
        except ValueError:  # empty vocabulary
            return 0.0
        return float((m[0] @ m[1].T).toarray()[0][0])
    ca, cb = Counter(_tokens(a)), Counter(_tokens(b))
    dot = sum(ca[t] * cb[t] for t in ca.keys() & cb.keys())
    norm = math.sqrt(sum(v * v for v in ca.values())) * math.sqrt(sum(v * v for v in cb.values()))
    return dot / norm if norm else 0.0


def missing_keywords(resume: str, job: str, exclude: set[str], limit: int = 10) -> list[str]:
    """Most frequent meaningful JD terms that never appear in the resume."""
    resume_tokens = set(_tokens(resume))
    resume_lower = resume.lower()
    counts = Counter(_tokens(job))
    out = []
    for term, _ in counts.most_common():
        if term in resume_tokens or term in exclude or term in resume_lower or len(term) < 3:
            continue
        out.append(term)
        if len(out) >= limit:
            break
    return out
