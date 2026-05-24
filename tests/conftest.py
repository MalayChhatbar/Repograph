from __future__ import annotations

from pathlib import Path

import pytest

from repograph.core import RepoGraphService


@pytest.fixture()
def sample_repo_root() -> Path:
    return Path("tests/fixtures/sample_repo").resolve()


@pytest.fixture()
def cycle_repo_root() -> Path:
    return Path("tests/fixtures/cycle_repo").resolve()


@pytest.fixture()
def js_repo_root() -> Path:
    return Path("tests/fixtures/js_repo").resolve()


@pytest.fixture()
def indexed_sample_service(sample_repo_root: Path, tmp_path: Path) -> RepoGraphService:
    service = RepoGraphService(sample_repo_root, db_path=tmp_path / "graph.db")
    service.index()
    return service
