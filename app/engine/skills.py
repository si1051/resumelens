"""Boundary-aware skill extraction against the curated taxonomy."""

from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache

from .taxonomy import ALIAS_TO_SKILL, AMBIGUOUS_ALIASES, SKILL_CATEGORY

_LIST_PUNCT = set(",/|()•;:·[]")
_EDGE = r"A-Za-z0-9+#"


@lru_cache(maxsize=1)
def _compiled_aliases() -> list[tuple[str, str, re.Pattern[str]]]:
    # Longest aliases first so "spring boot" wins over "spring", "node.js" over "js".
    aliases = sorted(ALIAS_TO_SKILL.items(), key=lambda kv: len(kv[0]), reverse=True)
    out = []
    for alias, skill in aliases:
        pattern = re.compile(rf"(?<![{_EDGE}]){re.escape(alias)}(?![{_EDGE}])", re.I)
        out.append((alias, skill, pattern))
    return out


def _in_list_context(text: str, start: int, end: int) -> bool:
    """True when a match sits in a comma/slash/bullet separated list, e.g. 'Java, Go, Rust'."""
    before = text[max(0, start - 3):start]
    after = text[end:end + 3]
    return any(ch in _LIST_PUNCT for ch in before + after) or text[max(0, start - 1):start] == "\n"


def extract_skills(text: str) -> Counter[str]:
    """Return canonical skill -> mention count."""
    if not text:
        return Counter()
    working = text
    counts: Counter[str] = Counter()
    for alias, skill, pattern in _compiled_aliases():
        matches = list(pattern.finditer(working))
        if not matches:
            continue
        kept = [m for m in matches
                if alias not in AMBIGUOUS_ALIASES or _in_list_context(working, m.start(), m.end())]
        if kept:
            counts[skill] += len(kept)
        # Mask every match so shorter aliases can't re-match inside it.
        for m in reversed(kept):
            working = working[:m.start()] + " " * (m.end() - m.start()) + working[m.end():]
    return counts


def categorize(skills: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for s in sorted(skills):
        grouped.setdefault(SKILL_CATEGORY.get(s, "other"), []).append(s)
    return grouped
