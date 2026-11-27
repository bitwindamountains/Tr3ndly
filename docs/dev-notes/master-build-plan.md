# Tr3ndly — Master Build and Validation Plan
## Demand intelligence for Philippine affiliate creators

**Version:** 2.0  
**Status:** Planning baseline  
**Last reviewed:** 2026-09-10  
**Primary objective:** Prove that Tr3ndly helps one operator choose and publish more profitable affiliate content with less research time.

---

# 1. Executive Decision

Build Tr3ndly as a **decision and experimentation system first**, not as an autonomous content factory.

The product must prove this loop:

```text
current demand signal
→ commercially useful product opportunity
→ eligible, competitive affiliate listing
→ truthful, publishable content
→ measured result
→ better next decision
```

The first release succeeds only if it improves one or more of:

- revenue per published post;
- affiliate click-through or conversion rate;
- time from research to published post;
- consistency of finding products worth testing.

Signal ingestion, AI generation, dashboards, and publishing integrations are supporting capabilities. They are not the product outcome.

## Build order

1. Validate recommendations manually using real posts and real affiliate results.
2. Build the smallest operator cockpit that removes repeated work.
3. Automate creative production only after product selection is useful.
4. Add more sources and publishing integrations only after they improve measured outcomes.
5. Consider a multi-user SaaS only after the single-operator workflow repeatedly creates value.

---

# 2. Product Thesis

Affiliate creators usually choose products from bestseller lists, marketplace browsing, social feeds, or intuition. These methods expose what is already visible, but they do not consistently answer:

> What should I promote today, for whom, with which listing and angle, and what evidence supports that choice?

Tr3ndly combines two independent forms of demand:

## Trending demand

A product or category is gaining purchase-oriented attention.

## Timely demand

A current event, forecast, season, calendar moment, or local condition creates a practical near-term need.

Examples:

```text
heat forecast → portable fan, insulated bottle
scheduled outage → rechargeable light, power bank
heavy rain → rain cover, dry bag, shoe cover
school opening → organizers, bags, desk accessories
product search acceleration → eligible listings in that category
```

Tr3ndly's initial advantage is not access to a secret dataset. It is the disciplined combination of:

- evidence-backed demand detection;
- Philippine geographic and cultural context;
- affiliate listing economics and availability;
- content-angle generation;
- a proprietary record of what the operator tested and what earned money.

The durable asset is the **closed-loop decision dataset**, not generic AI-generated copy.

---

# 3. Initial Customer and Market Wedge

## Primary user

A Philippines-based TikTok Shop or Shopee affiliate operator who:

- publishes at least several product posts per week;
- selects products personally;
- can access marketplace affiliate listings and metrics;
- wants faster research and more defensible product choices;
- accepts a human approval and manual-posting workflow.

## First content lanes

Start with two or three low-regulatory-risk lanes:

1. household convenience and preparedness;
2. student, commuter, and work-from-home utility;
3. seasonal organization, comfort, and everyday accessories.

Do not begin with supplements, medical devices, financial products, infant safety, disaster-survival claims, or other categories where a content error could cause disproportionate harm.

## Positioning

Use this promise during validation:

> Tr3ndly gives Philippine affiliate creators a ranked daily shortlist of products worth testing, explains why demand may exist now, and turns a chosen listing into truthful, ready-to-post content.

Do not promise guaranteed virality, guaranteed conversion, passive income, or fully autonomous posting.

---

# 4. Assumptions That Must Be Proven

| Assumption | Test | Pass signal | If false |
|---|---|---|---|
| Timely signals predict useful product demand | Manually produce daily opportunities for 2–4 weeks | Operator accepts at least 40% for marketplace search | Narrow event types or remove timely lane |
| Trend signals add information beyond marketplace bestsellers | Compare trend-led picks with bestseller-only picks | Trend-led cohort improves a business metric or finds opportunities earlier | Treat marketplace data as primary |
| Eligible listings can be found quickly | Time 30 product-match sessions | Median match time ≤10 minutes | Improve queries or integrate permitted imports |
| Content generation saves work | Compare normal workflow with Tr3ndly-assisted workflow | Median research-to-export time falls ≥30% | Simplify or remove low-value generation steps |
| Recommendations improve performance | Run labeled post experiments | Directional lift after controlling for account, posting window, category, and format | Rework ranking before adding automation |
| Operators trust the explanation | Record accept/reject reason for every recommendation | Most accepted recommendations cite useful evidence | Improve evidence and uncertainty display |

These thresholds are product gates, not claims of statistical significance. Keep raw results and confidence intervals; do not overstate small samples.

---

# 5. Non-Negotiable Product Principles

