import "server-only";

import { localDemoData } from "./demo";
import type {
  Decision,
  OpportunityDetail,
  SourceRun,
  SourceStatus,
  TodayData,
  TodayFilters,
} from "./types";

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
const TIMEOUT_MS = 2500;

/** Server-side fetch to the API with the operator token. The token never reaches the browser. */
async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = process.env.API_OPERATOR_TOKEN;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
    cache: "no-store",
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
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
