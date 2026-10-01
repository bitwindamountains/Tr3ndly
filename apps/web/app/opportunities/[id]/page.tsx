import { ArrowLeft, Clock3, MapPin, Search, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Brand } from "@/components/brand";
import { DecisionPanel } from "@/components/decision-panel";
import { getOpportunity } from "@/lib/api";

export default async function OpportunityPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const opportunity = await getOpportunity(id);
  if (!opportunity) notFound();

  return (
    <main className="shell detail-shell">
      <header className="detail-header">
        <Brand />
        <Link href="/"><ArrowLeft size={15} /> Back to Today</Link>
      </header>

      <section className="detail-hero">
        <div>
          <div className="detail-tags">
            <span>{opportunity.reason_type}</span>
            <span>{opportunity.status}</span>
            <span>{opportunity.score.version}</span>
          </div>
          <p className="eyebrow">{opportunity.category}</p>
          <h1>{opportunity.product_concept}</h1>
          <p>{opportunity.why_now}</p>
          <div className="meta-row">
            <span><MapPin size={15} /> {opportunity.location}</span>
            <span><Clock3 size={15} /> Expires {new Date(opportunity.expires_at).toLocaleDateString("en-PH")}</span>
          </div>
        </div>
        <div className="priority-dial">
          <strong>{opportunity.score.discovery_priority}</strong>
          <span>discovery priority</span>
        </div>
      </section>

      <div className="detail-grid">
        <div className="detail-main">
          <section className="detail-card">
            <p className="eyebrow">Evidence</p>
            <h2>Why Tr3ndly surfaced this</h2>
            {opportunity.evidence.map((item) => (
              <article className="evidence-row" key={`${item.source_name}-${item.observed_at}`}>
                <ShieldCheck size={18} />
                <div><strong>{item.source_name}</strong><p>{item.summary}</p><time>{new Date(item.observed_at).toLocaleString("en-PH")}</time></div>
              </article>
            ))}
          </section>

          <section className="detail-card">
            <p className="eyebrow">Marketplace bridge</p>
            <h2>Suggested searches</h2>
            <div className="query-list">
              {opportunity.search_queries.map((query) => <code key={query}><Search size={14} /> {query}</code>)}
            </div>
          </section>

          <section className="detail-card">
            <p className="eyebrow">Uncertainty</p>
            <h2>What could weaken this opportunity</h2>
            <ul>{opportunity.uncertainties.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
        </div>

        <aside>
          <DecisionPanel opportunityId={opportunity.id} />
          <section className="detail-card decision-history">
            <p className="eyebrow">Audit trail</p>
            <h2>Recent decisions</h2>
            {opportunity.decisions.length === 0 ? <p>No decisions recorded yet.</p> : opportunity.decisions.map((decision) => (
              <div key={decision.id}><strong>{decision.decision.replaceAll("_", " ")}</strong><span>{decision.reason_code.replaceAll("_", " ")}</span></div>
            ))}
          </section>
        </aside>
      </div>
    </main>
  );
}
