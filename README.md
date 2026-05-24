# RepoGraph

RepoGraph is a local-first code intelligence engine for understanding large repositories.
It indexes source code into SQLite and exposes a CLI plus terminal TUI for
exploring architecture, search results, impacts, cycles, routes, and PR risk.

## V1 focus

- Python + JavaScript/TypeScript indexing
- SQLite-backed repository graph
- CLI for indexing and analysis
- Textual TUI for overview, search, graph, impact, cycles, and explain
- Local-first workflow with optional Git-based risk analysis

## Architecture

```text
Python backend
  - CLI (Typer)
  - TUI (Textual)
  - Core analysis
  - SQLite storage
  - Python/JS parsers
```

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
repograph index .
repograph tui .
```

## Current v1 capabilities

- index Python and JS/TS files into SQLite + FTS5
- search repository content
- inspect routes
- explain a file's symbols, imports, routes, and related tests
- show direct and indirect impact of a change
- detect import cycles
- suggest likely dead code with confidence scores
- score PR risk from local Git diffs
- explore the graph from a terminal TUI

## Product decisions baked into v1

The earlier design questions are answered in the implementation like this:

- first workflows: onboarding to a new repo and impact analysis after a change
- local-first: all indexing is SQLite-based and offline
- optional config: not required for the first run
- graph interaction: focus-node neighborhood view with linked panels
- Git support: local diff and basic churn-based risk inputs
- plugin model: internal parser abstraction, no public plugin installation yet

## CLI examples

```bash
repograph index .
repograph summary
repograph search login
repograph impact src/auth/session.py
repograph cycles
repograph routes
repograph dead-code
repograph explain src/api/users.py
repograph pr-risk main..HEAD
repograph tui .
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
