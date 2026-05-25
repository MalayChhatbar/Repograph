# Releasing RepoGraph

This project is distributed as a Python CLI/TUI. The primary install path is `uv`.

## Release policy

- Version tags use `vX.Y.Z`
- Package version in `pyproject.toml` must match the tag without the `v`
- Every public release should ship:
  - Git tag
  - GitHub Release
  - `uv build` artifacts
  - PyPI publish

## Prerequisites

Install and configure:

```bash
uv --version
gh auth status
```

Optional but recommended:

```bash
uv run pytest tests --basetemp .pytest-tmp
uv build
```

## 1. Prepare the version

Update [pyproject.toml](/D:/repograph/pyproject.toml):

```toml
[project]
version = "0.1.0"
```

Commit the version bump:

```bash
git add pyproject.toml uv.lock README.md
git commit -m "release: prepare v0.1.0"
```

## 2. Verify locally

Run:

```bash
uv sync --dev
uv run pytest tests --basetemp .pytest-tmp
uv run repograph --help
uv run repograph tui --help
uv build
```

Expected artifacts:

```text
dist/*.whl
dist/*.tar.gz
```

## 3. Tag the release

```bash
git tag -a v0.1.0 -m "RepoGraph v0.1.0"
git push origin main
git push origin v0.1.0
```

## 4. Create the GitHub Release

With GitHub CLI:

```bash
gh release create v0.1.0 dist/* ^
  --title "RepoGraph v0.1.0" ^
  --notes-file RELEASE_NOTES_v0.1.0.md
```

If you want GitHub-generated notes instead:

```bash
gh release create v0.1.0 dist/* --title "RepoGraph v0.1.0" --generate-notes
```

## 5. Publish to PyPI

Set `UV_PUBLISH_TOKEN` or log in with trusted publishing later.

Publish:

```bash
uv publish
```

After PyPI publication, users can install with:

```bash
uv tool install repograph
```

## 6. Homebrew distribution

RepoGraph should use a custom tap first, not `homebrew/core`.

Recommended structure:

```text
yourname/homebrew-tap
  Formula/
    repograph.rb
```

Use the template at [packaging/homebrew/repograph.rb](/D:/repograph/packaging/homebrew/repograph.rb).

Update these fields in the formula:

- `desc`
- `homepage`
- `url`
- `sha256`
- `version`
- generated `resource` blocks

To calculate the SHA256:

```bash
certutil -hashfile dist\\repograph-0.1.0.tar.gz SHA256
```

Generate the Python dependency resource blocks with:

```bash
brew install brew-pypi-poet
poet -f repograph
```

Install from the tap:

```bash
brew tap yourname/tap
brew install yourname/tap/repograph
```

## 7. Winget distribution

Winget is worth doing only after the Windows distribution story is stable.

Current recommendation:

- publish PyPI first
- publish Homebrew second
- add Winget later if you ship a stable Windows installer or standalone executable

If you decide to proceed later, create a separate Windows artifact strategy and then generate a Winget manifest.

## 8. Suggested first GitHub release metadata

Title:

```text
RepoGraph v0.1.0
```

Tag:

```text
v0.1.0
```

Description:

```text
Local-first code intelligence CLI/TUI for indexing large repositories into a queryable dependency graph.
```

Topics:

```text
python
cli
tui
textual
sqlite
static-analysis
developer-tools
code-intelligence
dependency-graph
impact-analysis
repository-analysis
ast
```

## 9. Suggested release notes template

Create `RELEASE_NOTES_v0.1.0.md`:

```md
## RepoGraph v0.1.0

First public release of RepoGraph, a local-first code intelligence CLI/TUI for understanding large repositories.

### Highlights
- Python and JavaScript/TypeScript indexing into SQLite + FTS5
- CLI and Textual TUI workflows
- Search, explain, impact analysis, cycle detection, routes, dead code, and PR risk
- Local-first installation and usage with `uv`

### Install
```bash
uv tool install repograph
```

### Notes
- Python support is stronger than JS/TS in this release
- JS/TS parsing is heuristic in v0.1.0
```

## 10. Recommended release order

1. GitHub tag
2. GitHub Release with attached artifacts
3. PyPI publish with `uv publish`
4. Homebrew tap update
5. Winget later, not now