1. **Evidence before generation.** No opportunity without traceable evidence.
2. **Need before product.** Timely events map to consumer needs before product concepts.
3. **Listing before creative.** Do not create exact-product content until an eligible listing and its facts are supplied.
4. **Truth before persuasion.** Unverified product claims never enter published content.
5. **Human approval.** No scheduler or integration may bypass approval.
6. **Uncertainty is visible.** Show missing data, conflicts, freshness, and confidence.
7. **No forced recommendations.** Fewer than three is correct when evidence is weak.
8. **Measure decisions, not dashboard activity.** Optimize for useful picks, posts, clicks, orders, commission, and time saved.
9. **Manual paths remain valid.** Every external integration has a manual import/export fallback.
10. **No unauthorized marketplace or publisher scraping.** Access method and usage rights are explicit per source.

---

# 6. Scope by Release

## Release 0 — Concierge validation

No production application is required.

Use a spreadsheet or lightweight local tool to:

- collect a small daily set of signals;
- create and score opportunities;
- record why each was accepted or rejected;
- record marketplace match time, price, commission, seller/listing facts;
- create content briefs;
- publish manually;
- capture post and affiliate results.

Run this with one real operator for at least 2 weeks and preferably 30+ published content units across the selected lanes.

**Gate to Release 1:** The workflow produces repeated acceptable opportunities, listings can be found, and the operator wants to continue using it.

## Release 1 — Operator cockpit

Build only:

- source ingestion for the two most useful sources proven in Release 0;
- raw evidence storage and source health;
- deterministic normalization and exact deduplication;
- relevance, sensitivity, expiry, and opportunity scoring;
- a Today queue with accept/reject/defer feedback;
- manual marketplace match and image upload;
- content brief and copy variants;
- approval and export;
- manual metrics entry or CSV import;
- experiment labels and basic results.

Do not build semantic clustering, AI image editing, Remotion, direct publishing, a broad analytics suite, or Google Trends integration unless Release 0 evidence requires it.

**Gate to Release 2:** At least 70% of published content can be completed through the cockpit without reverting to an outside research workflow, and measured time-to-export improves.

## Release 2 — Creative acceleration

Add, in order:

1. reusable creative templates;
2. deterministic 9:16 slideshow/video rendering;
3. image background/layout editing using the actual product image;
4. visual fidelity checks;
5. creative variant experiments.

**Gate to Release 3:** Creative approval rate is ≥70%, material product-fidelity failures are <2% after review, and generation cost is acceptable relative to expected commission.

## Release 3 — Source and workflow expansion

Candidates:

- semantic event clustering if duplicates consume material operator time;
- additional news/event sources;
- permitted marketplace CSV/import adapters;
- official trend or commerce data integrations;
- platform analytics connectors;
- draft upload or official publishing.

Each addition needs a before/after metric and an owner. “More data” is not a sufficient reason.

## Release 4 — SaaS readiness

Only after the operator workflow demonstrates repeatable value across multiple accounts or users:

- organizations and roles;
- onboarding;
- per-tenant secrets and source configuration;
- quotas and billing;
- audit logs and account isolation;
- support and data-retention operations.

---

# 7. End-to-End User Journey

```text
1. Sources provide current demand evidence.
2. Tr3ndly normalizes, deduplicates, and expires evidence.
3. Policy gates remove irrelevant, unsafe, stale, or unverified candidates.
4. The system infers consumer needs and generic product concepts.
5. It ranks concepts using demand, execution, economics, and uncertainty.
6. The operator accepts, rejects, or defers a recommendation.
7. Tr3ndly supplies marketplace search phrases and listing requirements.
8. The operator confirms an affiliate-eligible listing and product facts.
9. Tr3ndly creates a versioned brief and a small set of content variants.
10. Automated checks and human approval run.
11. The operator exports and manually posts the content.
12. Results are imported and linked to the original decision and variant.
13. A weekly review changes hypotheses, not weights automatically.
```

Every recommendation detail must answer:

- Why now?
- Who is likely to care?
- Where is the evidence?
- How long may the opportunity last?
- What could make the inference wrong?
- What listing characteristics matter?
- What content angle is truthful and useful?

---

# 8. Opportunity Eligibility Gates

Scoring happens only after hard gates.

## Signal/event gates

- Philippine relevance or chosen target geography;
- current and not expired;
- at least one allowed source with retrievable provenance;
- business relevance above threshold;
- sensitivity not blocked;
- consumer need is concrete and near-term;
- product framing is appropriate.

High-impact alerts require official or first-party confirmation. News repetition alone does not make a hazardous event true.

## Product-concept gates

