"""Textual TUI for RepoGraph."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Static, TabbedContent, TabPane

from repograph.core import RepoGraphService


@dataclass(slots=True)
class RepoSnapshot:
    overview: str
    search_results: str
    graph: str
    impact: str
    cycles: str
    routes: str
    dead_code: str
    explain: str


class RepoGraphApp(App[None]):
    """Interactive terminal view for indexed repository intelligence."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #body {
        height: 1fr;
    }
    #sidebar {
        width: 32;
        min-width: 32;
        border-right: solid $surface;
        padding: 1;
    }
    #content {
        padding: 1;
    }
    Input {
        margin-bottom: 1;
    }
    .panel {
        border: round $surface;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "focus_search", "Search"),
        Binding("r", "refresh", "Refresh"),
    ]

    current_focus: reactive[str] = reactive("")
    current_query: reactive[str] = reactive("user")

    def __init__(self, service: RepoGraphService, initial_focus: str = "") -> None:
        super().__init__()
        self.service = service
        self.current_focus = initial_focus
        self.snapshot = RepoSnapshot("", "", "", "", "", "", "", "")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("RepoGraph", classes="panel")
                yield Input(value=self.current_query, placeholder="Search query", id="query-input")
                yield Input(value=self.current_focus, placeholder="Focus file", id="focus-input")
                yield Static(
                    "Keys\n"
                    "/ focus search\n"
                    "r refresh\n"
                    "q quit",
                    classes="panel",
                )
            with Vertical(id="content"):
                with TabbedContent(initial="overview"):
                    with TabPane("Overview", id="overview"):
                        yield Static(id="overview-view", classes="panel")
                    with TabPane("Search", id="search"):
                        yield Static(id="search-view", classes="panel")
                    with TabPane("Graph", id="graph"):
                        yield Static(id="graph-view", classes="panel")
                    with TabPane("Impact", id="impact"):
                        yield Static(id="impact-view", classes="panel")
                    with TabPane("Cycles", id="cycles"):
                        yield Static(id="cycles-view", classes="panel")
                    with TabPane("Routes", id="routes"):
                        yield Static(id="routes-view", classes="panel")
                    with TabPane("Dead Code", id="dead-code"):
                        yield Static(id="dead-code-view", classes="panel")
                    with TabPane("Explain", id="explain"):
                        yield Static(id="explain-view", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        summary = self.service.summary()
        if summary.total_files == 0:
            self.service.index()
            summary = self.service.summary()
        if not self.current_focus:
            self.current_focus = summary.top_files[0] if summary.top_files else ""
        self.refresh_snapshot()

    def action_focus_search(self) -> None:
        self.query_one("#query-input", Input).focus()

    def action_refresh(self) -> None:
        self.refresh_snapshot()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "query-input":
            self.current_query = event.value
        elif event.input.id == "focus-input":
            self.current_focus = event.value
        self.refresh_snapshot()

    def refresh_snapshot(self) -> None:
        self.snapshot = self._build_snapshot(self.current_query, self.current_focus)
        self.query_one("#overview-view", Static).update(self.snapshot.overview)
        self.query_one("#search-view", Static).update(self.snapshot.search_results)
        self.query_one("#graph-view", Static).update(self.snapshot.graph)
        self.query_one("#impact-view", Static).update(self.snapshot.impact)
        self.query_one("#cycles-view", Static).update(self.snapshot.cycles)
        self.query_one("#routes-view", Static).update(self.snapshot.routes)
        self.query_one("#dead-code-view", Static).update(self.snapshot.dead_code)
        self.query_one("#explain-view", Static).update(self.snapshot.explain)

    def _build_snapshot(self, query: str, focus: str) -> RepoSnapshot:
        summary = self.service.summary()
        search_results = self.service.search(query) if query else []
        focus_target = focus or (summary.top_files[0] if summary.top_files else "")
        graph = self.service.graph(focus_target) if focus_target else None
        impact = self.service.impact(focus_target) if focus_target else None
        explain = self.service.explain(focus_target) if focus_target else None
        cycles = self.service.cycles()
        routes = self.service.routes()
        dead_code = self.service.dead_code()

        overview_text = "\n".join(
            [
                f"Files: {summary.total_files}",
                f"Symbols: {summary.symbols}",
                f"Imports: {summary.imports}",
                f"Routes: {summary.routes}",
                f"Tests: {summary.tests}",
                "",
                "Languages:",
                *[f"  {language}: {count}" for language, count in sorted(summary.languages.items())],
                "",
                "Important files:",
                *[f"  {path}" for path in summary.top_files],
            ]
        )

        search_text = "\n".join(
            [f"{item.file_path}\n  {item.snippet}" for item in search_results]
        ) or "No search results."

        if graph and impact and explain:
            graph_text = "\n".join(
                [
                    f"Center: {graph['center']}",
                    "",
                    "Depends on:",
                    *[f"  {item}" for item in graph["depends_on"]],
                    "",
                    "Used by:",
                    *[f"  {item}" for item in graph["used_by"]],
                    "",
                    f"Indirect dependents: {len(graph['indirect_dependents'])}",
                    f"Related tests: {len(graph['related_tests'])}",
                    f"Routes: {len(graph['routes'])}",
                ]
            )
            impact_text = "\n".join(
                [
                    f"Focus: {impact.file_path}",
                    f"Risk score: {impact.risk_score}",
                    "",
                    "Reasons:",
                    *[f"  {reason}" for reason in impact.reasons],
                    "",
                    "Direct dependents:",
                    *[f"  {item}" for item in impact.direct_dependents],
                    "",
                    "Related tests:",
                    *[
                        f"  {item.test_path} ({item.confidence:.2f}, {item.reason})"
                        for item in impact.related_tests
                    ],
                ]
            )
            explain_text = "\n".join(
                [
                    f"File: {explain.file_path}",
                    "",
                    "Symbols:",
                    *[
                        f"  {symbol.kind}: {symbol.name} ({symbol.start_line}-{symbol.end_line})"
                        for symbol in explain.symbols
                    ],
                    "",
                    "Imports:",
                    *[f"  {item}" for item in explain.imports],
                    "",
                    "Routes:",
                    *[
                        f"  {route.method} {route.path} [{route.framework}]"
                        for route in explain.routes
                    ],
                ]
            )
        else:
            graph_text = "No focus file selected."
            impact_text = "No focus file selected."
            explain_text = "No focus file selected."

        cycle_text = "\n\n".join(" -> ".join(cycle) for cycle in cycles) or "No cycles detected."
        route_text = "\n".join(
            f"{route.method:6} {route.path:20} {route.file_path}"
            for route in routes
        ) or "No routes detected."
        dead_code_text = "\n".join(
            f"{item['qualified_name']} [{item['confidence']:.2f}]"
            for item in dead_code[:30]
        ) or "No likely dead code detected."

        return RepoSnapshot(
            overview=overview_text,
            search_results=search_text,
            graph=graph_text,
            impact=impact_text,
            cycles=cycle_text,
            routes=route_text,
            dead_code=dead_code_text,
            explain=explain_text,
        )


def run_tui(root: Path, focus: str = "") -> None:
    service = RepoGraphService(root.resolve())
    app = RepoGraphApp(service=service, initial_focus=focus)
    app.run()
