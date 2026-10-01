import { localDemoData } from "./demo";
import type { OpportunityDetail, TodayData } from "./types";

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function getToday(): Promise<{ data: TodayData; apiConnected: boolean }> {
  try {
    const response = await fetch(`${apiBaseUrl}/today`, {
      cache: "no-store",
      signal: AbortSignal.timeout(2500),
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    return { data: (await response.json()) as TodayData, apiConnected: true };
  } catch {
    return { data: localDemoData, apiConnected: false };
  }
}

/** Returns null only when the opportunity does not exist; API outages throw to error.tsx. */
export async function getOpportunity(id: string): Promise<OpportunityDetail | null> {
  const response = await fetch(`${apiBaseUrl}/opportunities/${encodeURIComponent(id)}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(2500),
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`API returned ${response.status}`);
  return (await response.json()) as OpportunityDetail;
}
