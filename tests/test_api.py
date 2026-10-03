import io

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "UP"
    assert "X-Request-ID" in r.headers


def test_analyze_text(resume, job):
    r = client.post("/api/v1/analyze", json={"resume_text": resume, "job_description": job})
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["overall_score"] <= 100
    assert "kubernetes" in body["skills"]["missing_required"]


def test_validation_rejects_short_input():
    r = client.post("/api/v1/analyze", json={"resume_text": "short", "job_description": "short"})
    assert r.status_code == 422


def test_analyze_txt_upload(resume, job):
    files = {"resume": ("resume.txt", io.BytesIO(resume.encode()), "text/plain")}
    r = client.post("/api/v1/analyze/file", files=files, data={"job_description": job})
    assert r.status_code == 200
    assert r.json()["grade"] in {"A", "B", "C", "D", "F"}


def test_rejects_unsupported_file(job):
    files = {"resume": ("resume.png", io.BytesIO(b"\x89PNG...."), "image/png")}
    r = client.post("/api/v1/analyze/file", files=files, data={"job_description": job})
    assert r.status_code == 415


def test_skill_extraction_endpoint():
    r = client.post("/api/v1/skills/extract", json={"text": "Java, Spring Boot, k8s"})
    assert r.status_code == 200
    assert set(r.json()["skills"]) == {"java", "spring boot", "kubernetes"}


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "ResumeLens" in r.text