- ordinary lawful product category;
- plausible connection to the stated need;
- no prohibited or high-risk claims required to sell the angle;
- likely discoverable on the target affiliate marketplace;
- not already saturated in the operator's recent content unless intentionally retesting.

## Listing gates before creative generation

- operator confirms current affiliate eligibility;
- affiliate link or permitted marketplace reference exists;
- price and commission are captured with timestamps;
- seller and fulfillment facts needed by the operator are captured;
- supplied product images may be used for the intended workflow;
- exact claims are supported by listing facts or supplied documentation;
- prohibited/restricted category policy passes.

A high score cannot override a failed gate.

---

# 9. Ranking Model

Do not reduce the decision to “trending versus timely.” A product can have strong demand evidence and still be a poor affiliate opportunity.

## 9.1 Demand score

Store `timely_score` and `trend_score` independently, each 0–100.

### Timely dimensions

```text
freshness
geographic relevance
affected reach
need strength
product actionability
source confidence
useful opportunity window
sensitivity penalty
```

Initial heuristic:

```text
timely_score =
  0.15*freshness +
  0.15*geography +
  0.10*reach +
  0.25*need_strength +
  0.20*actionability +
  0.15*source_confidence -
  sensitivity_penalty
```

### Trend dimensions

```text
velocity
persistence
cross-source confirmation
purchase intent
recency
```

Initial heuristic:

```text
trend_score =
  0.30*velocity +
  0.20*persistence +
  0.20*cross_source +
  0.20*purchase_intent +
  0.10*recency
```

Each source owns a documented normalization function. Raw ranks from different providers are never compared directly.

### Combined demand

```text
demand_score = min(
  100,
  max(timely_score, trend_score)
  + 0.15 * min(timely_score, trend_score)
)
```

## 9.2 Execution score

Estimate whether the opportunity can become compelling, truthful content:

```text
audience fit
demonstrability
visual clarity
angle novelty
operator/category fit
production effort
recent content saturation
```

## 9.3 Listing economics score

Calculated only when a listing is available:

```text
commission amount, not rate alone
price-band conversion prior
seller/listing quality indicators
shipping/fulfillment suitability
stock/eligibility freshness
rating/review evidence when permitted
return/refund risk proxy when available
```

Do not optimize for commission rate alone. Expected commission per qualified view is the eventual target.

## 9.4 Uncertainty and effort

Track:

- missing fields;
- conflicting evidence;
- source age;
- inference confidence;
- estimated minutes to match and produce;
- expected opportunity lifetime.

## 9.5 Priority score

Before a listing is matched:

```text
discovery_priority =
  0.55*demand_score +
  0.30*execution_score +
  0.15*marketplace_fit_prior -
  uncertainty_penalty -
  saturation_penalty
```

After matching:

```text
publish_priority =
  0.40*demand_score +
  0.25*execution_score +
  0.30*listing_economics_score +
  0.05*learning_value -
  uncertainty_penalty -
  effort_penalty
```

Weights are explicitly provisional. Version them and change them only through a recorded evaluation. Preserve component scores so the formula can be replayed on historical data.

Use a diversity constraint so the top queue does not contain near-identical products or three interpretations of the same event.

---

# 10. Source Strategy

## Source registry

Every source record includes:

```text
owner
purpose
access method
allowed environment
licence/terms URL
attribution requirement
retention rule
poll interval
rate limit
confidence tier
last terms review
last success
health state
```

Do not store full publisher content unless the licence permits it. Prefer title, permitted snippet, normalized facts, timestamps, canonical URL, and derived classifications.

## Source order

Release 0 should determine the actual order. Default candidates:

1. official PAGASA warnings/bulletins for hazardous weather facts;
2. structured forecast data for heat/rain context;
3. one licensed news/event discovery source;
4. manually exported marketplace/trend observations;
5. official commerce or trends APIs only after access is confirmed.

## Known access constraints as of 2026-09-10

- Google Trends API remains limited-access alpha. Treat access as optional, never as an MVP dependency.
- NewsAPI's free Developer plan is development-only and delayed; production, including internal production use, requires a suitable paid plan.
- Open-Meteo's free API is non-commercial. Commercial use requires the appropriate subscription and attribution.
- PAGASA is the authoritative source for Philippine warnings, but a website page is not automatically a stable public API. Confirm permitted machine access, terms, and document format before implementing an adapter.
- TikTok Shop developer access is product-, scope-, region-, and use-case-specific. A successful signed request and saved response fixture are required before any endpoint enters the roadmap.
- Research or seller APIs must not be treated as creator-affiliate eligibility APIs unless their terms and returned data explicitly support that purpose.

If a source cannot be legally and reliably used, replace it with a manual import or another licensed source; do not quietly scrape it.

---

# 11. Signal Processing

