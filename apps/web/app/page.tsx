import { TodayView } from "@/components/today-view";
import { getToday } from "@/lib/api";

export default async function HomePage() {
  const { data, apiConnected } = await getToday();
  return <TodayView data={data} apiConnected={apiConnected} />;
}

