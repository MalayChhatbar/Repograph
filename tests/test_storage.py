from __future__ import annotations

def test_search_returns_matching_file(indexed_sample_service) -> None:
    results = indexed_sample_service.search("create")
    assert any(item.file_path == "src/services/user_service.py" for item in results)


def test_explain_includes_symbols_imports_routes_and_tests(indexed_sample_service) -> None:
    explanation = indexed_sample_service.explain("src/api/users.py")
    assert [symbol.name for symbol in explanation.symbols] == ["list_users", "create_user_route"]
    assert "src/services/user_service.py" in explanation.imports
    assert len(explanation.routes) == 2


def test_graph_store_all_routes(indexed_sample_service) -> None:
    routes = indexed_sample_service.store.all_routes()
    assert len(routes) == 2
    assert routes[0].framework == "fastapi"


def test_graph_store_symbol_counts(indexed_sample_service) -> None:
    counts = indexed_sample_service.store.all_symbol_counts()
    assert any(qualified_name.endswith(":create_user") for _, qualified_name, _ in counts)
