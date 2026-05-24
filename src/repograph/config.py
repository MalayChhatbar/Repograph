"""Configuration helpers for RepoGraph."""

from __future__ import annotations

from pathlib import Path

DEFAULT_DB_NAME = ".repograph.db"
DEFAULT_IGNORES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".next",
    "coverage",
}


def default_database_path(root: Path) -> Path:
    return root / DEFAULT_DB_NAME

