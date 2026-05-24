from __future__ import annotations

from pathlib import Path

from repograph.core import RepoGraphService


def test_index_and_summary(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    service = RepoGraphService(fixture_root, db_path=tmp_path / "graph.db")
    service.index()

    summary = service.summary()
    assert summary.total_files == 4
    assert summary.languages["python"] == 4
    assert summary.routes == 2
    assert summary.symbols >= 4


def test_impact_detects_dependents_and_tests(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    service = RepoGraphService(fixture_root, db_path=tmp_path / "graph.db")
    service.index()

    impact = service.impact("src/services/user_service.py")
    assert "src/api/users.py" in impact.direct_dependents
    assert any(link.test_path == "tests/api/test_users.py" for link in impact.related_tests)
    assert impact.risk_score > 0


def test_cycles_empty_for_fixture(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    service = RepoGraphService(fixture_root, db_path=tmp_path / "graph.db")
    service.index()

    assert service.cycles() == []


def test_routes_and_dead_code(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    service = RepoGraphService(fixture_root, db_path=tmp_path / "graph.db")
    service.index()

    routes = service.routes()
    dead_code = service.dead_code()

    assert len(routes) == 2
    assert any(item["qualified_name"].endswith(":create_user_route") for item in dead_code)
