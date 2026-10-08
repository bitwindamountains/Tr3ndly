import { ArrowLeft, ExternalLink } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CopyButton } from "@/components/copy-button";
import { SiteHeader } from "@/components/site-header";
import { getExport } from "@/lib/api";
import { formatPht } from "@/lib/format";

export default async function ExportPage({ params }: { params: Promise<{ variantId: string }> }) {
  const { variantId } = await params;
  const pack = await getExport(variantId);
  if (!pack) notFound();

  return (
    <main className="shell detail-shell">
      <SiteHeader />
      <Link className="back-link" href="/results"><ArrowLeft size={15} /> Results</Link>

      <section className="hero compact-hero">
        <div>
          <p className="kicker">EXPORT · {pack.platform.replace("_", " ").toUpperCase()}</p>
          <h1>Ready to post</h1>
          <p className="hero-copy">Exported {formatPht(pack.exported_at)}. Tracking code <code>{pack.tracking_code}</code>.</p>
        </div>
      </section>

      <div className="detail-grid">
        <div className="detail-main">
          <section className="detail-card">
            <p className="eyebrow">Caption</p>
            <h2>Post text</h2>
            <pre className="post-text">{pack.post_text}</pre>
            <div className="button-row">
              <CopyButton label="Copy post text" text={pack.post_text} />
              <CopyButton label="Copy tracking code" text={pack.tracking_code} />
            </div>
          </section>
          <section className="detail-card">
            <p className="eyebrow">Links</p>
            <h2>Listing and affiliate link</h2>
            <ul className="link-list">
              <li><a href={pack.affiliate_url} rel="noreferrer" target="_blank">Affiliate link <ExternalLink size={13} /></a> <CopyButton label="Copy" text={pack.affiliate_url} /></li>
              <li><a href={pack.product_url} rel="noreferrer" target="_blank">Listing <ExternalLink size={13} /></a></li>
              {pack.image_url && <li><a href={pack.image_url} rel="noreferrer" target="_blank">Product image <ExternalLink size={13} /></a>{pack.image_usage_note ? ` (${pack.image_usage_note})` : ""}</li>}
            </ul>
          </section>
        </div>
        <aside>
          <section className="decision-panel">
            <p className="eyebrow">Before you post</p>
            <h2>Checklist</h2>
            <ol className="checklist">{pack.checklist.map((step) => <li key={step}>{step}</li>)}</ol>
          </section>
        </aside>
      </div>
    </main>
  );
}
