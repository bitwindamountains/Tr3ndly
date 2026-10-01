import { ArrowUpRight, Clock3, MapPin, Search, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";

import type { Opportunity } from "@/lib/types";

function hoursUntil(isoDate: string): number {
  return Math.max(0, Math.round((new Date(isoDate).getTime() - Date.now()) / 3_600_000));
}

export function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  return (
    <article className="opportunity-card">
      <div className="card-topline">
        <span className={`reason-pill reason-${opportunity.reason_type}`}>
          <Sparkles size={13} /> {opportunity.reason_type}
        </span>
        <span className="score"><strong>{opportunity.score.discovery_priority}</strong>/100</span>
      </div>

      <div>
        <p className="eyebrow">{opportunity.category}</p>
        <h3>{opportunity.product_concept}</h3>
        <p className="why-now">{opportunity.why_now}</p>
      </div>

      <div className="meta-row">
        <span><MapPin size={15} /> {opportunity.location}</span>
        <span><Clock3 size={15} /> {hoursUntil(opportunity.expires_at)}h window</span>
      </div>

      <div className="score-bars" aria-label="Score breakdown">
        <ScoreBar label="Demand" value={opportunity.score.demand} />
        <ScoreBar label="Content fit" value={opportunity.score.execution} />
        <ScoreBar label="Market fit" value={opportunity.score.marketplace_fit_prior} />
      </div>

      <div className="search-box">
        <span className="search-title"><Search size={14} /> Search starting point</span>
        <code>{opportunity.search_queries[0]}</code>
      </div>

      <div className="card-footer">
        <span className="evidence"><ShieldCheck size={15} /> {opportunity.evidence.length} evidence item</span>
        <Link href={`/opportunities/${opportunity.id}`}>
          Review opportunity <ArrowUpRight size={16} />
        </Link>
      </div>
    </article>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-bar">
      <div><span>{label}</span><strong>{value}</strong></div>
      <div className="bar-track"><span style={{ width: `${value}%` }} /></div>
    </div>
  );
}
