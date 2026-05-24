"""Python parsing using the standard library AST."""

from __future__ import annotations

import ast

from repograph.models import ImportRecord, RouteRecord, SymbolRecord
from repograph.parsers.base import BaseParser, ParseResult


class PythonParser(BaseParser):
    language = "python"
    _suffixes = {".py"}

    def can_parse(self, suffix: str) -> bool:
        return suffix in self._suffixes

    def parse(self, relative_path: str, source: str) -> ParseResult:
        tree = ast.parse(source)
        result = ParseResult()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result.symbols.append(
                    SymbolRecord(
                        path=relative_path,
                        name=node.name,
                        qualified_name=f"{relative_path}:{node.name}",
                        kind="function",
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                    )
                )
                route = self._extract_route(relative_path, node)
                if route:
                    result.routes.append(route)
            elif isinstance(node, ast.ClassDef):
                result.symbols.append(
                    SymbolRecord(
                        path=relative_path,
                        name=node.name,
                        qualified_name=f"{relative_path}:{node.name}",
                        kind="class",
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                    )
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result.imports.append(
                        ImportRecord(
                            source_path=relative_path,
                            target_path=alias.name.replace(".", "/") + ".py",
                            import_name=alias.name,
                        )
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                result.imports.append(
                    ImportRecord(
                        source_path=relative_path,
                        target_path=node.module.replace(".", "/") + ".py",
                        import_name=node.module,
                    )
                )
        return result

    def _extract_route(
        self, relative_path: str, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> RouteRecord | None:
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if not decorator.args:
                continue
            arg = decorator.args[0]
            if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
                continue
            framework = "fastapi"
            return RouteRecord(
                path=arg.value,
                method=method,
                file_path=relative_path,
                symbol_name=node.name,
                framework=framework,
            )
        return None

