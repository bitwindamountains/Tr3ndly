"use client";

import Link from "next/link";
import { useActionState, useState } from "react";

import { createBrief, exportCopy, generateCopy, reviewCopy } from "@/app/actions";
import type { CreativeVariant } from "@/lib/types";
import { ActionButton, FormMessage } from "./action-button";

export function BriefForm({ matchId, defaultAngle }: { matchId: string; defaultAngle: string }) {
  const [state, action, pending] = useActionState(createBrief.bind(null, matchId), null);

  return (
    <form action={action} className="stack-form">
      <div className="form-grid">
        <label>
          Platform
          <select name="platform" defaultValue="tiktok" required>
            <option value="tiktok">TikTok</option>
            <option value="facebook">Facebook</option>
            <option value="instagram">Instagram</option>
            <option value="youtube_shorts">YouTube Shorts</option>
          </select>
        </label>
        <label>Experiment label<input name="experiment_label" maxLength={120} placeholder="heat-fan-A" /></label>
        <label className="span-2">Angle<input name="angle" maxLength={500} placeholder={defaultAngle} /></label>
        <label className="span-2">Audience (leave empty for the opportunity&apos;s audience)<input name="audience" maxLength={240} /></label>
        <label className="span-2">Hypothesis<input name="hypothesis" maxLength={1000} placeholder="A practical hook beats a curiosity hook for this product" /></label>
      </div>
      <button className="button" disabled={pending} type="submit">{pending ? "Saving…" : "Create brief"}</button>
      <FormMessage state={state} />
    </form>
  );
}

export function GenerateButton({ briefId, generator }: { briefId: string; generator: string }) {
  return (
    <ActionButton
      action={generateCopy.bind(null, briefId)}
      label={generator === "template" ? "Generate copy (template)" : "Generate copy with Claude"}
      pendingLabel="Generating…"
    />
  );
}

const STATUS_LABELS: Record<CreativeVariant["status"], string> = {
  needs_review: "Needs review",
  approved: "Approved",
  rejected: "Rejected",
  exported: "Exported",
};

export function VariantCard({ variant }: { variant: CreativeVariant }) {
  const [editing, setEditing] = useState(false);
  const [state, action, pending] = useActionState(reviewCopy.bind(null, variant.id), null);
  const reviewable = variant.status === "needs_review" || variant.status === "approved";
  const blocking = variant.policy_issues.filter((issue) => issue.blocking);

  return (
    <article className={`variant-card variant-${variant.status}`}>
      <div className="variant-topline">
        <span className="state">{variant.hook_type}</span>
        <span className={`state state-${variant.status}`}>{STATUS_LABELS[variant.status]}</span>
        <small>{variant.generator}{variant.parent_id ? " · edited" : ""}</small>
      </div>

      {editing ? (
        <form action={action} className="stack-form">
          <label>Hook<input name="hook" defaultValue={variant.hook} required /></label>
          <label>Caption<textarea name="caption" defaultValue={variant.caption} rows={6} required /></label>
          <label>Call to action<input name="cta" defaultValue={variant.cta} required /></label>
          <label>Hashtags<input name="hashtags" defaultValue={variant.hashtags.join(" ")} /></label>
          <div className="button-row">
            <button className="button" disabled={pending} name="decision" type="submit" value="approved">Save and approve</button>
            <button className="button secondary" onClick={() => setEditing(false)} type="button">Cancel</button>
          </div>
        </form>
      ) : (
        <div className="variant-copy">
          <strong>{variant.hook}</strong>
          <p>{variant.caption}</p>
          <p className="variant-cta">{variant.cta}</p>
          {variant.hashtags.length > 0 && <p className="variant-tags">{variant.hashtags.join(" ")}</p>}
        </div>
      )}

      {variant.policy_issues.length > 0 && (
        <ul className="issue-list" aria-label="Policy issues">
          {variant.policy_issues.map((issue) => (
            <li className={issue.blocking ? "blocking" : "warning"} key={`${issue.code}-${issue.field}-${issue.match}`}>
              <strong>{issue.blocking ? "Blocked" : "Warning"}:</strong> “{issue.match}” in {issue.field}. {issue.message}
            </li>
          ))}
        </ul>
      )}

      {!editing && (
        <div className="button-row">
          {reviewable && (
            <form action={action} className="inline-form">
              <button className="button" disabled={pending || blocking.length > 0} name="decision" type="submit" value="approved">Approve</button>
              <button className="button secondary" disabled={pending} name="decision" type="submit" value="rejected">Reject</button>
            </form>
          )}
          {variant.status !== "exported" && (
            <button className="button secondary" onClick={() => setEditing(true)} type="button">Edit a copy</button>
          )}
          {variant.status === "approved" && (
            <ActionButton action={exportCopy.bind(null, variant.id)} label="Export" pendingLabel="Exporting…" />
          )}
          {variant.status === "exported" && (
            <Link className="button" href={`/exports/${variant.id}`}>View export · {variant.tracking_code}</Link>
          )}
        </div>
      )}
      <FormMessage state={state} />
    </article>
  );
}
