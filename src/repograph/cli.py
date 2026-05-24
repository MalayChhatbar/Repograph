"""CLI entrypoint for RepoGraph."""

from __future__ import annotations

from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from repograph.api import create_app
from repograph.core import RepoGraphService

app = typer.Typer(help="RepoGraph code intelligence engine.")
console = Console()


def _service(root: Path) -> RepoGraphService:
    return RepoGraphService(root.resolve())


@app.command()
def index(path: Path = Path(".")) -> None:
    """Index the repository into SQLite."""
    service = _service(path)
    service.index()
    console.print(f"Indexed repository at [bold]{path.resolve()}[/bold]")


@app.command()
def summary(path: Path = Path(".")) -> None:
    """Show repository summary."""
    result = _service(path).summary()
    table = Table(title="RepoGraph Summary")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Files", str(result.total_files))
    table.add_row("Symbols", str(result.symbols))
    table.add_row("Imports", str(result.imports))
    table.add_row("Routes", str(result.routes))
    table.add_row("Tests", str(result.tests))
    table.add_row("Languages", ", ".join(f"{k}: {v}" for k, v in result.languages.items()) or "-")
    console.print(table)


@app.command()
def search(query: str, path: Path = Path(".")) -> None:
    """Search indexed repository content."""
    results = _service(path).search(query)
    table = Table(title=f"Search: {query}")
    table.add_column("File")
    table.add_column("Snippet")
    for row in results:
        table.add_row(row.file_path, row.snippet)
    console.print(table)


@app.command()
def impact(file_path: str, path: Path = Path(".")) -> None:
    """Show impact analysis for a file."""
    result = _service(path).impact(file_path)
    console.print(f"[bold]{result.file_path}[/bold]")
    console.print(f"Risk score: {result.risk_score}")
    if result.reasons:
        console.print("Reasons:")
        for reason in result.reasons:
            console.print(f"- {reason}")
    if result.direct_dependents:
        console.print("Direct dependents:")
        for item in result.direct_dependents:
            console.print(f"- {item}")
    if result.indirect_dependents:
        console.print("Indirect dependents:")
        for item in result.indirect_dependents:
            console.print(f"- {item}")
    if result.related_tests:
        console.print("Related tests:")
        for test in result.related_tests:
            console.print(f"- {test.test_path} ({test.confidence:.2f}, {test.reason})")


@app.command("cycles")
def cycles_command(path: Path = Path(".")) -> None:
    """Show import cycles."""
    cycles = _service(path).cycles()
    if not cycles:
        console.print("No cycles detected.")
        return
    for index, cycle in enumerate(cycles, start=1):
        console.print(f"Cycle {index}:")
        for node in cycle:
            console.print(f"- {node}")


@app.command()
def explain(file_path: str, path: Path = Path(".")) -> None:
    """Explain a file's role in the graph."""
    result = _service(path).explain(file_path)
    console.print(f"[bold]{result.file_path}[/bold]")
    if result.symbols:
        console.print("Symbols:")
        for symbol in result.symbols:
            console.print(f"- {symbol.kind}: {symbol.name} ({symbol.start_line}-{symbol.end_line})")
    if result.imports:
        console.print("Imports:")
        for item in result.imports:
            console.print(f"- {item}")
    if result.routes:
        console.print("Routes:")
        for route in result.routes:
            console.print(f"- {route.method} {route.path} ({route.framework})")
    if result.related_tests:
        console.print("Related tests:")
        for test in result.related_tests:
            console.print(f"- {test.test_path} ({test.confidence:.2f})")


@app.command("pr-risk")
def pr_risk(revision_range: str, path: Path = Path(".")) -> None:
    """Compute PR risk from a git revision range."""
    result = _service(path).pr_risk(revision_range)
    console.print(f"Revision range: {result['revision_range']}")
    console.print(f"Risk score: {result['risk_score']}")
    changed_files = result["changed_files"]
    if changed_files:
        console.print("Changed files:")
        for item in changed_files:
            console.print(f"- {item}")
    suggested_tests = result["suggested_tests"]
    if suggested_tests:
        console.print("Suggested tests:")
        for item in suggested_tests:
            console.print(f"- {item}")


@app.command()
def serve(path: Path = Path("."), host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Run the FastAPI server."""
    application = create_app(path.resolve())
    uvicorn.run(application, host=host, port=port, reload=reload)

