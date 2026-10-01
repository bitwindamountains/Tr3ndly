import { Activity, AlertTriangle, Bell, ChevronDown, CircleDot, Clock3, DatabaseZap, SlidersHorizontal } from "lucide-react";

import type { SourceStatus, TodayData } from "@/lib/types";
import { Brand } from "./brand";
import { OpportunityCard } from "./opportunity-card";

export function TodayView({ data, apiConnected }: { data: TodayData; apiConnected: boolean }) {
  const generatedAt = new Intl.DateTimeFormat("en-PH", {
    timeZone: "Asia/Manila",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(data.generated_at));

  return (
    <main className="shell">
      <header className="topbar">
        <Brand />
        <nav aria-label="Primary navigation">
          <a className="active" href="#today">Today</a>
          <a href="#results">Results</a>
          <a href="#operations">Operations</a>
        </nav>
        <div className="header-actions">
          <button className="icon-button" aria-label="Notifications"><Bell size={18} /></button>
          <button className="avatar">TR</button>
        </div>
      </header>

      <section className="hero" id="today">
        <div>
          <p className="kicker">PHILIPPINES · OPPORTUNITY DESK</p>
          <h1>What is worth testing <em>today?</em></h1>
          <p className="hero-copy">Evidence-backed product opportunities, ranked for demand, content potential, and marketplace fit.</p>
        </div>
        <div className="status-stack">
          <span className={`connection ${apiConnected ? "connected" : "fallback"}`}>
            <CircleDot size={14} /> {apiConnected ? "API connected" : "Local fallback"}
          </span>
          <span><Clock3 size={14} /> Updated {generatedAt} PHT</span>
        </div>
      </section>

      {data.mode === "demo" && (
        <aside className="demo-banner">
          <DatabaseZap size={19} />
          <div>
            <strong>Demo evidence is active</strong>
            <span>No live source is enabled yet. These recommendations are clearly seeded and must not be posted as current claims.</span>
          </div>
        </aside>
      )}

      {data.mode === "live" && data.source_health === "degraded" && (
        <aside className="demo-banner degraded-banner" role="alert">
          <AlertTriangle size={19} />
          <div>
            <strong>Some sources are stale or failing</strong>
            <span>{data.sources.filter((source) => source.state !== "healthy" && source.state !== "disabled").map(describeSource).join(" · ")}. Treat rankings as possibly out of date.</span>
          </div>
        </aside>
      )}

      <section className="signal-section">
        <div className="section-heading">
          <div><p className="eyebrow">Demand context</p><h2>Timely business signals</h2></div>
          <span className="health"><Activity size={15} /> Source state: {data.source_health}</span>
        </div>
        <div className="signals-grid">
          {data.signals.map((signal, index) => (
            <article className="signal-card" key={signal.id}>
              <div className="signal-rank">0{index + 1}</div>
              <div>
                <div className="signal-labels"><span>{signal.event_type.replaceAll("_", " ")}</span><span>{signal.confidence}% confidence · {signal.location}</span></div>
                <h3>{signal.headline}</h3>
                <p>{signal.summary}</p>
                <div className="need-list">{signal.consumer_needs.map((need) => <span key={need}>{need}</span>)}</div>
              </div>
            </article>
          ))}
          {data.signals.length < 3 && (
            <article className="signal-card empty-signal">
              <div className="signal-rank">—</div>
              <div><span className="empty-label">QUALITY GATE</span><h3>No forced recommendations</h3><p>Empty space is intentional when evidence does not clear the confidence threshold.</p></div>
            </article>
          )}
        </div>
      </section>

      <section className="opportunities-section">
        <div className="section-heading opportunity-heading">
          <div><p className="eyebrow">Decision queue</p><h2>Top opportunities now</h2></div>
          <button className="filter-button"><SlidersHorizontal size={15} /> All opportunities <ChevronDown size={14} /></button>
        </div>
        <div className="opportunities-grid">
          {data.opportunities.map((opportunity) => <OpportunityCard key={opportunity.id} opportunity={opportunity} />)}
          <div className="next-slot">
            <span>Next qualified opportunity</span>
            <strong>Waiting for evidence</strong>
            <p>Tr3ndly will add a recommendation only when it clears eligibility and quality gates.</p>
          </div>
        </div>
      </section>

      {data.sources.length > 0 && (
        <footer className="source-footer">
          {data.sources.map((source) => (
            <span key={source.slug}>{source.attribution} · {describeSource(source)}</span>
          ))}
        </footer>
      )}
    </main>
  );
}

function describeSource(source: SourceStatus): string {
  const label = source.state.replaceAll("_", " ");
  if (!source.last_success_at) return `${source.display_name}: ${label}`;
  const updated = new Intl.DateTimeFormat("en-PH", {
    timeZone: "Asia/Manila",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(source.last_success_at));
  return `${source.display_name}: ${label}, last success ${updated} PHT`;
}

