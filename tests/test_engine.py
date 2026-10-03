import datetime as dt

from app.engine import analyze
from app.engine.bullets import score_bullet
from app.engine.skills import extract_skills
from app.engine.text import (
    estimate_years_experience,
    parse_resume,
    required_years,
    split_job_description,
)

TODAY = dt.date(2026, 6, 1)


class TestSkillExtraction:
    def test_aliases_map_to_canonical_names(self):
        found = extract_skills("Deployed on k8s with Postgres, wrote TypeScript and node.js services")
        assert {"kubernetes", "postgresql", "typescript", "node.js"} <= set(found)

    def test_java_is_not_found_inside_javascript(self):
        found = extract_skills("Senior JavaScript developer")
        assert "javascript" in found
        assert "java" not in found

    def test_symbols_in_skill_names(self):
        found = extract_skills("Languages: C++, C#, .NET")
        assert {"c++", "c#", ".net"} <= set(found)

    def test_ambiguous_words_need_list_context(self):
        assert "go" in extract_skills("Languages: Java, Go, Rust")
        assert "go" not in extract_skills("We go to market quickly")

    def test_longer_alias_wins(self):
        found = extract_skills("Spring Boot")
        assert "spring boot" in found
        assert "spring" not in found


class TestStructure:
    def test_sections_contacts_and_bullets(self, resume):
        s = parse_resume(resume)
        assert {"experience", "education", "skills", "summary"} <= set(s.sections)
        assert s.has_email and s.has_phone and s.has_github
        assert len(s.bullets) == 5

    def test_job_description_tiers(self, job):
        tiers = split_job_description(job)
        assert "Kubernetes" in tiers["required"]
        assert "Terraform" in tiers["preferred"]
        assert "Health insurance" in tiers["other"]

    def test_inline_preferred_cue(self):
        tiers = split_job_description("Requirements:\n- Java\n- AWS experience is a plus")
        assert "AWS" in tiers["preferred"]
        assert "Java" in tiers["required"]

    def test_years_merge_overlapping_ranges(self):
        lines = ["Engineer | 2018 - 2021", "Lead | Mar 2020 - Present", "Intern | 2015 to 2016"]
        assert estimate_years_experience(lines, 2026) == 9.0

    def test_required_years(self):
        assert required_years("5+ years Java, 3+ years cloud") == 3
        assert required_years("No experience needed") is None


class TestBullets:
    def test_strong_bullet_scores_high(self):
        r = score_bullet("Reduced API latency by 40% by adding Redis caching using Spring Cache")
        assert r.score >= 85
        assert "Quantifies impact" in r.strengths

    def test_weak_bullet_scores_low_with_advice(self):
        r = score_bullet("Responsible for various tasks")
        assert r.score < 40
        assert any("vague" in i.lower() for i in r.issues)


class TestAnalyze:
    def test_good_match_scores_well_and_flags_gaps(self, resume, job):
        a = analyze(resume, job, today=TODAY)
        assert 60 <= a.overall_score <= 100
        assert "kubernetes" in a.skills["missing_required"]
        assert "terraform" in a.skills["missing_preferred"]
        assert {"java", "spring boot", "postgresql"} <= set(a.skills["matched"])
        assert a.experience["required_years"] == 3
        assert a.experience["estimated_years"] >= 5
        assert any(s.area == "skills" and s.priority == "high" for s in a.suggestions)

    def test_unrelated_resume_is_capped(self, job):
        resume = ("Jane Doe jane@example.com 555-123-4567\nExperience\n"
                  "- Managed retail store operations and staff scheduling for 12 employees\n"
                  "Skills\nCustomer service, Excel\nEducation\nBA History 2019")
        a = analyze(resume, job, today=TODAY)
        assert a.overall_score <= 60
        assert a.grade in {"C", "D", "F"}

    def test_breakdown_weights_sum_to_one(self, resume, job):
        a = analyze(resume, job, today=TODAY)
        assert abs(sum(p["weight"] for p in a.breakdown.values()) - 1.0) < 1e-9

    def test_serializable(self, resume, job):
        import json

        json.dumps(analyze(resume, job, today=TODAY).to_dict())
