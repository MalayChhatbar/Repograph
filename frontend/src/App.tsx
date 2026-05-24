import { useEffect, useMemo, useState } from "react";

import { api } from "./api";
import type {
  DeadCodeRecord,
  ExplainResult,
  ImpactResult,
  RouteRecord,
  SearchResult,
  SummaryResult,
} from "./types";

type TabKey = "overview" | "search" | "graph" | "impact" | "cycles" | "routes" | "dead" | "explain";

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "overview", label: "Overview" },
  { key: "search", label: "Search" },
  { key: "graph", label: "Graph" },
  { key: "impact", label: "Impact" },
  { key: "cycles", label: "Cycles" },
  { key: "routes", label: "Routes" },
  { key: "dead", label: "Dead Code" },
  { key: "explain", label: "Explain" },
];

export function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [summary, setSummary] = useState<SummaryResult | null>(null);
  const [searchQuery, setSearchQuery] = useState("user");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [selectedFile, setSelectedFile] = useState("src/services/user_service.py");
  const [impact, setImpact] = useState<ImpactResult | null>(null);
  const [explain, setExplain] = useState<ExplainResult | null>(null);
  const [cycles, setCycles] = useState<string[][]>([]);
  const [routes, setRoutes] = useState<RouteRecord[]>([]);
  const [deadCode, setDeadCode] = useState<DeadCodeRecord[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  async function refreshOverview() {
    setLoading(true);
    setError("");
    try {
      const [nextSummary, nextCycles, nextRoutes, nextDeadCode] = await Promise.all([
        api.summary(),
        api.cycles(),
        api.routes(),
        api.deadCode(),
      ]);
      setSummary(nextSummary);
      setCycles(nextCycles);
      setRoutes(nextRoutes);
      setDeadCode(nextDeadCode);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshOverview();
  }, []);

  useEffect(() => {
    api.search(searchQuery).then(setSearchResults).catch(() => undefined);
  }, [searchQuery]);

  useEffect(() => {
    api.impact(selectedFile).then(setImpact).catch(() => undefined);
    api.explain(selectedFile).then(setExplain).catch(() => undefined);
  }, [selectedFile]);

  const languagePairs = useMemo(
    () => Object.entries(summary?.languages ?? {}).sort((a, b) => b[1] - a[1]),
    [summary],
  );

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">RG</div>
          <div>
            <h1>RepoGraph</h1>
            <p>Local-first code intelligence</p>
          </div>
        </div>
        <nav className="tabs" aria-label="Primary">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              className={tab.key === activeTab ? "tab active" : "tab"}
              onClick={() => setActiveTab(tab.key)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-card">
          <label htmlFor="file-input">Focus file</label>
          <input
            id="file-input"
            value={selectedFile}
            onChange={(event) => setSelectedFile(event.target.value)}
          />
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h2>
              {activeTab === "overview" && "Repository overview"}
              {activeTab === "search" && "Search the index"}
              {activeTab === "graph" && "Graph neighborhood"}
              {activeTab === "impact" && "Impact analysis"}
              {activeTab === "cycles" && "Dependency cycles"}
              {activeTab === "routes" && "Route map"}
              {activeTab === "dead" && "Potential dead code"}
              {activeTab === "explain" && "File explain"}
            </h2>
            <p>{error || "Built for onboarding, architecture reading, and safer code changes."}</p>
          </div>
          <div className="topbar-actions">
            <button
              type="button"
              className="action"
              onClick={() => {
                setLoading(true);
                api
                  .index()
                  .then(() => refreshOverview())
                  .catch((err: Error) => setError(err.message))
                  .finally(() => setLoading(false));
              }}
            >
              {loading ? "Indexing..." : "Refresh Index"}
            </button>
          </div>
        </header>

        {activeTab === "overview" && (
          <section className="panel-grid">
            <article className="panel metrics">
              <Metric label="Files" value={summary?.total_files ?? "-"} />
              <Metric label="Symbols" value={summary?.symbols ?? "-"} />
              <Metric label="Imports" value={summary?.imports ?? "-"} />
              <Metric label="Routes" value={summary?.routes ?? "-"} />
              <Metric label="Tests" value={summary?.tests ?? "-"} />
            </article>
            <article className="panel">
              <h3>Languages</h3>
              <ul className="list">
                {languagePairs.map(([language, count]) => (
                  <li key={language}>
                    <span>{language}</span>
                    <strong>{count}</strong>
                  </li>
                ))}
              </ul>
            </article>
            <article className="panel">
              <h3>Important files</h3>
              <ul className="list">
                {(summary?.top_files ?? []).map((item) => (
                  <li key={item}>
                    <button type="button" className="linkish" onClick={() => setSelectedFile(item)}>
                      {item}
                    </button>
                  </li>
                ))}
              </ul>
            </article>
          </section>
        )}

        {activeTab === "search" && (
          <section className="panel">
            <div className="toolbar">
              <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} />
            </div>
            <ul className="list result-list">
              {searchResults.map((result) => (
                <li key={`${result.file_path}:${result.snippet}`}>
                  <button type="button" className="result" onClick={() => setSelectedFile(result.file_path)}>
                    <strong>{result.file_path}</strong>
                    <span dangerouslySetInnerHTML={{ __html: result.snippet }} />
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        {activeTab === "graph" && (
          <section className="panel-grid graph-grid">
            <article className="panel">
              <h3>Center node</h3>
              <div className="focus-file">{selectedFile}</div>
            </article>
            <article className="panel">
              <h3>Depends on</h3>
              <SimpleList items={explain?.imports ?? []} onSelect={setSelectedFile} />
            </article>
            <article className="panel">
              <h3>Used by</h3>
              <SimpleList items={impact?.direct_dependents ?? []} onSelect={setSelectedFile} />
            </article>
            <article className="panel">
              <h3>Neighborhood notes</h3>
              <ul className="list">
                <li>
                  <span>Indirect dependents</span>
                  <strong>{impact?.indirect_dependents.length ?? 0}</strong>
                </li>
                <li>
                  <span>Related tests</span>
                  <strong>{impact?.related_tests.length ?? 0}</strong>
                </li>
                <li>
                  <span>Routes in file</span>
                  <strong>{explain?.routes.length ?? 0}</strong>
                </li>
              </ul>
            </article>
          </section>
        )}

        {activeTab === "impact" && impact && (
          <section className="panel-grid impact-grid">
            <article className="panel">
              <h3>{impact.file_path}</h3>
              <div className="risk">{impact.risk_score}</div>
              <ul className="list">
                {impact.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </article>
            <article className="panel">
              <h3>Direct dependents</h3>
              <SimpleList items={impact.direct_dependents} onSelect={setSelectedFile} />
            </article>
            <article className="panel">
              <h3>Indirect dependents</h3>
              <SimpleList items={impact.indirect_dependents} onSelect={setSelectedFile} />
            </article>
            <article className="panel">
              <h3>Related tests</h3>
              <ul className="list">
                {impact.related_tests.map((test) => (
                  <li key={test.test_path}>
                    <span>{test.test_path}</span>
                    <strong>{test.confidence.toFixed(2)}</strong>
                  </li>
                ))}
              </ul>
            </article>
          </section>
        )}

        {activeTab === "cycles" && (
          <section className="panel">
            <h3>Detected cycles</h3>
            <div className="cycle-stack">
              {cycles.length === 0 && <p className="muted">No cycles detected in the current index.</p>}
              {cycles.map((cycle, index) => (
                <div className="cycle" key={`${cycle.join("->")}-${index}`}>
                  {cycle.map((node) => (
                    <button key={node} type="button" className="cycle-node" onClick={() => setSelectedFile(node)}>
                      {node}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </section>
        )}

        {activeTab === "routes" && (
          <section className="panel">
            <ul className="list result-list">
              {routes.map((route) => (
                <li key={`${route.method}:${route.path}:${route.file_path}`}>
                  <button type="button" className="result" onClick={() => setSelectedFile(route.file_path)}>
                    <strong>
                      {route.method} {route.path}
                    </strong>
                    <span>
                      {route.framework} in {route.file_path}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        {activeTab === "dead" && (
          <section className="panel">
            <ul className="list result-list">
              {deadCode.map((item) => (
                <li key={item.qualified_name}>
                  <button type="button" className="result" onClick={() => setSelectedFile(item.path)}>
                    <strong>{item.qualified_name}</strong>
                    <span>
                      {item.path} · confidence {item.confidence.toFixed(2)} · {item.reasons.join(", ")}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        {activeTab === "explain" && explain && (
          <section className="panel-grid">
            <article className="panel">
              <h3>Symbols</h3>
              <ul className="list">
                {explain.symbols.map((symbol) => (
                  <li key={symbol.qualified_name}>
                    <span>{symbol.kind}</span>
                    <strong>{symbol.name}</strong>
                  </li>
                ))}
              </ul>
            </article>
            <article className="panel">
              <h3>Imports</h3>
              <SimpleList items={explain.imports} onSelect={setSelectedFile} />
            </article>
            <article className="panel">
              <h3>Routes</h3>
              <ul className="list">
                {explain.routes.map((route) => (
                  <li key={`${route.method}:${route.path}`}>
                    <span>{route.method}</span>
                    <strong>{route.path}</strong>
                  </li>
                ))}
              </ul>
            </article>
            <article className="panel">
              <h3>Related tests</h3>
              <ul className="list">
                {explain.related_tests.map((test) => (
                  <li key={test.test_path}>
                    <span>{test.test_path}</span>
                    <strong>{test.reason}</strong>
                  </li>
                ))}
              </ul>
            </article>
          </section>
        )}
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SimpleList({
  items,
  onSelect,
}: {
  items: string[];
  onSelect: (value: string) => void;
}) {
  return (
    <ul className="list">
      {items.map((item) => (
        <li key={item}>
          <button type="button" className="linkish" onClick={() => onSelect(item)}>
            {item}
          </button>
        </li>
      ))}
    </ul>
  );
}
