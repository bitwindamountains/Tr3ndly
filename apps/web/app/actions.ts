"use server";

import { refresh } from "next/cache";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiPost, postDecision, type SendResult } from "@/lib/api";
import { assertOperator } from "@/lib/auth";
import {
  authConfig,
  passwordMatches,
  safeNextPath,
  SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
  signSession,
} from "@/lib/session";
import type { Decision, ResultsImportResult } from "@/lib/types";

const DECISIONS: ReadonlyArray<Decision["decision"]> = [
  "accepted",
  "rejected",
  "deferred",
  "insufficient_evidence",
];

export type ActionResult = { ok: boolean; message: string; details?: string[] };

const ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;
const UNREACHABLE: ActionResult = { ok: false, message: "Could not reach the Tr3ndly API." };
const INVALID_ID: ActionResult = { ok: false, message: "Invalid request." };

function field(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value.trim() : "";
}

function optionalField(form: FormData, name: string): string | null {
  return field(form, name) || null;
}

function optionalInt(form: FormData, name: string): number | null {
  const value = field(form, name).replaceAll(",", "");
  return value ? Number.parseInt(value, 10) : null;
}

function lines(form: FormData, name: string): string[] {
  return field(form, name)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

/** Call the API and refresh the page on success; domain errors come back as messages. */
async function send<T>(call: () => Promise<SendResult<T>>, success: string): Promise<ActionResult> {
  let result: SendResult<T>;
  try {
    result = await call();
  } catch {
    return UNREACHABLE;
  }
  if (!result.ok) return { ok: false, message: result.detail };
  refresh();
  return { ok: true, message: success };
}

export async function addProductMatch(
  opportunityId: string,
  _previous: ActionResult | null,
  form: FormData,
): Promise<ActionResult> {
  await assertOperator();
  if (!ID_PATTERN.test(opportunityId)) return INVALID_ID;
  const body = {
    marketplace: field(form, "marketplace"),
    product_url: field(form, "product_url"),
    affiliate_url: field(form, "affiliate_url"),
    listing_title: field(form, "listing_title"),
    seller_name: optionalField(form, "seller_name"),
    seller_type: optionalField(form, "seller_type"),
    price_php: field(form, "price_php").replaceAll(",", ""),
    commission_rate_pct: field(form, "commission_rate_pct"),
    rating: optionalField(form, "rating"),
    review_count: optionalInt(form, "review_count"),
    sold_count: optionalInt(form, "sold_count"),
    in_stock: form.get("in_stock") === "on",
    shipping_note: optionalField(form, "shipping_note"),
    verified_facts: lines(form, "verified_facts"),
    image_url: optionalField(form, "image_url"),
    image_usage_note: optionalField(form, "image_usage_note"),
    notes: optionalField(form, "notes"),
  };
  return send(
    () => apiPost(`/opportunities/${opportunityId}/product-match`, body),
    "Listing added. Confirm it once you have checked it is live and eligible.",
  );
}

export async function confirmProductMatch(matchId: string): Promise<ActionResult> {
  await assertOperator();
  if (!ID_PATTERN.test(matchId)) return INVALID_ID;
  return send(
    () => apiPost(`/product-matches/${matchId}/confirm`, { eligibility_confirmed: true }),
    "Listing confirmed.",
  );
}

export async function logSearchFailure(
  opportunityId: string,
  _previous: ActionResult | null,
  form: FormData,
): Promise<ActionResult> {
  await assertOperator();
  if (!ID_PATTERN.test(opportunityId)) return INVALID_ID;
  const body = {
    marketplace: field(form, "marketplace"),
    query: field(form, "query"),
    reason: field(form, "reason"),
    note: optionalField(form, "note"),
  };
  return send(() => apiPost(`/opportunities/${opportunityId}/search-failures`, body), "Search logged.");
}

export async function createBrief(
  matchId: string,
  _previous: ActionResult | null,
  form: FormData,
): Promise<ActionResult> {
  await assertOperator();
  if (!ID_PATTERN.test(matchId)) return INVALID_ID;
  const body = {
    platform: field(form, "platform"),
    angle: optionalField(form, "angle"),
    audience: optionalField(form, "audience"),
    hypothesis: optionalField(form, "hypothesis"),
    experiment_label: optionalField(form, "experiment_label"),
  };
  return send(() => apiPost(`/product-matches/${matchId}/creative-brief`, body), "Brief created.");
}

export async function generateCopy(briefId: string): Promise<ActionResult> {
  await assertOperator();
  if (!ID_PATTERN.test(briefId)) return INVALID_ID;
  return send(() => apiPost(`/creative-briefs/${briefId}/generate`), "Copy generated. Review each variant.");
}

/** Approve or reject a variant. When the form carries edited copy, the edit is saved as a new variant. */
export async function reviewCopy(
  variantId: string,
  _previous: ActionResult | null,
  form: FormData,
): Promise<ActionResult> {
  await assertOperator();
  const decision = field(form, "decision");
  if (!ID_PATTERN.test(variantId) || (decision !== "approved" && decision !== "rejected")) {
    return INVALID_ID;
  }
  const edits = form.has("hook")
    ? {
        hook: field(form, "hook"),
        caption: field(form, "caption"),
        cta: field(form, "cta"),
        hashtags: field(form, "hashtags").split(/[\s,]+/).filter(Boolean),
      }
    : null;
  const result = await send(
    () => apiPost(`/creatives/${variantId}/review`, { decision, note: optionalField(form, "note"), edits }),
    decision === "approved" ? "Approved." : "Rejected.",
  );
  // A blocked approval still saved the edit, so show it.
  if (!result.ok && edits) refresh();
  return result;
}

export async function exportCopy(variantId: string): Promise<ActionResult> {
  await assertOperator();
  if (!ID_PATTERN.test(variantId)) return INVALID_ID;
  let result: SendResult<unknown>;
  try {
    result = await apiPost(`/creatives/${variantId}/export`);
  } catch {
    return UNREACHABLE;
  }
  if (!result.ok) return { ok: false, message: result.detail };
  redirect(`/exports/${variantId}`);
}

export async function importResults(
  _previous: ActionResult | null,
  form: FormData,
): Promise<ActionResult> {
  await assertOperator();
  const file = form.get("file");
  const csv = file instanceof File && file.size > 0 ? await file.text() : field(form, "csv");
  if (!csv) return { ok: false, message: "Choose a CSV file or paste CSV rows." };
  let result: SendResult<ResultsImportResult>;
  try {
    result = await apiPost<ResultsImportResult>("/results/import", { csv });
  } catch {
    return UNREACHABLE;
  }
  if (!result.ok) return { ok: false, message: result.detail };
  refresh();
  const { imported, unchanged, baseline_codes: baseline, errors } = result.data;
  const details = [...errors];
  if (baseline.length) details.push(`Baseline (not Tr3ndly) codes: ${baseline.join(", ")}`);
  return {
    ok: errors.length === 0,
    message: `Imported ${imported} row(s); ${unchanged} unchanged; ${errors.length} with errors.`,
    details,
  };
}

export async function recordDecision(
  opportunityId: string,
  decision: Decision["decision"],
  reasonCode: string,
): Promise<ActionResult> {
  await assertOperator();
  if (!DECISIONS.includes(decision) || !/^[a-z_]{2,120}$/.test(reasonCode)) {
    return { ok: false, message: "Invalid decision." };
  }
  try {
    const result = await postDecision(opportunityId, decision, reasonCode);
    if (!result.ok) {
      return { ok: false, message: result.status === 409 ? result.detail : "Could not record the decision." };
    }
  } catch {
    return { ok: false, message: "Could not reach the Tr3ndly API." };
  }
  refresh();
  return { ok: true, message: "Decision recorded." };
}

export async function login(_previous: ActionResult | null, formData: FormData): Promise<ActionResult> {
  const config = authConfig();
  const next = safeNextPath(formData.get("next"));
  if (config) {
    const password = formData.get("password");
    if (typeof password !== "string" || !passwordMatches(config, password)) {
      return { ok: false, message: "Incorrect password." };
    }
    const cookieStore = await cookies();
    cookieStore.set(SESSION_COOKIE, signSession(config.secret), {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: SESSION_MAX_AGE_SECONDS,
    });
  }
  redirect(next);
}

export async function logout(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE);
  redirect("/login");
}
