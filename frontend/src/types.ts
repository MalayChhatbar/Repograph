export type SummaryResult = {
  total_files: number;
  languages: Record<string, number>;
  symbols: number;
  imports: number;
  routes: number;
  tests: number;
  top_files: string[];
};

export type SearchResult = {
  file_path: string;
  snippet: string;
};

export type TestLinkRecord = {
  test_path: string;
  target_path: string;
  confidence: number;
  reason: string;
};

export type ImpactResult = {
  file_path: string;
  direct_dependents: string[];
  indirect_dependents: string[];
  related_tests: TestLinkRecord[];
  risk_score: number;
  reasons: string[];
};

export type ExplainResult = {
  file_path: string;
  symbols: Array<{
    path: string;
    name: string;
    qualified_name: string;
    kind: string;
    start_line: number;
    end_line: number;
  }>;
  imports: string[];
  routes: Array<{
    path: string;
    method: string;
    file_path: string;
    symbol_name: string;
    framework: string;
  }>;
  related_tests: TestLinkRecord[];
};

export type RouteRecord = {
  path: string;
  method: string;
  file_path: string;
  symbol_name: string;
  framework: string;
};

export type DeadCodeRecord = {
  path: string;
  qualified_name: string;
  confidence: number;
  reasons: string[];
};
