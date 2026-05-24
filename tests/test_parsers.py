from __future__ import annotations

from pathlib import Path

from repograph.parsers.javascript import JavaScriptParser
from repograph.parsers.python import PythonParser


def test_python_parser_extracts_symbols_imports_and_routes(sample_repo_root: Path) -> None:
    parser = PythonParser()
    file_path = sample_repo_root / "src/api/users.py"
    result = parser.parse("src/api/users.py", file_path.read_text())

    assert {symbol.name for symbol in result.symbols} >= {"list_users", "create_user_route"}
    assert any(item.target_path.endswith("src/services/user_service.py") for item in result.imports)
    assert {(route.method, route.path) for route in result.routes} == {
        ("GET", "/users"),
        ("POST", "/users"),
    }


def test_javascript_parser_extracts_imports_symbols_and_routes(js_repo_root: Path) -> None:
    parser = JavaScriptParser()
    file_path = js_repo_root / "src/routes/users.ts"
    result = parser.parse("src/routes/users.ts", file_path.read_text())

    assert any(item.target_path == "../services/userService" for item in result.imports)
    assert any(symbol.name == "listUsers" for symbol in result.symbols)
    assert {(route.method, route.path) for route in result.routes} == {
        ("GET", "/api/users"),
        ("POST", "/api/users"),
    }


def test_parsers_only_claim_known_suffixes() -> None:
    assert PythonParser().can_parse(".py")
    assert not PythonParser().can_parse(".ts")
    assert JavaScriptParser().can_parse(".tsx")
    assert not JavaScriptParser().can_parse(".go")
