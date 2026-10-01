import Link from "next/link";
import type { ReactNode } from "react";

import type { ReasonType, TodayFilters } from "@/lib/types";

const reasons: Array<{ value: ReasonType | undefined; label: string }> = [
  { value: undefined, label: "All reasons" },
  { value: "timely", label: "Timely" },
  { value: "trend", label: "Trend" },
  { value: "both", label: "Both" },
];

function href(filters: TodayFilters): string {
  const params = new URLSearchParams();
  if (filters.location) params.set("location", filters.location);
  if (filters.reason_type) params.set("reason", filters.reason_type);
  return params.size ? `/?${params}#queue` : "/#queue";
}

export function TodayFilterBar({ active, locations }: { active: TodayFilters; locations: string[] }) {
  return (
    <nav aria-label="Filter opportunities" className="filter-bar">
      <div>
        <Chip current={!active.location} to={href({ ...active, location: undefined })}>All locations</Chip>
        {locations.map((location) => (
          <Chip current={active.location === location} key={location} to={href({ ...active, location })}>
            {location}
          </Chip>
        ))}
      </div>
      <div>
        {reasons.map((reason) => (
          <Chip
            current={active.reason_type === reason.value}
            key={reason.label}
            to={href({ ...active, reason_type: reason.value })}
          >
            {reason.label}
          </Chip>
        ))}
      </div>
    </nav>
  );
}

function Chip({ current, to, children }: { current: boolean; to: string; children: ReactNode }) {
  return (
    <Link aria-current={current ? "true" : undefined} className={current ? "chip active" : "chip"} href={to} scroll={false}>
      {children}
    </Link>
  );
}
