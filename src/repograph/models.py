"""Core Pydantic models used across the application."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FileRecord(BaseModel):
    path: str
    language: str
    line_count: int
    content_hash: str


class SymbolRecord(BaseModel):
    path: str
    name: str
    qualified_name: str
    kind: str
    start_line: int
    end_line: int


class ImportRecord(BaseModel):
    source_path: str
    target_path: str
    import_name: str = ""


class RouteRecord(BaseModel):
    path: str
    method: str
    file_path: str
    symbol_name: str
    framework: str


class TestLinkRecord(BaseModel):
    test_path: str
    target_path: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class SearchResult(BaseModel):
    file_path: str
    snippet: str


class ImpactResult(BaseModel):
    file_path: str
    direct_dependents: list[str]
    indirect_dependents: list[str]
    related_tests: list[TestLinkRecord]
    risk_score: int
    reasons: list[str]


class SummaryResult(BaseModel):
    total_files: int
    languages: dict[str, int]
    symbols: int
    imports: int
    routes: int
    tests: int
    top_files: list[str]


class CycleResult(BaseModel):
    nodes: list[str]


class ExplainResult(BaseModel):
    file_path: str
    symbols: list[SymbolRecord]
    imports: list[str]
    routes: list[RouteRecord]
    related_tests: list[TestLinkRecord]

