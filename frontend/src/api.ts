import type { ExplainResult, ImpactResult, SearchResult, SummaryResult } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export const api = {
  summary: () => getJson<SummaryResult>("/summary"),
  search: (query: string) => getJson<SearchResult[]>(`/search?query=${encodeURIComponent(query)}`),
  impact: (filePath: string) =>
    getJson<ImpactResult>(`/impact/${encodeURIComponent(filePath).replace(/%2F/g, "/")}`),
  explain: (filePath: string) =>
    getJson<ExplainResult>(`/explain/${encodeURIComponent(filePath).replace(/%2F/g, "/")}`),
  cycles: () => getJson<string[][]>("/cycles"),
};

