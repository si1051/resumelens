"""Scores resume bullets the way a recruiter skims them: verb, impact, specificity, length."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

STRONG_VERBS = {
    "accelerated", "achieved", "architected", "automated", "boosted", "built", "championed", "consolidated",
    "created", "cut", "debugged", "decreased", "delivered", "deployed", "designed", "developed", "drove",
    "eliminated", "engineered", "enhanced", "established", "expanded", "implemented", "improved", "increased",
    "integrated", "introduced", "launched", "led", "migrated", "modernized", "optimized", "orchestrated",
    "overhauled", "owned", "pioneered", "reduced", "refactored", "resolved", "revamped", "scaled",
    "secured", "shipped", "simplified", "spearheaded", "streamlined", "transformed", "tuned", "upgraded",
    "mentored", "coordinated", "analyzed", "configured", "containerized", "instrumented", "wrote", "partnered",
    "collaborated", "authored", "standardized", "accelerating", "trained", "maintained", "tested", "translated",
}
WEAK_STARTS = {"responsible", "helped", "assisted", "worked", "involved", "participated", "tasked", "duties",
               "handled", "did", "was", "were", "has", "had", "in", "the"}
WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "assisted in", "involved in", "duties included",
    "participated in", "various", "etc", "team player", "hard working", "hardworking",
]
METRIC = re.compile(
    r"(\d+(?:\.\d+)?\s?(?:%|percent|x\b|k\b|m\b|ms\b|s\b|hrs?\b|hours\b|days\b|users\b|customers\b|requests\b))"
    r"|(\$\s?\d)|(\b\d{2,}(?:,\d{3})*\b)",
    re.I,
)
PRONOUN = re.compile(r"^\s*(i|we|my|our)\b", re.I)


@dataclass
class BulletReport:
    text: str
    score: int
    strengths: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def score_bullet(text: str) -> BulletReport:
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    first = words[0].lower() if words else ""
    lower = text.lower()
    score = 40
    strengths: list[str] = []
    issues: list[str] = []

    if first in STRONG_VERBS or (first.endswith("ed") and first not in WEAK_STARTS and len(first) > 4):
        score += 20
        strengths.append("Starts with an action verb")
    elif first in WEAK_STARTS:
        score -= 10
        issues.append(f'Starts weakly ("{words[0]}"); lead with what you did, e.g. "Built", "Reduced".')
    else:
        issues.append("Start with a strong past-tense action verb.")

    if METRIC.search(text):
        score += 25
        strengths.append("Quantifies impact")
    else:
        issues.append("Add a number: %, time saved, users, revenue, latency, scale.")

    found_weak = [p for p in WEAK_PHRASES if re.search(rf"\b{re.escape(p)}\b", lower)]
    if found_weak:
        score -= 10 * len(found_weak)
        issues.append(f"Replace vague phrasing: {', '.join(found_weak)}.")

    n = len(words)
    if n < 8:
        score -= 10
        issues.append("Too short to show scope; add the tool used and the result.")
    elif n > 35:
        score -= 10
        issues.append("Too long; keep bullets to one or two lines.")
    else:
        score += 10

    if PRONOUN.match(text):
        score -= 5
        issues.append("Drop first-person pronouns.")

    if re.search(r"\b(using|with|via|leveraging)\b", lower):
        score += 5
        strengths.append("Names the tools or method")

    return BulletReport(text=text, score=max(0, min(100, score)), strengths=strengths, issues=issues)


def score_bullets(bullets: list[str]) -> tuple[int, list[BulletReport]]:
    reports = [score_bullet(b) for b in bullets if b.strip()]
    if not reports:
        return 0, []
    avg = round(sum(r.score for r in reports) / len(reports))
    return avg, reports
