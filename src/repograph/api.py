"""FastAPI application for RepoGraph."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from repograph.core import RepoGraphService


def create_app(root: Path | None = None) -> FastAPI:
    repo_root = (root or Path.cwd()).resolve()
    service = RepoGraphService(repo_root)
    app = FastAPI(title="RepoGraph API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/index")
    def index() -> dict[str, str]:
        service.index()
        return {"status": "indexed"}

    @app.get("/summary")
    def summary():
        return service.summary()

    @app.get("/search")
    def search(query: str):
        return service.search(query)

    @app.get("/impact/{file_path:path}")
    def impact(file_path: str):
        return service.impact(file_path)

    @app.get("/cycles")
    def cycles():
        return service.cycles()

    @app.get("/routes")
    def routes():
        return service.routes()

    @app.get("/dead-code")
    def dead_code():
        return service.dead_code()

    @app.get("/explain/{file_path:path}")
    def explain(file_path: str):
        details = service.explain(file_path)
        if not details.symbols and not details.imports and not details.routes and not details.related_tests:
            raise HTTPException(status_code=404, detail="File not indexed")
        return details

    @app.get("/pr-risk")
    def pr_risk(revision_range: str):
        return service.pr_risk(revision_range)

    return app


app = create_app()
