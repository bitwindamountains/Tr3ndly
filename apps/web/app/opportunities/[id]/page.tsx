import { ArrowLeft, Clock3, MapPin, Search, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { confirmProductMatch } from "@/app/actions";
import { ActionButton } from "@/components/action-button";
import { DecisionPanel } from "@/components/decision-panel";
import { ListingForm, SearchFailureForm } from "@/components/listing-forms";
import { SiteHeader } from "@/components/site-header";
import { getOpportunity } from "@/lib/api";
import { formatPeso, formatPht } from "@/lib/format";
import type { ProductMatch } from "@/lib/types";

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
      <SiteHeader />
      <Link className="back-link" href="/"><ArrowLeft size={15} /> Back to Today</Link>

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
            <span><Clock3 size={15} /> Expires {new Date(opportunity.expires_at).toLocaleString("en-PH", { timeZone: "Asia/Manila", dateStyle: "medium", timeStyle: "short" })} PHT</span>
          </div>
        </div>
        <div className="priority-dial">
          <strong>{opportunity.score.publish_priority ?? opportunity.score.discovery_priority}</strong>
          <span>{opportunity.score.publish_priority != null ? "publish priority" : "discovery priority"}</span>
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
                <div><strong>{item.source_url ? <a href={item.source_url} rel="noreferrer" target="_blank">{item.source_name}</a> : item.source_name}</strong><p>{item.summary}</p><time>{new Date(item.observed_at).toLocaleString("en-PH", { timeZone: "Asia/Manila" })} PHT</time></div>
              </article>
            ))}
          </section>

          <section className="detail-card">
            <p className="eyebrow">Score breakdown · {opportunity.score.version}</p>
            <h2>How the priority was calculated</h2>
            <dl className="score-table">
              {opportunity.score.timely_score != null && <><dt>Timely demand</dt><dd>{opportunity.score.timely_score}</dd></>}
              {opportunity.score.trend_score != null && <><dt>Trend demand</dt><dd>{opportunity.score.trend_score}</dd></>}
              <dt>Combined demand</dt><dd>{opportunity.score.demand}</dd>
              <dt>Content fit</dt><dd>{opportunity.score.execution}</dd>
              <dt>Marketplace fit (prior)</dt><dd>{opportunity.score.marketplace_fit_prior}</dd>
              <dt>Uncertainty penalty</dt><dd>−{opportunity.score.uncertainty_penalty}</dd>
              <dt>Discovery priority</dt><dd><strong>{opportunity.score.discovery_priority}</strong></dd>
              {opportunity.score.listing_economics != null && <><dt>Listing economics</dt><dd>{opportunity.score.listing_economics}</dd></>}
              {opportunity.score.publish_priority != null && <><dt>Publish priority</dt><dd><strong>{opportunity.score.publish_priority}</strong></dd></>}
            </dl>
          </section>

          <section className="detail-card">
            <p className="eyebrow">Marketplace bridge</p>
            <h2>Suggested searches</h2>
            <div className="query-list">
              {opportunity.search_queries.map((query) => <code key={query}><Search size={14} /> {query}</code>)}
            </div>
          </section>

          <section className="detail-card">
            <p className="eyebrow">Product match</p>
            <h2>Affiliate listings</h2>
            {opportunity.product_matches.length === 0 ? (
              <p>No listing yet. Search the marketplace with the phrases above, then add the listing you would promote.</p>
            ) : (
              opportunity.product_matches.map((match) => (
                <MatchRow key={match.id} match={match} matchable={opportunity.matchable} />
              ))
            )}
            {opportunity.matchable ? (
              <details className="form-details">
                <summary>Add a listing</summary>
                <ListingForm opportunityId={opportunity.id} />
              </details>
            ) : (
              <p className="muted-note">Accept this opportunity to add a listing.</p>
            )}
            <details className="form-details">
              <summary>Log a search that found nothing usable ({opportunity.search_failures.length} logged)</summary>
              <SearchFailureForm defaultQuery={opportunity.search_queries[0] ?? ""} opportunityId={opportunity.id} />
              {opportunity.search_failures.length > 0 && (
                <ul>
                  {opportunity.search_failures.map((failure) => (
                    <li key={failure.id}>{failure.marketplace}: “{failure.query}”, {failure.reason.replaceAll("_", " ")}</li>
                  ))}
                </ul>
              )}
            </details>
          </section>

          <section className="detail-card">
            <p className="eyebrow">Uncertainty</p>
            <h2>What could weaken this opportunity</h2>
            <ul>{opportunity.uncertainties.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
        </div>

        <aside>
          <DecisionPanel closed={!opportunity.decidable} opportunityId={opportunity.id} />
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

function MatchRow({ match, matchable }: { match: ProductMatch; matchable: boolean }) {
  return (
    <article className={`match-row match-${match.status}`}>
      <div className="match-head">
        <div>
          <strong><a href={match.product_url} rel="noreferrer" target="_blank">{match.listing_title}</a></strong>
          <small>{match.marketplace.replace("_", " ")}{match.seller_name ? ` · ${match.seller_name}` : ""}{match.seller_type ? ` (${match.seller_type})` : ""}</small>
        </div>
        <span className={`state state-${match.status}`}>{match.status}</span>
      </div>
      <dl className="match-facts">
        <div><dt>Price</dt><dd>{formatPeso(match.price_php)}</dd></div>
        <div><dt>Commission</dt><dd>{match.commission_rate_pct}% ≈ {formatPeso(match.expected_commission_php)}</dd></div>
        <div><dt>Rating</dt><dd>{match.rating != null ? `${match.rating} (${match.review_count ?? 0})` : "—"}</dd></div>
        <div><dt>Sold</dt><dd>{match.sold_count?.toLocaleString("en-PH") ?? "—"}</dd></div>
        <div><dt>Economics</dt><dd><strong>{match.listing_economics}</strong>/100</dd></div>
        <div><dt>Stock</dt><dd>{match.in_stock ? "In stock" : "Out of stock"}</dd></div>
      </dl>
      {match.verified_facts.length > 0 && <p className="muted-note">Verified facts: {match.verified_facts.join(" · ")}</p>}
      {match.eligibility_checked_at && <p className="muted-note">Last checked live {formatPht(match.eligibility_checked_at)}</p>}
      <div className="button-row">
        {matchable && match.status !== "stale" && (
          <ActionButton
            action={confirmProductMatch.bind(null, match.id)}
            label={match.status === "confirmed" ? "Re-check: still live and eligible" : "Confirm: live and affiliate-eligible"}
            pendingLabel="Confirming…"
          />
        )}
        {match.status === "confirmed" && <Link className="button" href={`/studio/${match.id}`}>Open studio</Link>}
      </div>
    </article>
  );
}
