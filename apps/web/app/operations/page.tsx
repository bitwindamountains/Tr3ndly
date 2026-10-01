import { SiteHeader } from "@/components/site-header";
import { getOperations } from "@/lib/api";
import { formatPht } from "@/lib/format";

const STAT_LABELS: Array<[string, string]> = [
  ["fetched", "Fetched"],
  ["new_signals", "New"],
  ["duplicate_signals", "Duplicate"],
  ["events_created", "Events +"],
  ["events_retired", "Events retired"],
  ["opportunities_created", "Opportunities +"],
  ["opportunities_rescored", "Rescored"],
];

export default async function OperationsPage() {
  const { sources, runs } = await getOperations();

  return (
    <main className="shell">
      <SiteHeader active="operations" />

      <section className="hero compact-hero">
        <div>
          <p className="kicker">OPERATIONS</p>
          <h1>Source health and runs</h1>
          <p className="hero-copy">
            Start the worker with <code>python -m tr3ndly.worker</code>. Today is marked degraded when a source
            misses two poll intervals or its last run failed.
          </p>
        </div>
      </section>

      <section className="detail-card ops-card">
        <p className="eyebrow">Sources</p>
        <h2>Registered sources</h2>
        <div className="table-scroll">
          <table className="ops-table">
            <thead>
              <tr><th>Source</th><th>State</th><th>Polls every</th><th>Last run</th><th>Last success</th><th>Last error</th></tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.slug}>
                  <td><strong>{source.display_name}</strong><small>{source.attribution}</small></td>
                  <td><span className={`state state-${source.state}`}>{source.state.replaceAll("_", " ")}</span></td>
                  <td>{source.poll_interval_minutes} min</td>
                  <td>{source.last_run_at ? formatPht(source.last_run_at) : "—"}</td>
                  <td>{source.last_success_at ? formatPht(source.last_success_at) : "—"}</td>
                  <td className="error-cell">{source.last_error ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="detail-card ops-card">
        <p className="eyebrow">History</p>
        <h2>Recent runs</h2>
        {runs.length === 0 ? (
          <p>No runs yet. Run <code>python -m tr3ndly.worker --once</code> to fetch the first batch.</p>
        ) : (
          <div className="table-scroll">
            <table className="ops-table">
              <thead>
                <tr><th>Started</th><th>Source</th><th>Status</th>{STAT_LABELS.map(([, label]) => <th className="num" key={label}>{label}</th>)}<th>Error</th></tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id}>
                    <td>{formatPht(run.started_at)}</td>
                    <td>{run.source}</td>
                    <td><span className={`state state-${run.status}`}>{run.status}</span></td>
                    {STAT_LABELS.map(([key]) => <td className="num" key={key}>{run.stats[key] ?? "—"}</td>)}
                    <td className="error-cell">{run.error ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
