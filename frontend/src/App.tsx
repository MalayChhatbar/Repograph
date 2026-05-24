import { useEffect, useMemo, useState } from "react";

import { api } from "./api";
import type { ExplainResult, ImpactResult, SearchResult, SummaryResult } from "./types";

type TabKey = "overview" | "search" | "impact" | "cycles" | "explain";

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "overview", label: "Overview" },
  { key: "search", label: "Search" },
  { key: "impact", label: "Impact" },
  { key: "cycles", label: "Cycles" },
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
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api.summary().then(setSummary).catch((err: Error) => setError(err.message));
    api.cycles().then(setCycles).catch(() => undefined);
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
              {activeTab === "impact" && "Impact analysis"}
              {activeTab === "cycles" && "Dependency cycles"}
              {activeTab === "explain" && "File explain"}
            </h2>
            <p>{error || "Built for onboarding, architecture reading, and safer code changes."}</p>
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

