import type {
  DeadCodeRecord,
  ExplainResult,
  ImpactResult,
  RouteRecord,
  SearchResult,
  SummaryResult,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

async function postJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export const api = {
  index: () => postJson<{ status: string }>("/index"),
  summary: () => getJson<SummaryResult>("/summary"),
  search: (query: string) => getJson<SearchResult[]>(`/search?query=${encodeURIComponent(query)}`),
  impact: (filePath: string) =>
    getJson<ImpactResult>(`/impact/${encodeURIComponent(filePath).replace(/%2F/g, "/")}`),
  explain: (filePath: string) =>
    getJson<ExplainResult>(`/explain/${encodeURIComponent(filePath).replace(/%2F/g, "/")}`),
  cycles: () => getJson<string[][]>("/cycles"),
  routes: () => getJson<RouteRecord[]>("/routes"),
  deadCode: () => getJson<DeadCodeRecord[]>("/dead-code"),
};
