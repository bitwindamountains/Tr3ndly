import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { SiteHeader } from "@/components/site-header";
import { BriefForm, GenerateButton, VariantCard } from "@/components/studio-forms";
import { getStudio } from "@/lib/api";
import { formatPeso, formatPht } from "@/lib/format";

export default async function StudioPage({ params }: { params: Promise<{ matchId: string }> }) {
  const { matchId } = await params;
  const studio = await getStudio(matchId);
  if (!studio) notFound();
  const { opportunity, product_match: match } = studio;
  const confirmed = match.status === "confirmed";

  return (
    <main className="shell detail-shell">
      <SiteHeader />
      <Link className="back-link" href={`/opportunities/${opportunity.id}`}><ArrowLeft size={15} /> Back to opportunity</Link>

      <section className="hero compact-hero">
        <div>
          <p className="kicker">STUDIO · {opportunity.location.toUpperCase()}</p>
          <h1>{opportunity.product_concept}</h1>
          <p className="hero-copy">
            {match.listing_title} · {formatPeso(match.price_php)} · {match.commission_rate_pct}% commission
            {match.eligibility_checked_at && <> · checked live {formatPht(match.eligibility_checked_at)}</>}
          </p>
        </div>
      </section>

      {!confirmed && (
        <aside className="demo-banner degraded-banner" role="alert">
          <div><strong>This listing is no longer the confirmed one.</strong><span>Write copy from the opportunity&apos;s current listing.</span></div>
        </aside>
      )}

      <div className="detail-grid">
        <div className="detail-main">
          {studio.briefs.length === 0 && (
            <section className="detail-card"><p>No brief yet. Create one to generate copy.</p></section>
          )}
          {studio.briefs.map((brief) => (
            <section className="detail-card" key={brief.id}>
              <p className="eyebrow">Brief · {brief.platform.replace("_", " ")} · {brief.version}{brief.experiment_label ? ` · ${brief.experiment_label}` : ""}</p>
              <h2>{brief.angle}</h2>
              <dl className="score-table">
                <dt>Audience</dt><dd>{brief.audience}</dd>
                {brief.hypothesis && <><dt>Hypothesis</dt><dd>{brief.hypothesis}</dd></>}
              </dl>
              <p><strong>Verified facts:</strong> {brief.verified_facts.join(" · ")}</p>
              <p><strong>Do not claim:</strong> {brief.forbidden_claims.join(" · ")}</p>
              <p><strong>Disclosure added to every export:</strong> {brief.disclosure}</p>
              {confirmed && <GenerateButton briefId={brief.id} generator={studio.generator} />}
              <div className="variant-list">
                {brief.variants.map((variant) => <VariantCard key={variant.id} variant={variant} />)}
              </div>
            </section>
          ))}
        </div>

        <aside>
          {confirmed && (
            <section className="detail-card">
              <p className="eyebrow">New brief</p>
              <h2>Plan a post</h2>
              <BriefForm defaultAngle={`A practical ${opportunity.product_concept.toLowerCase()} for…`} matchId={match.id} />
            </section>
          )}
          <section className="detail-card">
            <p className="eyebrow">Why now</p>
            <p>{opportunity.why_now}</p>
            <p className="muted-note">Copy is written by {studio.generator === "template" ? "templates (set ANTHROPIC_API_KEY to use Claude)" : studio.generator}. Every variant is checked for unsupported claims and needs your approval.</p>
          </section>
        </aside>
      </div>
    </main>
  );
}
