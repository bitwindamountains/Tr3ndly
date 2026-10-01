import type { TodayData } from "./types";

const now = new Date();
const expiry = new Date(now.getTime() + 36 * 60 * 60 * 1000);

export const localDemoData: TodayData = {
  generated_at: now.toISOString(),
  mode: "demo",
  source_health: "demo",
  sources: [],
  signals: [
    {
      id: "signal_demo_heat",
      headline: "Hot daytime conditions create a practical cooling need",
      event_type: "HEAT_CONDITION",
      location: "Metro Manila",
      summary: "Seeded data demonstrates the evidence-to-opportunity workflow while live sources are disabled.",
      confidence: 78,
      consumer_needs: ["personal cooling", "hydration", "sun protection"],
      timely_score: 78,
      sensitivity: "low",
      expires_at: expiry.toISOString(),
    },
  ],
  opportunities: [
    {
      id: "demo_opp_fan",
      product_concept: "Portable rechargeable fan",
      category: "Household convenience",
      reason_type: "timely",
      why_now: "Warm daytime conditions may increase interest in portable personal cooling.",
      target_user: "Commuters, students, and households",
      location: "Metro Manila",
      expires_at: expiry.toISOString(),
      score: {
        demand: 76,
        execution: 84,
        marketplace_fit_prior: 80,
        uncertainty_penalty: 8,
        discovery_priority: 70,
        version: "discovery-v0.1",
      },
      search_queries: [
        "portable rechargeable fan",
        "mini fan USB rechargeable",
        "handheld fan long battery",
      ],
      uncertainties: [
        "No affiliate listing has been matched yet.",
        "This is seeded demo data, not a live weather recommendation.",
      ],
      evidence: [
        {
          source_name: "Demo weather source",
          source_url: null,
          observed_at: now.toISOString(),
          summary: "Elevated apparent temperatures are expected during daytime hours.",
        },
      ],
    },
  ],
};

