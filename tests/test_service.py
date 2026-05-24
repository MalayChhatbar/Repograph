from __future__ import annotations

import subprocess
from pathlib import Path

from repograph.core import RepoGraphService


def test_index_and_summary(indexed_sample_service: RepoGraphService) -> None:
    summary = indexed_sample_service.summary()
    assert summary.total_files == 4
    assert summary.languages["python"] == 4
    assert summary.routes == 2
    assert summary.symbols >= 4


def test_impact_detects_dependents_and_tests(indexed_sample_service: RepoGraphService) -> None:
    impact = indexed_sample_service.impact("src/services/user_service.py")
    assert "src/api/users.py" in impact.direct_dependents
    assert any(link.test_path == "tests/api/test_users.py" for link in impact.related_tests)
    assert impact.risk_score > 0


def test_cycles_empty_for_fixture(indexed_sample_service: RepoGraphService) -> None:
    assert indexed_sample_service.cycles() == []


def test_routes_and_dead_code(indexed_sample_service: RepoGraphService) -> None:
    routes = indexed_sample_service.routes()
    dead_code = indexed_sample_service.dead_code()
    assert len(routes) == 2
    assert any(item["qualified_name"].endswith(":create_user_route") for item in dead_code)


def test_graph_neighborhood(indexed_sample_service: RepoGraphService) -> None:
    graph = indexed_sample_service.graph("src/api/users.py")
    assert graph["center"] == "src/api/users.py"
    assert "src/services/user_service.py" in graph["depends_on"]


def test_cycle_detection_finds_simple_cycle(cycle_repo_root: Path, tmp_path: Path) -> None:
    service = RepoGraphService(cycle_repo_root, db_path=tmp_path / "cycle.db")
    service.index()
    cycles = service.cycles()
    assert cycles
    assert any("src/a.py" in cycle and "src/b.py" in cycle for cycle in cycles)


def test_js_repo_indexing(js_repo_root: Path, tmp_path: Path) -> None:
    service = RepoGraphService(js_repo_root, db_path=tmp_path / "js.db")
    service.index()
    summary = service.summary()
    assert summary.total_files == 3
    assert summary.routes == 2
    assert summary.languages["javascript"] == 3


def test_pr_risk_uses_changed_files_and_suggests_tests(indexed_sample_service: RepoGraphService, monkeypatch) -> None:
    monkeypatch.setattr(indexed_sample_service, "_changed_files", lambda revision_range: ["src/services/user_service.py"])
    monkeypatch.setattr(indexed_sample_service, "_git_churn", lambda path: 2)
    result = indexed_sample_service.pr_risk("main..HEAD")
    assert result["revision_range"] == "main..HEAD"
    assert result["risk_score"] > 0
    assert "tests/api/test_users.py" in result["suggested_tests"]


def test_git_churn_handles_missing_git(indexed_sample_service: RepoGraphService, monkeypatch) -> None:
    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", raise_file_not_found)
    assert indexed_sample_service._git_churn("src/api/users.py") == 0


def test_changed_files_handles_git_errors(indexed_sample_service: RepoGraphService, monkeypatch) -> None:
    class Result:
        returncode = 1
        stdout = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: Result())
    assert indexed_sample_service._changed_files("main..HEAD") == []
