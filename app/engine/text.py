"""Text normalisation and resume/JD structure detection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "summary": re.compile(r"^(professional\s+)?(summary|profile|objective|about me)\b", re.I),
    "experience": re.compile(
        r"^(professional\s+|work\s+|relevant\s+)?(experience|employment(\s+history)?|work history)\b", re.I
    ),
    "education": re.compile(r"^education(al background)?\b|^academic", re.I),
    "skills": re.compile(r"^(technical\s+|core\s+|key\s+)?(skills|competencies|technologies|tech stack)\b", re.I),
    "projects": re.compile(r"^(academic\s+|personal\s+|key\s+)?projects?\b", re.I),
    "certifications": re.compile(r"^(certifications?|licenses?)\b", re.I),
}

BULLET_PREFIX = re.compile(r"^\s*(?:[-•*▪●◦‣–—]|\d+[.)])\s+")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
LINKEDIN = re.compile(r"linkedin\.com/in/[\w-]+", re.I)
GITHUB = re.compile(r"github\.com/[\w-]+", re.I)


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


@dataclass
class ResumeStructure:
    sections: dict[str, list[str]] = field(default_factory=dict)
    bullets: list[str] = field(default_factory=list)
    has_email: bool = False
    has_phone: bool = False
    has_linkedin: bool = False
    has_github: bool = False
    word_count: int = 0


def _section_for(line: str) -> str | None:
    candidate = line.strip().strip(":").strip()
    if not candidate or len(candidate) > 40:
        return None
    for name, pattern in SECTION_PATTERNS.items():
        if pattern.match(candidate):
            return name
    return None


def parse_resume(text: str) -> ResumeStructure:
    text = normalize(text)
    s = ResumeStructure(
        has_email=bool(EMAIL.search(text)),
        has_phone=bool(PHONE.search(text)),
        has_linkedin=bool(LINKEDIN.search(text)),
        has_github=bool(GITHUB.search(text)),
        word_count=len(re.findall(r"\b\w+\b", text)),
    )
    current = "header"
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        section = _section_for(line)
        if section:
            current = section
            s.sections.setdefault(current, [])
            continue
        s.sections.setdefault(current, []).append(line)
        if BULLET_PREFIX.match(line):
            s.bullets.append(BULLET_PREFIX.sub("", line).strip())
        elif current in {"experience", "projects"} and len(line.split()) >= 6 and not _looks_like_title(line):
            # Some exports drop bullet glyphs; treat sentence-like lines in experience as bullets.
            s.bullets.append(line)
    return s


_DATE_HINT = re.compile(r"\b(19|20)\d{2}\b|\bpresent\b|\bcurrent\b", re.I)


def _looks_like_title(line: str) -> bool:
    """Job titles / company lines are short or carry dates and pipes rather than verbs."""
    return bool(_DATE_HINT.search(line)) and len(line.split()) <= 12 or "|" in line


# --------------------------------------------------------------------- job description tiers

REQUIRED_HEADERS = re.compile(
    r"(required|requirements|must[- ]have|minimum qualifications|basic qualifications|what you('ll)? need|"
    r"qualifications|you have|who you are|what we're looking for)",
    re.I,
)
PREFERRED_HEADERS = re.compile(
    r"(preferred|nice[- ]to[- ]have|bonus|plus|desired|good to have|additional qualifications|"
    r"preferred qualifications)",
    re.I,
)
OTHER_HEADERS = re.compile(
    r"^(about (us|the (company|team|role))|benefits|perks|what we offer|compensation|responsibilities|"
    r"what you('ll)? do|the role|equal opportunity)",
    re.I,
)


def split_job_description(text: str) -> dict[str, str]:
    """Split a JD into required / preferred / other text using its headings.

    Lines without a recognised heading default to "other"; inline cues such as
    "(preferred)" or "is a plus" move a single line to the preferred tier.
    """
    tiers: dict[str, list[str]] = {"required": [], "preferred": [], "other": []}
    current = "other"
    for raw in normalize(text).split("\n"):
        line = raw.strip()
        if not line:
            continue
        stripped = BULLET_PREFIX.sub("", line).strip()
        is_heading = len(stripped) <= 60 and (stripped.endswith(":") or not BULLET_PREFIX.match(line))
        if is_heading and len(stripped.split()) <= 7:
            if PREFERRED_HEADERS.search(stripped):
                current = "preferred"
                continue
            if REQUIRED_HEADERS.search(stripped):
                current = "required"
                continue
            if OTHER_HEADERS.search(stripped):
                current = "other"
                continue
        tier = current
        if re.search(r"\b(preferred|is a plus|a plus|nice to have|bonus)\b", stripped, re.I):
            tier = "preferred"
        elif re.search(r"\b(required|must have|must be|mandatory)\b", stripped, re.I):
            tier = "required"
        tiers[tier].append(stripped)
    return {k: "\n".join(v) for k, v in tiers.items()}


# ---------------------------------------------------------------------- years of experience

_MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
_RANGE = re.compile(
    rf"(?:(?:{_MONTHS})[a-z]*\.?\s+)?((?:19|20)\d{{2}})\s*(?:-|–|—|to)\s*"
    rf"(?:(?:(?:{_MONTHS})[a-z]*\.?\s+)?((?:19|20)\d{{2}})|(present|current|now|today))",
    re.I,
)
_REQUIRED_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:-\s*\d{1,2}\s*)?(?:years?|yrs?)", re.I)


def estimate_years_experience(experience_lines: list[str], current_year: int) -> float | None:
    """Merge employment date ranges from the experience section into total years."""
    spans: list[tuple[int, int]] = []
    for line in experience_lines:
        for m in _RANGE.finditer(line):
            start = int(m.group(1))
            end = current_year if m.group(3) else int(m.group(2))
            if 1970 <= start <= end <= current_year:
                spans.append((start, end))
    if not spans:
        return None
    spans.sort()
    merged = [spans[0]]
    for start, end in spans[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return float(sum(max(end - start, 0.5) for start, end in merged))


def required_years(job_text: str) -> int | None:
    """Smallest 'N+ years' requirement mentioned in the job description, if any."""
    found = [int(n) for n in _REQUIRED_YEARS.findall(job_text) if 0 < int(n) <= 20]
    return min(found) if found else None
