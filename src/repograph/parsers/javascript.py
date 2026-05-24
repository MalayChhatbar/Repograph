"""Lightweight JavaScript and TypeScript parser using regex heuristics."""

from __future__ import annotations

import re

from repograph.models import ImportRecord, RouteRecord, SymbolRecord
from repograph.parsers.base import BaseParser, ParseResult

IMPORT_RE = re.compile(
    r"""import\s+(?:[\w*\s{},]+from\s+)?["'](?P<target>[^"']+)["'];?"""
)
FUNCTION_RE = re.compile(r"""(?:export\s+)?function\s+(?P<name>[A-Za-z_][\w]*)\s*\(""")
CLASS_RE = re.compile(r"""(?:export\s+)?class\s+(?P<name>[A-Za-z_][\w]*)\b""")
ROUTE_RE = re.compile(
    r"""(?:app|router)\.(?P<method>get|post|put|patch|delete)\(\s*["'](?P<path>[^"']+)["']"""
)


class JavaScriptParser(BaseParser):
    language = "javascript"
    _suffixes = {".js", ".jsx", ".ts", ".tsx"}

    def can_parse(self, suffix: str) -> bool:
        return suffix in self._suffixes

    def parse(self, relative_path: str, source: str) -> ParseResult:
        result = ParseResult()
        lines = source.splitlines()

        for index, line in enumerate(lines, start=1):
            import_match = IMPORT_RE.search(line)
            if import_match:
                result.imports.append(
                    ImportRecord(
                        source_path=relative_path,
                        target_path=import_match.group("target"),
                        import_name=import_match.group("target"),
                    )
                )
            function_match = FUNCTION_RE.search(line)
            if function_match:
                name = function_match.group("name")
                result.symbols.append(
                    SymbolRecord(
                        path=relative_path,
                        name=name,
                        qualified_name=f"{relative_path}:{name}",
                        kind="function",
                        start_line=index,
                        end_line=index,
                    )
                )
            class_match = CLASS_RE.search(line)
            if class_match:
                name = class_match.group("name")
                result.symbols.append(
                    SymbolRecord(
                        path=relative_path,
                        name=name,
                        qualified_name=f"{relative_path}:{name}",
                        kind="class",
                        start_line=index,
                        end_line=index,
                    )
                )
            route_match = ROUTE_RE.search(line)
            if route_match:
                result.routes.append(
                    RouteRecord(
                        path=route_match.group("path"),
                        method=route_match.group("method").upper(),
                        file_path=relative_path,
                        symbol_name="",
                        framework="express",
                    )
                )
        return result

