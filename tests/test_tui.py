from __future__ import annotations

import asyncio
from pathlib import Path

from repograph.core import RepoGraphService
from repograph.tui import RepoGraphApp


def test_tui_mounts_and_renders_overview(sample_repo_root: Path, tmp_path: Path) -> None:
    async def run() -> None:
        service = RepoGraphService(sample_repo_root, db_path=tmp_path / "graph.db")
        service.index()
        app = RepoGraphApp(service=service, initial_focus="src/api/users.py")

        async with app.run_test() as pilot:
            await pilot.pause()
            overview = app.query_one("#overview-view")
            assert "Files:" in str(overview.renderable)
            graph = app.query_one("#graph-view")
            assert "Center: src/api/users.py" in str(graph.renderable)

    asyncio.run(run())


def test_tui_refreshes_after_focus_change(sample_repo_root: Path, tmp_path: Path) -> None:
    async def run() -> None:
        service = RepoGraphService(sample_repo_root, db_path=tmp_path / "graph.db")
        service.index()
        app = RepoGraphApp(service=service, initial_focus="src/api/users.py")

        async with app.run_test() as pilot:
            app.current_focus = "src/services/user_service.py"
            app.refresh_snapshot()
            await pilot.pause()
            impact = app.query_one("#impact-view")
            assert "src/services/user_service.py" in str(impact.renderable)

    asyncio.run(run())
