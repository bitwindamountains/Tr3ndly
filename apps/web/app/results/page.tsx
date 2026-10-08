import { ResultsImportForm } from "@/components/results-import-form";
import { SiteHeader } from "@/components/site-header";
import { getResultsOverview } from "@/lib/api";
import { formatPercent, formatPeso } from "@/lib/format";
import type { ResultTotals } from "@/lib/types";

function money(value: number | null): string {
  return value == null ? "—" : formatPeso(value);
}

function TotalsTile({ title, totals }: { title: string; totals: ResultTotals }) {
  return (
    <section className="detail-card">
      <p className="eyebrow">{title}</p>
      <h2>{money(totals.commission_php)} commission</h2>
      <dl className="score-table">
        <dt>Posts</dt><dd>{totals.posts}</dd>
        <dt>Commission per post</dt><dd>{money(totals.commission_per_post_php)}</dd>
        <dt>Commission per 1,000 views</dt><dd>{money(totals.commission_per_1000_views_php)}</dd>
        <dt>Views</dt><dd>{totals.views.toLocaleString("en-PH")}</dd>
        <dt>Clicks</dt><dd>{totals.clicks.toLocaleString("en-PH")}</dd>
        <dt>Click-through rate</dt><dd>{formatPercent(totals.click_through_rate)}</dd>
        <dt>Orders</dt><dd>{totals.orders.toLocaleString("en-PH")}</dd>
        <dt>Conversion rate</dt><dd>{formatPercent(totals.conversion_rate)}</dd>
        <dt>Sales (GMV)</dt><dd>{money(totals.gmv_php)}</dd>
      </dl>
    </section>
  );
}

function GroupTable({ title, groups }: { title: string; groups: Array<{ key: string; totals: ResultTotals }> }) {
  if (groups.length === 0) return null;
  return (
    <section className="detail-card ops-card">
      <p className="eyebrow">Assisted posts by {title}</p>
      <div className="table-scroll">
        <table className="ops-table">
          <thead>
            <tr><th>{title}</th><th className="num">Posts</th><th className="num">Clicks</th><th className="num">Orders</th><th className="num">Commission</th><th className="num">Per post</th></tr>
          </thead>
          <tbody>
            {groups.map((group) => (
              <tr key={group.key}>
                <td>{group.key.replaceAll("_", " ")}</td>
                <td className="num">{group.totals.posts}</td>
                <td className="num">{group.totals.clicks}</td>
                <td className="num">{group.totals.orders}</td>
                <td className="num">{money(group.totals.commission_php)}</td>
                <td className="num">{money(group.totals.commission_per_post_php)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default async function ResultsPage() {
  const overview = await getResultsOverview();

  return (
    <main className="shell">
      <SiteHeader active="results" />

      <section className="hero compact-hero">
        <div>
          <p className="kicker">RESULTS</p>
          <h1>What is earning</h1>
          <p className="hero-copy">
            Import your affiliate report. Rows match exported posts by tracking code (the sub ID on your affiliate link),
            so each sale traces back to the listing, brief, and copy variant that produced it.
          </p>
        </div>
      </section>

      {overview.warnings.length > 0 && (
        <aside className="demo-banner">
          <div>{overview.warnings.map((warning) => <span key={warning}>{warning}</span>)}</div>
        </aside>
      )}

      <div className="results-grid">
        <TotalsTile title="Tr3ndly-assisted posts" totals={overview.assisted} />
        <TotalsTile title="Baseline posts" totals={overview.baseline} />
        <section className="detail-card">
          <p className="eyebrow">Import</p>
          <h2>Add results</h2>
          <ResultsImportForm />
        </section>
      </div>

      <GroupTable groups={overview.by_event_type} title="event type" />
      <GroupTable groups={overview.by_category} title="category" />
      <GroupTable groups={overview.by_hook_type} title="hook type" />
    </main>
  );
}
