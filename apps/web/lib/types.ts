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
    /** Present once a listing is confirmed; publish_priority then ranks the opportunity. */
    listing_economics?: number | null;
    publish_priority?: number | null;
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

export type Marketplace = "shopee" | "lazada" | "tiktok_shop" | "other";

export interface ProductMatch {
  id: string;
  opportunity_id: string;
  marketplace: Marketplace;
  product_url: string;
  affiliate_url: string;
  listing_title: string;
  seller_name: string | null;
  seller_type: "mall" | "preferred" | "standard" | null;
  price_php: number;
  commission_rate_pct: number;
  expected_commission_php: number;
  rating: number | null;
  review_count: number | null;
  sold_count: number | null;
  in_stock: boolean;
  shipping_note: string | null;
  verified_facts: string[];
  image_url: string | null;
  image_usage_note: string | null;
  notes: string | null;
  status: "candidate" | "confirmed" | "stale";
  listing_economics: number;
  economics_components: Record<string, number>;
  eligibility_checked_at: string | null;
  confirmed_at: string | null;
  created_at: string;
}

export interface SearchFailure {
  id: string;
  marketplace: Marketplace;
  query: string;
  reason: string;
  note: string | null;
  created_at: string;
}

export interface OpportunityDetail extends Opportunity {
  status: string;
  decidable: boolean;
  /** Whether listings can be added or confirmed now (accepted or matched, window open). */
  matchable: boolean;
  decisions: Decision[];
  product_matches: ProductMatch[];
  search_failures: SearchFailure[];
}

export type Platform = "tiktok" | "facebook" | "instagram" | "youtube_shorts";

export interface PolicyIssue {
  code: string;
  field: string;
  match: string;
  message: string;
  blocking: boolean;
}

export interface CreativeVariant {
  id: string;
  brief_id: string;
  parent_id: string | null;
  hook_type: string;
  hook: string;
  caption: string;
  cta: string;
  hashtags: string[];
  generator: string;
  prompt_version: string | null;
  policy_issues: PolicyIssue[];
  status: "needs_review" | "approved" | "rejected" | "exported";
  tracking_code: string | null;
  exported_at: string | null;
  created_at: string;
}

export interface CreativeBrief {
  id: string;
  product_match_id: string;
  platform: Platform;
  audience: string;
  angle: string;
  verified_facts: string[];
  forbidden_claims: string[];
  disclosure: string;
  hypothesis: string | null;
  experiment_label: string | null;
  version: string;
  created_at: string;
  variants: CreativeVariant[];
}

export interface StudioData {
  opportunity: Opportunity;
  product_match: ProductMatch;
  generator: string;
  briefs: CreativeBrief[];
}

export interface ExportPackage {
  variant_id: string;
  tracking_code: string;
  platform: Platform;
  post_text: string;
  disclosure: string;
  affiliate_url: string;
  product_url: string;
  image_url: string | null;
  image_usage_note: string | null;
  checklist: string[];
  exported_at: string;
}

export interface ResultTotals {
  posts: number;
  views: number;
  clicks: number;
  orders: number;
  gmv_php: number;
  commission_php: number;
  commission_per_post_php: number | null;
  commission_per_1000_views_php: number | null;
  click_through_rate: number | null;
  conversion_rate: number | null;
}

export interface ResultsOverview {
  assisted: ResultTotals;
  baseline: ResultTotals;
  by_category: Array<{ key: string; totals: ResultTotals }>;
  by_event_type: Array<{ key: string; totals: ResultTotals }>;
  by_hook_type: Array<{ key: string; totals: ResultTotals }>;
  warnings: string[];
}

export interface ResultsImportResult {
  rows: number;
  imported: number;
  unchanged: number;
  baseline_codes: string[];
  errors: string[];
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
