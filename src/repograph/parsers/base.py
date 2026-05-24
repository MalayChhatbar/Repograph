"""Base parser contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

from repograph.models import ImportRecord, RouteRecord, SymbolRecord


@dataclass(slots=True)
class ParseResult:
    symbols: list[SymbolRecord] = field(default_factory=list)
    imports: list[ImportRecord] = field(default_factory=list)
    routes: list[RouteRecord] = field(default_factory=list)


class BaseParser:
    language: str

    def can_parse(self, suffix: str) -> bool:
        raise NotImplementedError

    def parse(self, relative_path: str, source: str) -> ParseResult:
        raise NotImplementedError

