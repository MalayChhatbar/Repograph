"""SQLite storage for indexed graph data."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from repograph.models import (
    ExplainResult,
    FileRecord,
    ImportRecord,
    RouteRecord,
    SearchResult,
    SummaryResult,
    SymbolRecord,
    TestLinkRecord,
)

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    line_count INTEGER NOT NULL,
    content_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    name TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    FOREIGN KEY(path) REFERENCES files(path) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    import_name TEXT NOT NULL,
    FOREIGN KEY(source_path) REFERENCES files(path) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    file_path TEXT NOT NULL,
    symbol_name TEXT NOT NULL,
    framework TEXT NOT NULL,
    FOREIGN KEY(file_path) REFERENCES files(path) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    confidence REAL NOT NULL,
    reason TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS file_search USING fts5(
    path,
    content
);
"""


class GraphStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def reset(self) -> None:
        self.connection.executescript(
            """
            DELETE FROM symbols;
            DELETE FROM imports;
            DELETE FROM routes;
            DELETE FROM test_links;
            DELETE FROM files;
            DELETE FROM file_search;
            """
        )
        self.connection.commit()

    def upsert_file(self, file: FileRecord, content: str) -> None:
        self.connection.execute(
            """
            INSERT INTO files(path, language, line_count, content_hash)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
              language=excluded.language,
              line_count=excluded.line_count,
              content_hash=excluded.content_hash
            """,
            (file.path, file.language, file.line_count, file.content_hash),
        )
        self.connection.execute("DELETE FROM file_search WHERE path = ?", (file.path,))
        self.connection.execute(
            "INSERT INTO file_search(path, content) VALUES (?, ?)",
            (file.path, content),
        )

    def replace_symbols(self, path: str, symbols: list[SymbolRecord]) -> None:
        self.connection.execute("DELETE FROM symbols WHERE path = ?", (path,))
        self.connection.executemany(
            """
            INSERT INTO symbols(path, name, qualified_name, kind, start_line, end_line)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    symbol.path,
                    symbol.name,
                    symbol.qualified_name,
                    symbol.kind,
                    symbol.start_line,
                    symbol.end_line,
                )
                for symbol in symbols
            ],
        )

    def replace_imports(self, path: str, imports: list[ImportRecord]) -> None:
        self.connection.execute("DELETE FROM imports WHERE source_path = ?", (path,))
        self.connection.executemany(
            """
            INSERT INTO imports(source_path, target_path, import_name)
            VALUES (?, ?, ?)
            """,
            [(imp.source_path, imp.target_path, imp.import_name) for imp in imports],
        )

    def replace_routes(self, path: str, routes: list[RouteRecord]) -> None:
        self.connection.execute("DELETE FROM routes WHERE file_path = ?", (path,))
        self.connection.executemany(
            """
            INSERT INTO routes(path, method, file_path, symbol_name, framework)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    route.path,
                    route.method,
                    route.file_path,
                    route.symbol_name,
                    route.framework,
                )
                for route in routes
            ],
        )

    def replace_test_links(self, path: str, links: list[TestLinkRecord]) -> None:
        self.connection.execute("DELETE FROM test_links WHERE target_path = ?", (path,))
        self.connection.executemany(
            """
            INSERT INTO test_links(test_path, target_path, confidence, reason)
            VALUES (?, ?, ?, ?)
            """,
            [(link.test_path, link.target_path, link.confidence, link.reason) for link in links],
        )

    def commit(self) -> None:
        self.connection.commit()

    def summary(self) -> SummaryResult:
        total_files = self.connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        symbols = self.connection.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        imports = self.connection.execute("SELECT COUNT(*) FROM imports").fetchone()[0]
        routes = self.connection.execute("SELECT COUNT(*) FROM routes").fetchone()[0]
        tests = self.connection.execute(
            "SELECT COUNT(DISTINCT test_path) FROM test_links"
        ).fetchone()[0]
        languages = {
            row["language"]: row["count"]
            for row in self.connection.execute(
                "SELECT language, COUNT(*) AS count FROM files GROUP BY language"
            )
        }
        top_files = [
            row["path"]
            for row in self.connection.execute(
                """
                SELECT source_path AS path, COUNT(*) AS degree
                FROM imports
                GROUP BY source_path
                ORDER BY degree DESC, source_path ASC
                LIMIT 5
                """
            )
        ]
        return SummaryResult(
            total_files=total_files,
            languages=languages,
            symbols=symbols,
            imports=imports,
            routes=routes,
            tests=tests,
            top_files=top_files,
        )

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        return [
            SearchResult(file_path=row["path"], snippet=row["snippet"])
            for row in self.connection.execute(
                """
                SELECT path, snippet(file_search, 1, '[', ']', '...', 12) AS snippet
                FROM file_search
                WHERE file_search MATCH ?
                LIMIT ?
                """,
                (query, limit),
            )
        ]

    def imports_for_file(self, path: str) -> list[str]:
        return [
            row["target_path"]
            for row in self.connection.execute(
                "SELECT target_path FROM imports WHERE source_path = ? ORDER BY target_path",
                (path,),
            )
        ]

    def dependents_for_file(self, path: str) -> list[str]:
        return [
            row["source_path"]
            for row in self.connection.execute(
                "SELECT source_path FROM imports WHERE target_path = ? ORDER BY source_path",
                (path,),
            )
        ]

    def symbols_for_file(self, path: str) -> list[SymbolRecord]:
        return [
            SymbolRecord(
                path=row["path"],
                name=row["name"],
                qualified_name=row["qualified_name"],
                kind=row["kind"],
                start_line=row["start_line"],
                end_line=row["end_line"],
            )
            for row in self.connection.execute(
                """
                SELECT path, name, qualified_name, kind, start_line, end_line
                FROM symbols WHERE path = ? ORDER BY start_line
                """,
                (path,),
            )
        ]

    def routes_for_file(self, path: str) -> list[RouteRecord]:
        return [
            RouteRecord(
                path=row["path"],
                method=row["method"],
                file_path=row["file_path"],
                symbol_name=row["symbol_name"],
                framework=row["framework"],
            )
            for row in self.connection.execute(
                """
                SELECT path, method, file_path, symbol_name, framework
                FROM routes WHERE file_path = ?
                ORDER BY method, path
                """,
                (path,),
            )
        ]

    def related_tests_for_file(self, path: str) -> list[TestLinkRecord]:
        return [
            TestLinkRecord(
                test_path=row["test_path"],
                target_path=row["target_path"],
                confidence=row["confidence"],
                reason=row["reason"],
            )
            for row in self.connection.execute(
                """
                SELECT test_path, target_path, confidence, reason
                FROM test_links
                WHERE target_path = ?
                ORDER BY confidence DESC, test_path ASC
                """,
                (path,),
            )
        ]

    def explain(self, path: str) -> ExplainResult:
        return ExplainResult(
            file_path=path,
            symbols=self.symbols_for_file(path),
            imports=self.imports_for_file(path),
            routes=self.routes_for_file(path),
            related_tests=self.related_tests_for_file(path),
        )

    def all_symbol_counts(self) -> list[tuple[str, str, int]]:
        return [
            (row["path"], row["qualified_name"], row["ref_count"])
            for row in self.connection.execute(
                """
                SELECT s.path, s.qualified_name, COUNT(fs.path) AS ref_count
                FROM symbols s
                LEFT JOIN file_search fs ON fs.content MATCH '"' || s.name || '"'
                GROUP BY s.path, s.qualified_name
                ORDER BY ref_count ASC, s.qualified_name ASC
                """
            )
        ]

    def all_routes(self) -> list[RouteRecord]:
        return [
            RouteRecord(
                path=row["path"],
                method=row["method"],
                file_path=row["file_path"],
                symbol_name=row["symbol_name"],
                framework=row["framework"],
            )
            for row in self.connection.execute(
                """
                SELECT path, method, file_path, symbol_name, framework
                FROM routes
                ORDER BY file_path, method, path
                """
            )
        ]
