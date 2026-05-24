"""Indexing and graph analysis."""

from __future__ import annotations

import hashlib
import subprocess
from collections import Counter, deque
from pathlib import Path

from repograph.config import DEFAULT_IGNORES, default_database_path
from repograph.models import FileRecord, ImpactResult, TestLinkRecord
from repograph.parsers import JavaScriptParser, PythonParser
from repograph.storage import GraphStore


class RepoGraphService:
    def __init__(self, root: Path, db_path: Path | None = None) -> None:
        self.root = root.resolve()
        self.db_path = db_path or default_database_path(self.root)
        self.store = GraphStore(self.db_path)
        self.parsers = [PythonParser(), JavaScriptParser()]

    def index(self) -> None:
        self.store.reset()
        files = list(self._iter_source_files())
        test_files = [path for path in files if self._is_test_file(path)]

        for file_path in files:
            relative_path = file_path.relative_to(self.root).as_posix()
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            parser = self._parser_for(file_path.suffix)
            language = parser.language if parser else self._detect_language(file_path.suffix)
            file_record = FileRecord(
                path=relative_path,
                language=language,
                line_count=len(content.splitlines()),
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
            self.store.upsert_file(file_record, content)
            if parser:
                parsed = parser.parse(relative_path, content)
                self.store.replace_symbols(relative_path, parsed.symbols)
                self.store.replace_imports(relative_path, parsed.imports)
                self.store.replace_routes(relative_path, parsed.routes)
            self.store.replace_test_links(relative_path, self._link_tests(relative_path, test_files))
        self.store.commit()

    def summary(self):
        return self.store.summary()

    def search(self, query: str):
        return self.store.search(query)

    def explain(self, path: str):
        return self.store.explain(path)

    def impact(self, path: str) -> ImpactResult:
        direct = self.store.dependents_for_file(path)
        indirect = self._transitive_dependents(path)
        related_tests = self._impact_test_links(path, direct, indirect)
        risk_score, reasons = self._score_risk(path, direct, indirect, related_tests)
        return ImpactResult(
            file_path=path,
            direct_dependents=direct,
            indirect_dependents=indirect,
            related_tests=related_tests,
            risk_score=risk_score,
            reasons=reasons,
        )

    def cycles(self) -> list[list[str]]:
        adjacency = self._adjacency()
        visited: set[str] = set()
        stack: list[str] = []
        in_stack: set[str] = set()
        cycles: list[list[str]] = []

        def dfs(node: str) -> None:
            visited.add(node)
            stack.append(node)
            in_stack.add(node)
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in in_stack:
                    try:
                        start = stack.index(neighbor)
                    except ValueError:
                        continue
                    cycle = stack[start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            stack.pop()
            in_stack.remove(node)

        for node in adjacency:
            if node not in visited:
                dfs(node)
        return cycles

    def pr_risk(self, revision_range: str) -> dict[str, object]:
        changed_files = self._changed_files(revision_range)
        impacts = [self.impact(path) for path in changed_files]
        total = min(100, sum(item.risk_score for item in impacts))
        suggested_tests = sorted(
            {
                link.test_path
                for impact in impacts
                for link in impact.related_tests
                if link.confidence >= 0.6
            }
        )
        return {
            "revision_range": revision_range,
            "risk_score": total,
            "changed_files": changed_files,
            "impacts": impacts,
            "suggested_tests": suggested_tests,
        }

    def _iter_source_files(self):
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in DEFAULT_IGNORES for part in path.parts):
                continue
            if path.name == self.db_path.name:
                continue
            if path.suffix.lower() not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                continue
            yield path

    def _parser_for(self, suffix: str):
        for parser in self.parsers:
            if parser.can_parse(suffix.lower()):
                return parser
        return None

    def _detect_language(self, suffix: str) -> str:
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }.get(suffix.lower(), "unknown")

    def _is_test_file(self, path: Path) -> bool:
        name = path.name.lower()
        return (
            "test" in path.parts
            or name.startswith("test_")
            or name.endswith(".test.ts")
            or name.endswith(".spec.ts")
            or name.endswith(".test.js")
            or name.endswith(".spec.js")
        )

    def _link_tests(self, relative_path: str, test_files: list[Path]) -> list[TestLinkRecord]:
        if relative_path.startswith("tests/") or "/tests/" in relative_path:
            return []
        stem = Path(relative_path).stem
        parent = Path(relative_path).parent.name
        links: list[TestLinkRecord] = []
        for test_file in test_files:
            test_rel = test_file.relative_to(self.root).as_posix()
            test_name = test_file.stem.lower()
            if stem.lower() in test_name:
                confidence = 0.8
                reason = "matching file stem"
            elif parent and parent.lower() in test_rel.lower():
                confidence = 0.5
                reason = "matching module area"
            else:
                continue
            links.append(
                TestLinkRecord(
                    test_path=test_rel,
                    target_path=relative_path,
                    confidence=confidence,
                    reason=reason,
                )
            )
        return links

    def _adjacency(self) -> dict[str, list[str]]:
        rows = self.store.connection.execute(
            "SELECT source_path, target_path FROM imports ORDER BY source_path, target_path"
        )
        adjacency: dict[str, list[str]] = {}
        for row in rows:
            adjacency.setdefault(row["source_path"], []).append(row["target_path"])
            adjacency.setdefault(row["target_path"], [])
        return adjacency

    def _transitive_dependents(self, path: str) -> list[str]:
        visited: set[str] = set()
        queue: deque[str] = deque(self.store.dependents_for_file(path))
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for dependent in self.store.dependents_for_file(current):
                if dependent not in visited:
                    queue.append(dependent)
        return sorted(visited)

    def _impact_test_links(
        self, path: str, direct: list[str], indirect: list[str]
    ) -> list[TestLinkRecord]:
        collected: dict[tuple[str, str], TestLinkRecord] = {}
        candidate_paths = [path, *direct, *indirect]
        for candidate in candidate_paths:
            for link in self.store.related_tests_for_file(candidate):
                key = (link.test_path, link.target_path)
                existing = collected.get(key)
                if existing is None or link.confidence > existing.confidence:
                    collected[key] = link
        return sorted(
            collected.values(),
            key=lambda item: (-item.confidence, item.test_path, item.target_path),
        )

    def _score_risk(
        self,
        path: str,
        direct: list[str],
        indirect: list[str],
        related_tests: list[TestLinkRecord],
    ) -> tuple[int, list[str]]:
        reasons: list[str] = []
        score = min(40, len(direct) * 8)
        if direct:
            reasons.append(f"used directly by {len(direct)} files")
        indirect_only = max(0, len(indirect) - len(direct))
        score += min(20, indirect_only * 2)
        if indirect_only:
            reasons.append(f"has {indirect_only} indirect dependents")
        lower = path.lower()
        if any(keyword in lower for keyword in ("auth", "payment", "db", "config")):
            score += 15
            reasons.append("belongs to a sensitive subsystem")
        if not related_tests:
            score += 15
            reasons.append("no related tests detected")
        else:
            high_conf = sum(1 for link in related_tests if link.confidence >= 0.6)
            if high_conf < 2:
                score += 8
                reasons.append("thin related test coverage")
        churn = self._git_churn(path)
        score += min(10, churn * 2)
        if churn:
            reasons.append(f"changed in {churn} recent commits")
        return min(100, score), reasons

    def _git_churn(self, path: str) -> int:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--", path],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return 0
        if result.returncode != 0:
            return 0
        return min(5, len([line for line in result.stdout.splitlines() if line.strip()]))

    def _changed_files(self, revision_range: str) -> list[str]:
        result = subprocess.run(
            ["git", "diff", "--name-only", revision_range],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
