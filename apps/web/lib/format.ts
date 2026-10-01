import type { SourceStatus } from "./types";

const pht = new Intl.DateTimeFormat("en-PH", {
  timeZone: "Asia/Manila",
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

/** Philippine time, e.g. "Oct 2, 1:56 AM PHT". */
export function formatPht(iso: string): string {
  return `${pht.format(new Date(iso))} PHT`;
}

export function describeSource(source: SourceStatus): string {
  const label = source.state.replaceAll("_", " ");
  if (!source.last_success_at) return `${source.display_name}: ${label}`;
  return `${source.display_name}: ${label}, last success ${formatPht(source.last_success_at)}`;
}
