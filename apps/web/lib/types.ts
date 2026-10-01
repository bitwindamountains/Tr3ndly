export type ReasonType = "timely" | "trend" | "both";

export interface Evidence {
  source_name: string;
  source_url: string | null;
  observed_at: string;
  summary: string;
}

export interface Opportunity {
  id: string;
  product_concept: string;
  category: string;
  reason_type: ReasonType;
  why_now: string;
  target_user: string;
  location: string;
  expires_at: string;
  score: {
    demand: number;
    execution: number;
    marketplace_fit_prior: number;
    uncertainty_penalty: number;
    discovery_priority: number;
    timely_score?: number | null;
    trend_score?: number | null;
    version: string;
  };
  search_queries: string[];
  uncertainties: string[];
  evidence: Evidence[];
}

export interface Decision {
  id: string;
  opportunity_id: string;
  decision: "accepted" | "rejected" | "deferred" | "insufficient_evidence";
  reason_code: string;
  note: string | null;
  score_version: string;
  created_at: string;
}

export interface OpportunityDetail extends Opportunity {
  status: string;
  decidable: boolean;
  decisions: Decision[];
}

export interface SourceStatus {
  slug: string;
  display_name: string;
  state: "healthy" | "degraded" | "failing" | "never_run" | "disabled";
  poll_interval_minutes: number;
  attribution: string;
  last_run_at: string | null;
  last_success_at: string | null;
  last_error: string | null;
}

export interface TodayData {
  generated_at: string;
  mode: "demo" | "live";
  source_health: "healthy" | "degraded" | "demo";
  sources: SourceStatus[];
  locations: string[];
  signals: Array<{
    id: string;
    headline: string;
    event_type: string;
    location: string;
    summary: string;
    confidence: number;
    consumer_needs: string[];
    timely_score: number;
    sensitivity: string;
    expires_at: string;
  }>;
  opportunities: Opportunity[];
}

export interface TodayFilters {
  location?: string;
  reason_type?: ReasonType;
}

export interface SourceRun {
  id: string;
  source: string;
  status: "running" | "succeeded" | "failed";
  started_at: string;
  finished_at: string | null;
  error: string | null;
  stats: Record<string, number>;
}