## Release 1 pipeline

```text
fetch
→ validate
→ normalize
→ content hash/exact dedupe
→ deterministic policy checks
→ structured classification
→ human-visible evidence
```

Adapter contract:

```python
class SourceAdapter(Protocol):
    async def fetch(self, cursor: Cursor | None) -> FetchResult: ...
    def normalize(self, item: object) -> NormalizedSignal: ...
```

Requirements:

- idempotency and cursor/checkpoint handling;
- bounded timeout and retry with jitter;
- explicit rate limiting;
- raw payload retention only as allowed;
- no AI inside fetch adapters;
- fixture-based contract tests;
- last-success and degraded-source states.

## Semantic clustering trigger

Do not add embeddings and pgvector by default. Add them when exact/rule-based deduplication leaves enough duplicate events to harm queue quality or operator time.

When added, use embeddings only to nominate merge candidates. Require compatible geography, event type, and time window before merging.

## Structured event output

```json
{
  "event_type": "POWER_INTERRUPTION",
  "business_relevant": true,
  "sensitivity": "low",
  "country": "PH",
  "regions": ["Cebu"],
  "starts_at": "...",
  "ends_at": "...",
  "affected_needs": ["lighting", "charging"],
  "confidence": 0.86,
  "evidence_ids": ["..."],
  "reason": "..."
}
```

Validate model output against a versioned schema and reject rather than guess when required facts are absent.

---

# 12. Product and Marketplace Bridge

AI produces generic product concepts, not fabricated SKUs.

```json
{
  "name": "Rechargeable emergency lamp",
  "category": "Home & Living",
  "need_solved": "Backup lighting",
  "target_user": "Household, renter, or student",
  "required_features": ["rechargeable", "portable"],
  "claims_to_avoid": ["guaranteed emergency safety"],
  "search_queries": [
    "rechargeable emergency light",
    "portable rechargeable LED lamp"
  ],
  "expected_lifetime_hours": 48,
  "rationale": "..."
}
```

The product-match form captures:

```text
marketplace
marketplace product ID when permitted
product and affiliate URLs
listing title and seller
price and currency
commission rate and estimated amount
stock/availability observation
shipping observation
rating/reviews when permitted
category
verified facts and claims
image provenance/usage note
eligibility confirmation timestamp
operator notes
```

Eligibility expires. Recheck before export if the configured freshness window has passed.

Log unsuccessful searches. “No viable listing” is valuable training data for marketplace-fit priors.

---

# 13. Creative System

## Brief first

Every asset derives from an immutable, versioned brief:

```text
opportunity and evidence
selected listing
audience
single content angle
verified product facts
allowed claims
forbidden claims
required affiliate/commercial disclosure
platform and format
experiment hypothesis
```

## Copy output

Generate a small, meaningfully diverse set:

- one practical-problem hook;
- one benefit/demonstration hook;
- one curiosity or preparedness hook when appropriate;
- two short captions;
- one call to action;
- disclosure text;
- optional hashtags based on platform policy and operator preference.

Unsupported superlatives, urgency, prices, safety claims, durability claims, and performance numbers fail validation.

## Visual progression

1. Original marketplace asset plus text/layout template.
2. Deterministic crop, background, motion, and typography.
3. AI-assisted background or scene editing using the real product image.
4. More complex generation only if it improves approval or performance.

Never create a different-looking product and represent it as the listing.

## Video

Start with a deterministic 9:16 template only after static/slideshow content is useful:

```text
0–2s   hook
2–5s   product and problem
5–10s  verified features/demonstration
10–14s why-now or use context
14–17s CTA and disclosure-safe end frame
```

Remotion is the preferred renderer if the web stack is already TypeScript. Use FFmpeg for encoding and media utilities. Do not make generative video a core dependency.

---

# 14. Compliance, Safety, and Rights

## Content rules

Block or require review for:

- deaths, injuries, victims, or graphic incidents used as sales hooks;
- fear-based disaster urgency;
- guaranteed safety, medical, financial, or performance claims;
- unsupported “best,” “#1,” scarcity, price, or durability claims;
- political persuasion;
- protected-class targeting or sensitive personal inference;
- prohibited marketplace categories;
- product-image transformations that change color, shape, logo, quantity, accessories, or visible features;
- copyrighted publisher content beyond permitted use;
- expired evidence or affiliate eligibility.

Use preparedness, practical utility, comfort, organization, and truthful demonstration framing.

## Platform disclosure

The exported posting checklist must require the operator to use the platform's commercial-content disclosure control where applicable. TikTok currently requires the content disclosure setting for content promoting a brand, product, or service and may restrict or remove undisclosed posts.

