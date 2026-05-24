from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from repograph.cli import app
from repograph.core import RepoGraphService

runner = CliRunner()


def _prepare_repo(root: Path, db_root: Path) -> None:
    service = RepoGraphService(root, db_path=db_root / ".repograph.db")
    service.index()


def test_index_command(sample_repo_root: Path, tmp_path: Path) -> None:
    result = runner.invoke(app, ["index", str(sample_repo_root)])
    assert result.exit_code == 0
    assert "Indexed repository" in result.stdout


def test_summary_command(sample_repo_root: Path) -> None:
    runner.invoke(app, ["index", str(sample_repo_root)])
    result = runner.invoke(app, ["summary", str(sample_repo_root)])
    assert result.exit_code == 0
    assert "RepoGraph Summary" in result.stdout


def test_search_command(sample_repo_root: Path) -> None:
    runner.invoke(app, ["index", str(sample_repo_root)])
    result = runner.invoke(app, ["search", "create", str(sample_repo_root)])
    assert result.exit_code == 0
    assert "src/services/user_service.py" in result.stdout


def test_impact_command(sample_repo_root: Path) -> None:
    runner.invoke(app, ["index", str(sample_repo_root)])
    result = runner.invoke(app, ["impact", "src/services/user_service.py", str(sample_repo_root)])
    assert result.exit_code == 0
    assert "Risk score" in result.stdout


def test_routes_command(sample_repo_root: Path) -> None:
    runner.invoke(app, ["index", str(sample_repo_root)])
    result = runner.invoke(app, ["routes", str(sample_repo_root)])
    assert result.exit_code == 0
    assert "/users" in result.stdout


def test_dead_code_command(sample_repo_root: Path) -> None:
    runner.invoke(app, ["index", str(sample_repo_root)])
    result = runner.invoke(app, ["dead-code", str(sample_repo_root)])
    assert result.exit_code == 0
    assert "Potential Dead Code" in result.stdout


def test_explain_command(sample_repo_root: Path) -> None:
    runner.invoke(app, ["index", str(sample_repo_root)])
    result = runner.invoke(app, ["explain", "src/api/users.py", str(sample_repo_root)])
    assert result.exit_code == 0
    assert "Symbols:" in result.stdout


def test_cycles_command(cycle_repo_root: Path) -> None:
    runner.invoke(app, ["index", str(cycle_repo_root)])
    result = runner.invoke(app, ["cycles", str(cycle_repo_root)])
    assert result.exit_code == 0
    assert "Cycle 1" in result.stdout


def test_pr_risk_command(sample_repo_root: Path, monkeypatch) -> None:
    runner.invoke(app, ["index", str(sample_repo_root)])
    monkeypatch.setattr("repograph.core.RepoGraphService._changed_files", lambda self, rr: ["src/services/user_service.py"])
    monkeypatch.setattr("repograph.core.RepoGraphService._git_churn", lambda self, p: 2)
    result = runner.invoke(app, ["pr-risk", "main..HEAD", str(sample_repo_root)])
    assert result.exit_code == 0
    assert "Suggested tests:" in result.stdout
