"""Request/response models (Pydantic v2)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=50, max_length=50_000, description="Plain-text resume")
    job_description: str = Field(min_length=50, max_length=50_000, description="Full job posting text")


class SkillsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)


class Suggestion(BaseModel):
    priority: str
    area: str
    message: str


class BulletOut(BaseModel):
    text: str
    score: int
    strengths: list[str]
    issues: list[str]


class AnalyzeResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    grade: str
    breakdown: dict[str, dict]
    skills: dict
    keywords: dict
    experience: dict
    ats: dict
    bullets: dict
    suggestions: list[Suggestion]


class SkillsResponse(BaseModel):
    skills: dict[str, int]
    by_category: dict[str, list[str]]
