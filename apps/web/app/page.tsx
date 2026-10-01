import { TodayView } from "@/components/today-view";
import { getToday } from "@/lib/api";
import type { ReasonType, TodayFilters } from "@/lib/types";

const REASONS: ReadonlyArray<ReasonType> = ["timely", "trend", "both"];

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ location?: string; reason?: string }>;
}) {
  const params = await searchParams;
  const filters: TodayFilters = {
    location: params.location || undefined,
    reason_type: REASONS.find((reason) => reason === params.reason),
  };
  const { data, apiConnected } = await getToday(filters);
  return <TodayView apiConnected={apiConnected} data={data} filters={filters} />;
}