Text disclosure is configurable but cannot be silently removed from an approved export package.

## Philippine privacy and e-commerce

Before collecting multi-user account data or importing identifiable audience/customer data:

- define lawful purpose and data minimization;
- provide a privacy notice;
- set retention/deletion rules;
- protect access tokens and personal data;
- document data-subject request handling;
- perform a legal/compliance review appropriate to the actual business model.

The Data Privacy Act principles of transparency, legitimate purpose, and proportionality apply to personal-information processing. The Internet Transactions Act and other consumer-protection rules should be reviewed before public commercial launch.

This plan is product guidance, not legal advice.

---

# 15. Experiment and Analytics Design

Analytics must be designed before the first published test.

## Decision log

For every recommendation, record:

```text
shown_at
rank and score version
evidence snapshot
accepted / rejected / deferred
reason code and note
marketplace search time
match success/failure
creative generation and edit time
published/not published
experiment ID and variant
```

## Outcome metrics

Capture when available:

```text
views and qualified views
average watch time / completion
likes, comments, shares, saves
product clicks
affiliate clicks
orders
gross merchandise value
commission/revenue
refunds/cancellations if available
```

Derived business metrics:

- click-through rate;
- conversion rate;
- commission per 1,000 views;
- commission per post;
- commission per operator hour;
- time from recommendation to export/post;
- opportunity and creative acceptance rates.

## Comparison method

- Establish a baseline from recent normal-workflow posts.
- Label every assisted and unassisted post.
- Compare within the same account, category, format, and similar posting windows.
- Prefer paired or alternating tests when practical.
- Report sample sizes and uncertainty.
- Do not claim causality from a handful of viral or zero-view posts.

## Learning policy

For the MVP, weights remain fixed. Review performance weekly and change one hypothesis at a time.

After enough observations:

1. use smoothed category/source priors;
2. backtest every proposed scoring change on held-out time periods;
3. use bounded multipliers;
4. progress to interpretable prediction models only when they beat simple baselines.

Never train on post-publish information that would not have existed at ranking time.

---

# 16. MVP Information Architecture

Keep the first UI small.

## `/today`

- up to three timely signals;
- ranked product opportunities;
- filters for lane, location, reason type, and expiry;
- accept, reject, defer, and “not enough evidence” actions;
- source health warning when ranking is degraded.

## `/opportunities/[id]`

- why now;
- evidence and timestamps;
- uncertainty and counter-signals;
- score breakdown and score version;
- consumer need and target user;
- marketplace search queries;
- accept/reject history;
- product match.

## `/studio/[product_match_id]`

- actual product images and verified facts;
- brief and experiment hypothesis;
- hooks, caption, CTA, and disclosure;
- preview and edit controls;
- compliance results;
- approve, reject, and export.

## `/results`

- import/manual entry;
- assisted versus baseline results;
- performance by reason, category, source, hook, and template;
- time saved and cost per published item;
- data-quality warnings.

## `/operations`

- source and job health;
- failed imports/jobs;
- model calls and costs;
- prompt/score versions;
- settings.

Do not build separate pages for every database entity until navigation evidence demands them.

---

# 17. Technical Architecture

## Shape

Use a modular monolith:

```text
Next.js web
FastAPI application
single dedicated worker/scheduler process
PostgreSQL
S3-compatible object storage
```

No microservices, Kubernetes, Redis, or vector database are required initially.

## Stack

| Layer | Choice |
|---|---|
| Web | Next.js, TypeScript strict, Tailwind, shadcn/ui |
| API | Python 3.12+, FastAPI, Pydantic v2 |
| Persistence | PostgreSQL, SQLAlchemy 2, Alembic |
| Storage | Supabase Storage or another S3-compatible service |
| Worker | One separately deployed process with APScheduler initially |
| AI | Provider adapter using structured outputs and versioned schemas |
| Video | Remotion plus FFmpeg when Release 2 begins |
| Observability | Structured logs, job history, Sentry |
| Tests | pytest, contract fixtures, Playwright |

APScheduler must run in exactly one worker process; never embed the same scheduler in every web/API replica.

## Provider abstraction

```python
class AIProvider(Protocol):
    async def classify_event(...): ...
    async def infer_needs(...): ...
    async def generate_product_concepts(...): ...
    async def generate_creative_brief(...): ...
    async def generate_copy(...): ...
    async def verify_fidelity(...): ...
    async def edit_image(...): ...
```

Model IDs belong in configuration, not domain code. Route workloads by measured quality, latency, and cost. Pin versions where stability matters and re-run evals before changing them.

## Suggested repository

