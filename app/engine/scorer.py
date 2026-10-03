"""Combines the individual signals into one explainable score with prioritised advice."""

from __future__ import annotations

import datetime as _dt
from dataclasses import asdict, dataclass, field

from .bullets import score_bullets
from .similarity import cosine_similarity, missing_keywords
from .skills import categorize, extract_skills
from .taxonomy import ALIAS_TO_SKILL
from .text import estimate_years_experience, normalize, parse_resume, required_years, split_job_description

WEIGHTS = {
    "required_skills": 0.40,
    "keyword_similarity": 0.20,
    "preferred_skills": 0.10,
    "bullet_quality": 0.15,
    "ats_readiness": 0.10,
    "experience_fit": 0.05,
}
SIMILARITY_CEILING = 0.35  # cosine this high already means a very close match for resume vs JD


@dataclass
class Suggestion:
    priority: str  # high | medium | low
    area: str
    message: str


@dataclass
class Analysis:
    overall_score: int
    grade: str
    breakdown: dict[str, dict]
    skills: dict
    keywords: dict
    experience: dict
    ats: dict
    bullets: dict
    suggestions: list[Suggestion] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _grade(score: int) -> str:
    for cutoff, letter in ((85, "A"), (70, "B"), (55, "C"), (40, "D")):
        if score >= cutoff:
            return letter
    return "F"


def _coverage(have: set[str], need: set[str]) -> float | None:
    return None if not need else len(have & need) / len(need)


def analyze(resume_text: str, job_description: str, today: _dt.date | None = None) -> Analysis:
    today = today or _dt.date.today()
    resume_text = normalize(resume_text)
    job_description = normalize(job_description)

    structure = parse_resume(resume_text)
    tiers = split_job_description(job_description)

    resume_skills = set(extract_skills(resume_text))
    required = set(extract_skills(tiers["required"]))
    preferred = set(extract_skills(tiers["preferred"])) - required
    other = set(extract_skills(tiers["other"])) - required - preferred
    if not required:
        # JD without clear headings: treat everything it names as required.
        required, other = required | other, set()

    req_cov = _coverage(resume_skills, required)
    pref_cov = _coverage(resume_skills, preferred)
    similarity = cosine_similarity(resume_text, job_description)

    bullet_avg, bullet_reports = score_bullets(structure.bullets)

    # ATS readiness: can a parser find what recruiters filter on?
    ats_checks = {
        "email": structure.has_email,
        "phone": structure.has_phone,
        "experience_section": "experience" in structure.sections,
        "education_section": "education" in structure.sections,
        "skills_section": "skills" in structure.sections,
        "reasonable_length": 250 <= structure.word_count <= 1100,
        "linkedin_or_github": structure.has_linkedin or structure.has_github,
    }
    ats_score = round(100 * sum(ats_checks.values()) / len(ats_checks))

    need_years = required_years(tiers["required"] or job_description)
    have_years = estimate_years_experience(structure.sections.get("experience", []), today.year)
    if need_years is None or have_years is None:
        exp_score = 100 if need_years is None else 60
    else:
        exp_score = 100 if have_years >= need_years else round(100 * have_years / need_years)

    parts = {
        "required_skills": 100 * (req_cov if req_cov is not None else 1.0),
        "keyword_similarity": 100 * min(1.0, similarity / SIMILARITY_CEILING),
        "preferred_skills": 100 * (pref_cov if pref_cov is not None else 1.0),
        "bullet_quality": bullet_avg if bullet_reports else 30,
        "ats_readiness": ats_score,
        "experience_fit": exp_score,
    }
    overall = round(sum(parts[k] * w for k, w in WEIGHTS.items()))
    # A resume missing most must-have skills shouldn't score well on polish alone.
    if req_cov is not None and req_cov < 0.5:
        overall = min(overall, 60)

    missing_required = sorted(required - resume_skills)
    missing_preferred = sorted(preferred - resume_skills)
    keyword_source = "\n".join(t for t in (tiers["required"], tiers["preferred"]) if t) or job_description
    skill_words = {w for alias in ALIAS_TO_SKILL for w in alias.split()}
    gap_keywords = missing_keywords(resume_text, keyword_source, exclude=skill_words, limit=12)

    suggestions = _suggest(missing_required, missing_preferred, gap_keywords, bullet_reports, ats_checks,
                           need_years, have_years)

    return Analysis(
        overall_score=overall,
        grade=_grade(overall),
        breakdown={k: {"score": round(v), "weight": WEIGHTS[k]} for k, v in parts.items()},
        skills={
            "matched": sorted(resume_skills & (required | preferred | other)),
            "missing_required": missing_required,
            "missing_preferred": missing_preferred,
            "required_coverage": None if req_cov is None else round(req_cov * 100),
            "resume_skills_by_category": categorize(list(resume_skills)),
        },
        keywords={"similarity": round(similarity, 3), "missing": gap_keywords},
        experience={"required_years": need_years,
                    "estimated_years": None if have_years is None else round(have_years, 1)},
        ats={"score": ats_score, "checks": ats_checks, "word_count": structure.word_count},
        bullets={
            "count": len(bullet_reports),
            "average_score": bullet_avg,
            "weakest": [asdict(r) for r in sorted(bullet_reports, key=lambda r: r.score)[:5]],
        },
        suggestions=suggestions,
    )


def _suggest(missing_required, missing_preferred, gap_keywords, bullets, ats, need_years, have_years):
    out: list[Suggestion] = []
    if missing_required:
        out.append(Suggestion("high", "skills",
                              f"The posting requires {', '.join(missing_required[:6])}. If you have used them, "
                              "add them to your Skills section and show them in an experience bullet."))
    weak = [b for b in bullets if b.score < 60]
    if weak:
        out.append(Suggestion("high", "bullets",
                              f"{len(weak)} of {len(bullets)} bullets are weak. Lead with an action verb and "
                              "add a measurable result (%, $, time, scale)."))
    no_metric = sum(1 for b in bullets if "Quantifies impact" not in b.strengths)
    if bullets and no_metric / len(bullets) > 0.5:
        out.append(Suggestion("medium", "bullets",
                              "Most bullets have no numbers. Quantify at least one result per role."))
    if not ats["skills_section"]:
        out.append(Suggestion("high", "ats", 'Add a clearly labelled "Skills" section; ATS filters read it first.'))
    if not ats["experience_section"]:
        out.append(Suggestion("high", "ats", 'Use a standard "Experience" heading so parsers find your roles.'))
    if not (ats["email"] and ats["phone"]):
        out.append(Suggestion("high", "ats", "Put your email and phone number in plain text at the top."))
    if not ats["reasonable_length"]:
        out.append(Suggestion("medium", "ats", "Aim for roughly 400 to 900 words (one or two pages)."))
    if not ats["linkedin_or_github"]:
        out.append(Suggestion("low", "ats", "Add your LinkedIn or GitHub URL."))
    if need_years and have_years is not None and have_years < need_years:
        out.append(Suggestion("medium", "experience",
                              f"The role asks for {need_years}+ years; about {have_years:.0f} were detected. "
                              "Count internships, research and freelance work, and include dates for every role."))
    if missing_preferred:
        out.append(Suggestion("low", "skills",
                              f"Nice-to-haves you could mention: {', '.join(missing_preferred[:5])}."))
    if gap_keywords:
        out.append(Suggestion("low", "keywords",
                              "Terms from the posting that never appear in your resume: "
                              f"{', '.join(gap_keywords[:6])}."))
    return out
