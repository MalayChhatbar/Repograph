# RepoGraph

RepoGraph is a local-first code intelligence engine for understanding large repositories.
It indexes source code into SQLite, exposes a CLI and API, and powers a React UI for
exploring architecture, search results, impacts, cycles, and PR risk.

## V1 focus

- Python + JavaScript/TypeScript indexing
- SQLite-backed repository graph
- CLI for indexing and analysis
- FastAPI server for a React frontend
- React UI for overview, search, graph, impact, cycles, and explain
- Local-first workflow with optional Git-based risk analysis

## Architecture

```text
Python backend
  - CLI (Typer)
  - API (FastAPI)
  - Core analysis
  - SQLite storage
  - Python/JS parsers

React frontend
  - Overview dashboard
  - Search and graph exploration
  - Impact and cycles views
```

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
repograph index .
repograph serve --reload
```

Then open the frontend app in `frontend/` with your package manager of choice.

## CLI examples

```bash
repograph index .
repograph summary
repograph search login
repograph impact src/auth/session.py
repograph cycles
repograph explain src/api/users.py
repograph pr-risk main..HEAD
```

## Design decisions answered

RepoGraph v1 assumes:

- onboarding and impact analysis are the first killer workflows
- local-first and offline by default
- optional config instead of required config
- general repository navigation before deep framework specialization
- Git diff and basic churn are part of v1
- confidence-based dead code and explainable risk scoring
- basic monorepo package awareness later, not blocking v1