```text
tr3ndly/
├── apps/
│   ├── web/
│   └── api/
├── tr3ndly/
│   ├── sources/
│   ├── signals/
│   ├── intelligence/
│   ├── marketplace/
│   ├── creative/
│   ├── experiments/
│   └── operations/
├── prompts/
├── worker/
├── migrations/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── evals/
│   └── e2e/
├── docs/
└── AGENTS.md
```

Keep Python domain code in one importable package. Do not create pseudo-microservices as folders with unclear ownership.

---

# 18. Data Model and State

Build tables only when the current release uses them.

## Release 1 tables

```text
users
source_configs
source_runs
raw_signals
event_clusters
event_cluster_members
trend_signals
product_concepts
opportunities
opportunity_evidence
score_snapshots
decision_events
marketplace_products
product_assets
creative_briefs
creative_variants
approvals
exports
posts
metric_observations
experiments
model_runs
prompt_versions
```

Use append-only snapshots for evidence, scores, briefs, approvals, and observed metrics where replay/audit matters.

## State machines

Opportunity:

```text
discovered → eligible → accepted → matched → content_ready → used
                    ↘ rejected
                    ↘ expired
```

Product match:

```text
candidate → eligibility_confirmed → stale/unavailable
```

Creative:

```text
draft → generated → needs_review → approved → exported → posted
                              ↘ rejected
```

State transitions are validated in domain code and audited. Avoid relying only on database enums for workflow rules.

---

# 19. API Surface

Start with task-oriented routes rather than exposing every table:

```text
GET  /health
GET  /today

GET  /opportunities/{id}
POST /opportunities/{id}/decision
POST /opportunities/{id}/product-match

POST /product-matches/{id}/confirm
POST /product-matches/{id}/creative-brief

POST /creative-briefs/{id}/generate
POST /creatives/{id}/review
POST /creatives/{id}/export

POST /results/import
GET  /results/overview

GET  /operations/sources
POST /operations/sources/{id}/run
GET  /operations/jobs
GET  /operations/model-runs
```

Generate a typed TypeScript client from OpenAPI. Use idempotency keys for generation, import, export, and future publishing commands.

---

# 20. AI Quality and Evaluation

## Evaluation set before production inference

Create a time-stamped, manually labeled Philippine corpus. Start with at least 100 examples across:

- heat, rain, typhoon, outage, water interruption;
- school, holiday, concert, transport, technology release;
- crime, tragedy, gossip, political opinion;
- ambiguous or commercially tempting but inappropriate events;
- multilingual English, Filipino, and common code-switching.

Labels:

```text
business relevance
event type
sensitivity
geography
time window
acceptable needs
unacceptable products
source confidence
review notes
```

## Required metrics

- precision on publishable business relevance;
- recall on the selected event lanes;
- blocked-event false-negative rate;
- need/product acceptance rate;
- event duplicate/merge error rate;
- explanation usefulness;
- product-fidelity failure rate;
- creative approval rate.

The launch target for blocked or exploitative recommendations is zero on the evaluation set. Production still requires human review.

## Prompt discipline

Prompts and schemas are versioned in source control with:

- purpose and owner;
- semantic version;
- changelog;
- input/output schema;
- representative fixtures;
- failure behavior;
- evaluation results.

Cache by normalized input hash, prompt version, schema version, and model configuration.

---

# 21. Security and Operations

- Secrets exist only in backend/worker secret storage.
- Never expose service-role, marketplace, or model credentials to the browser.
- Use signed uploads/downloads and strict MIME, extension, and size checks.
- Strip metadata from exported user assets when appropriate.
- Sanitize external HTML and treat all source text as untrusted input.
- Prevent prompt-injected source text from changing tool or policy behavior.
- Use least-privilege database and storage credentials.
- Back up PostgreSQL and verify restore procedures before launch.
- Set retention policies for raw signals, uploads, logs, and model inputs.
- Record who approved an asset and which facts/evidence it used.
- Apply bounded retries, circuit breakers, and spend limits.
- Show degraded results when sources fail; never silently present stale ranking as current.

Operational dashboards must expose:

```text
source freshness and last success
job failures and retry count
items fetched/accepted/rejected/deduplicated
model calls, latency, and estimated cost
generation/fidelity failures
imports with incomplete attribution
```

---

# 22. Cost Controls

1. Filter and exactly deduplicate before model calls.
2. Use the least expensive model that passes the eval target.
3. Escalate only ambiguous or high-value cases.
4. Cache deterministic model work by versioned input.
5. Generate media only after a listing is confirmed.
6. Default to one brief and a small variant set.
7. Set per-run and per-day spend caps.
8. Store cost by source, opportunity, creative, and published post.
9. Include paid data-source licences in unit economics.
10. Track commission per operator hour and net contribution after data/model costs.

---

