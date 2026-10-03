"""Runtime settings, read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _csv(name: str, default: str) -> list[str]:
    return [v.strip() for v in os.getenv(name, default).split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    cors_origins: list[str]
    max_upload_bytes: int
    max_text_chars: int
    rate_limit_per_minute: int


def get_settings() -> Settings:
    return Settings(
        cors_origins=_csv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024))),
        max_text_chars=int(os.getenv("MAX_TEXT_CHARS", "50000")),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
    )
