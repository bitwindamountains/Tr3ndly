import "server-only";

import { localDemoData } from "./demo";
import type {
  Decision,
  ExportPackage,
  OpportunityDetail,
  ResultsOverview,
  SourceRun,
  SourceStatus,
  StudioData,
  TodayData,
  TodayFilters,
} from "./types";

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
const TIMEOUT_MS = 2500;
// Copy generation can call a model, which takes far longer than a read.
const MUTATION_TIMEOUT_MS = 180_000;

/** Server-side fetch to the API with the operator token. The token never reaches the browser. */
async function apiFetch(
  path: string,
  init: RequestInit = {},
  timeoutMs: number = TIMEOUT_MS,
): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = process.env.API_OPERATOR_TOKEN;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
    cache: "no-store",
    signal: AbortSignal.timeout(timeoutMs),
  });
}

export type SendResult<T> = { ok: true; data: T } | { ok: false; status: number; detail: string };

/** POST JSON to the API. Domain errors (404/409/422/502) come back as `detail` messages. */
export async function apiPost<T>(path: string, body: unknown = {}): Promise<SendResult<T>> {
  const response = await apiFetch(
    path,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) },
    MUTATION_TIMEOUT_MS,
  );
  if (response.ok) return { ok: true, data: (await response.json()) as T };
  const payload = (await response.json().catch(() => ({}))) as { detail?: unknown };
  return { ok: false, status: response.status, detail: describeDetail(payload.detail, response.status) };
}

function describeDetail(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  // FastAPI validation errors: [{ loc: [..., "field"], msg }]
  if (Array.isArray(detail)) {
    return detail
      .map((item: { loc?: unknown[]; msg?: string }) => {
        const field = Array.isArray(item.loc) ? String(item.loc[item.loc.length - 1]) : "input";
        return `${field.replaceAll("_", " ")}: ${item.msg ?? "invalid"}`;
      })
      .join("; ");
  }
  return `API returned ${status}`;
}

/** Returns null when the record does not exist; API outages throw to error.tsx. */
async function getOrNull<T>(path: string): Promise<T | null> {
  const response = await apiFetch(path);
  if (response.status === 404) return null;
  return json<T>(response);
}

export function getStudio(matchId: string): Promise<StudioData | null> {
  return getOrNull<StudioData>(`/product-matches/${encodeURIComponent(matchId)}/studio`);
}

export function getExport(variantId: string): Promise<ExportPackage | null> {
  return getOrNull<ExportPackage>(`/creatives/${encodeURIComponent(variantId)}/export`);
}

export async function getResultsOverview(): Promise<ResultsOverview> {
  return json<ResultsOverview>(await apiFetch("/results/overview"));
}

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(`API returned ${response.status}`);
  return (await response.json()) as T;
}

export async function getToday(
  filters: TodayFilters = {},
): Promise<{ data: TodayData; apiConnected: boolean }> {
  const params = new URLSearchParams();
  if (filters.location) params.set("location", filters.location);
  if (filters.reason_type) params.set("reason_type", filters.reason_type);
  const query = params.size ? `?${params}` : "";
  try {
    return { data: await json<TodayData>(await apiFetch(`/today${query}`)), apiConnected: true };
  } catch {
    return { data: localDemoData, apiConnected: false };
  }
}

/** Returns null only when the opportunity does not exist; API outages throw to error.tsx. */
export async function getOpportunity(id: string): Promise<OpportunityDetail | null> {
  const response = await apiFetch(`/opportunities/${encodeURIComponent(id)}`);
  if (response.status === 404) return null;
  return json<OpportunityDetail>(response);
}

export async function getOperations(): Promise<{ sources: SourceStatus[]; runs: SourceRun[] }> {
  const [sources, runs] = await Promise.all([
    apiFetch("/operations/sources").then((response) => json<SourceStatus[]>(response)),
    apiFetch("/operations/runs?limit=25").then((response) => json<SourceRun[]>(response)),
  ]);
  return { sources, runs };
}

export async function postDecision(
  opportunityId: string,
  decision: Decision["decision"],
  reasonCode: string,
): Promise<{ ok: true } | { ok: false; status: number; detail: string }> {
  const response = await apiFetch(`/opportunities/${encodeURIComponent(opportunityId)}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, reason_code: reasonCode }),
  });
  if (response.ok) return { ok: true };
  const body = (await response.json().catch(() => ({}))) as { detail?: unknown };
  return {
    ok: false,
    status: response.status,
    detail: typeof body.detail === "string" ? body.detail : `API returned ${response.status}`,
  };
}