# 23. Delivery Plan and Gates

## Phase A — Validation operations

Deliverables:

- assumption register;
- source/licence register;
- operator baseline dataset;
- manual opportunity and decision log;
- at least 30 published test units if feasible;
- weekly learning report;
- decision to proceed, narrow, pivot, or stop.

Do not write production ingestion code before the first week of manual results reveals which sources and event types matter.

## Phase B — Foundation

- monorepo and root `AGENTS.md`;
- Next.js shell and FastAPI health endpoint;
- PostgreSQL and reversible Alembic migration;
- typed configuration and secret validation;
- CI for lint, types, tests, migration up/down check;
- structured logging and job-run model;
- seeded demo data for UI development.

**Done:** One documented command starts the local stack; CI passes; health and Today shell load.

## Phase C — First evidence slice

Implement one vertical slice using the best Release 0 source:

```text
source fixture/live fetch
→ raw signal
→ normalization/dedupe
→ classification
→ opportunity
→ Today card
→ operator decision
```

**Done:** The slice is replayable from fixtures, evidence is visible, and decision feedback is saved.

## Phase D — Product match and scoring

- needs and product concept generation;
- hard eligibility gates;
- component score snapshots and versioned formulas;
- marketplace queries;
- manual match, failed-search logging, and expiry;
- listing economics and post-match priority.

**Done:** The operator can move from an evidence-backed opportunity to a confirmed listing in the measured target time.

## Phase E — Content and export

- verified-facts model;
- brief and copy generation;
- compliance checks;
- approval audit trail;
- export package with asset, caption, disclosure checklist, link reference, and experiment ID.

**Done:** A matched listing becomes a reviewed export without unsupported claims.

## Phase F — Measurement loop

- post record and baseline/assisted label;
- CSV/manual metric import;
- experiment assignment;
- results dashboard;
- weekly review report;
- cost and time accounting.

**Done:** Each outcome traces back to the evidence, score version, listing, brief, and creative variant that produced it.

## Phase G — Creative acceleration

Only after the Release 1 gate:

- deterministic layouts and 9:16 rendering;
- product-image editing;
- visual fidelity evaluation;
- variant workflow.

## Phase H — External automation

Only after relevant access and value are proven:

- official source adapters;
- analytics connectors;
- TikTok upload/direct posting;
- Meta publishing;
- multi-user features.

Manual export remains a permanent fallback.

---

# 24. First Implementation Tasks

After Release 0 validates proceeding, execute one contract-sized task at a time:

1. Create repository skeleton, commands, CI, and `AGENTS.md`.
2. Add typed settings, FastAPI health, Next.js Today shell, and seeded demo mode.
3. Add database connection, reversible migrations, source runs, raw signals, and decision events.
4. Implement the source adapter contract and fixture harness.
5. Implement the single highest-value source adapter.
6. Implement normalization, hashes, exact deduplication, freshness, and expiry.
7. Create the labeled eval dataset and scoring harness.
8. Implement the AI provider abstraction and one structured classifier.
9. Build the first evidence-to-opportunity vertical slice.
10. Add accept/reject/defer feedback with reason codes.
11. Add product concept, marketplace query, manual match, and failed-search capture.
12. Add listing economics and versioned priority scores.
13. Add verified facts, creative brief, copy, policy checks, approval, and export.
14. Add result import, experiments, and baseline comparison.

Semantic clustering, image generation, video rendering, and publishing are deliberately absent from the first 14 tasks.

Every implementation task must specify:

```text
goal
files/modules allowed to change
input/output contract
schema changes
acceptance criteria
tests
observability
security and data-rights considerations
non-goals
rollback or failure behavior
```

---

# 25. Launch Gates

## Internal operator launch

- the selected sources remain healthy for 7 consecutive days;
- stale/degraded data is visibly marked;
- evaluation targets are met for the chosen lanes;
- every opportunity has evidence, expiry, uncertainty, and score version;
- product match and “no match” are both supported;
- every creative uses verified facts and requires approval;
- export and results import work end to end;
- restore, secret, and spend-limit checks pass;
- source licences and platform rules have current review dates.

## Broader beta

- Release 1 and Release 2 product gates pass;
- at least two operators complete onboarding without developer intervention;
- tenant isolation and per-user secrets are implemented;
- privacy notice, retention, deletion, and support processes exist;
- unit economics include paid data, models, storage, and operator support;
- no critical compliance or product-fidelity incident remains unresolved.

## Stop or pivot triggers

Pause expansion if, after a fair test:

- accepted opportunities remain rare;
- marketplace match repeatedly fails or takes too long;
- performance is no better than a simple bestseller baseline;
- research time is not materially reduced;
- source licensing costs overwhelm likely commission;
- reliable metrics cannot be obtained;
- the workflow encourages unsafe or misleading content.

A pivot could retain the best-performing component: daily research brief, listing-economics tracker, content compliance assistant, or creative experiment log.

---

# 26. Success Metrics

## North-star metric

**Net commission per operator hour from Tr3ndly-assisted published content.**

This combines business value and time saved while discouraging empty content volume.

## Leading indicators

- useful opportunity acceptance rate;
- viable listing match rate and median match time;
- recommendation-to-publish rate;
- research-to-export time;
- creative first-pass approval rate;
- affiliate click-through rate;
- cost per approved/published creative;
- percentage of outcomes with complete attribution.

## Guardrails

- exploitative/blocked recommendation rate;
- unsupported-claim rate;
- material product-fidelity failure rate;
- stale-opportunity rate;
- duplicate recommendation rate;
- source/licence violation count;
- operator overrides caused by missing or misleading evidence.

---

# 27. Risk Register

| Risk | Early warning | Mitigation |
|---|---|---|
| News does not translate to purchase intent | Low acceptance/conversion | Narrow event taxonomy; emphasize calendar/weather/commerce signals |
| Marketplace eligibility cannot be automated | Frequent stale/no-match results | Keep manual bridge; timestamp eligibility; support permitted imports |
| Trend APIs are unavailable or delayed | Adapter access blocked | Treat as optional; use manual observations and commerce evidence |
| Data licensing becomes expensive | Cost per post rises | Validate with manual/low-volume sources; negotiate or replace before scale |
| Affiliate performance data is incomplete | Outcomes cannot be attributed | Design manual CSV entry first; require experiment/post identifiers |
| AI invents claims or alters products | Review failures | Verified-facts allowlist, deterministic templates, fidelity gate, human approval |
| Event-based selling feels exploitative | High sensitivity flags/user distrust | Restrict lanes and framing; block victim/tragedy hooks |
| Ranking optimizes vanity metrics | Views rise but commission does not | Use commission per 1,000 views and per operator hour |
| Too much infrastructure delays learning | Weeks pass without posts | Enforce release gates and first vertical slice |
| A single viral post distorts learning | Abrupt weight changes | Fixed weights, robust summaries, uncertainty, time-based holdout |

Review this table weekly during validation and monthly after launch.

---

# 28. Current External References

Re-verify these before implementing or launching an integration:

- OpenAI model catalog and Responses API: https://platform.openai.com/docs/models
- TikTok Content Posting API: https://developers.tiktok.com/products/content-posting-api
- TikTok Direct Post requirements: https://developers.tiktok.com/docs/en/content-posting-api-get-started
- TikTok commercial-content disclosure: https://support.tiktok.com/en/business-and-creator/creator-and-business-accounts/promoting-a-brand-product-or-service
- Google Trends API alpha: https://developers.google.com/search/apis/trends
- NewsAPI pricing and environment restrictions: https://newsapi.org/pricing
- Open-Meteo commercial terms and attribution: https://open-meteo.com/en/terms
- PAGASA: https://www.pagasa.dost.gov.ph/
- Philippine Data Privacy Act: https://privacy.gov.ph/data-privacy-act/
- Philippine Internet Transactions Act: https://lawphil.net/statutes/repacts/ra2023/ra_11967_2023.html

Do not encode model names, prices, rate limits, scopes, or platform rules permanently in this plan. Record verified values in a dated integration decision record when implementation begins.

---

# 29. Relationship to the Architecture Document

`TR3NDLY_SYSTEM_ARCHITECTURE.md` remains a useful catalogue of the intended full system. This document controls **product scope, sequencing, validation gates, and MVP priority**.

Where the documents differ:

- this plan's release gates and reduced MVP scope take precedence;
- advanced components in the architecture document are future capabilities, not automatic MVP requirements;
- external API/model claims must be re-verified at implementation time;
- the implemented architecture must follow proven workflow needs, not the maximum envisioned feature set.

Update the architecture document after Release 0, once the first source mix, content lanes, and measurement workflow are proven.

---

# 30. Final Product Vision

The mature Tr3ndly experience should feel simple:

```text
Open Today.

See a small number of Philippine product opportunities with:
- credible evidence;
- who may need the product and why;
- when the opportunity expires;
- uncertainty and counter-signals;
- what listing characteristics to search for;
- expected content and commercial potential.

Choose a real affiliate listing.

Receive a truthful brief and a few high-quality content options.
Approve and publish.

See whether the decision earned attention, clicks, orders, commission,
and whether it saved enough time to repeat.
```

Tr3ndly wins when it makes the operator's next decision better—not when it merely generates more content.
