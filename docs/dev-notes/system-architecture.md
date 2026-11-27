# Tr3ndly — Current-Demand Affiliate Intelligence & Content Automation
## System Architecture Specification
**Version:** 2.0  
**Status:** Pre-build architecture  
**Primary market for MVP:** Philippines  
**Primary operator:** Single creator/operator first, multi-account capable later

> **Planning status (2026-09-10):** This document describes the broader target architecture. For MVP scope, sequencing, validation gates, and implementation priority, `TR3NDLY_MASTER_BUILD_PLAN.md` version 2.0 is authoritative. Components described here may be deferred until the corresponding product gate is met. Reconcile this specification after Release 0 validation identifies the proven source mix, content lanes, and measurement workflow.

---

## 1. Product Definition

Tr3ndly is no longer a fashion-only trend system.

It is an **AI-powered current-demand product opportunity engine** that discovers products for affiliate marketing for two independent reasons:

1. **Trend-based opportunities** — an item/category is already gaining popularity or purchase interest.
2. **Timely opportunities** — a current event, weather condition, seasonal event, outage, public situation, or other demand-changing signal creates a practical consumer need.

Tr3ndly converts those signals into:

**signal → consumer need → product concept → marketplace search target → selected affiliate listing → ad creative → human approval → publishing → performance feedback**

The system must always explain **why** a product is recommended.

---

## 2. Core Product Principles

1. **Two discovery engines, one opportunity layer.**
   - Trending and timely signals are independent.
   - A product can qualify through either one or both.

2. **Product concept is separate from affiliate listing.**
   - Tr3ndly first decides *what kind of product is worth promoting*.
   - The exact Shopee/TikTok affiliate listing is matched later.
   - This avoids making marketplace API access a hard dependency.

3. **No prohibited marketplace scraping.**
   - Shopee/TikTok marketplace crawling is not a required system capability.
   - Marketplace details are obtained through official APIs, exports, user-entered details, or user-supplied product assets.

4. **Current events are filtered for commercial usefulness and sensitivity.**
   - The product does not become a generic news aggregator.
   - Crime, celebrity gossip, deaths, and unrelated political stories should normally be rejected.
   - Disaster/weather information can be used only for practical preparedness-oriented recommendations, not fear-based exploitation.

5. **Human approval remains mandatory before publishing.**

6. **Every recommendation is auditable.**
   - Save source, timestamps, score components, model version, prompts, and rationale.

---

## 3. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SIGNAL SOURCES                          │
│                                                                         │
│  News / Events      Weather        Search Trends       Commerce Trends │
│  NewsAPI / GDELT    PAGASA         Google Trends      TikTok Bestsellers│
│  verified sources   Open-Meteo     (when available)   other APIs later │
└──────────┬──────────────┬─────────────────┬──────────────────┬───────────┘
           │              │                 │                  │
           ▼              ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL INGESTION LAYER                          │
│ fetch → normalize → source metadata → dedupe → persist raw evidence     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       SIGNAL UNDERSTANDING LAYER                        │
│                                                                         │
│  Event clustering              Trend normalization                     │
│  Business relevance filter     Velocity / persistence                   │
│  Sensitivity filter            Cross-source confirmation               │
│  Geo + freshness scoring       Product/category extraction             │
└──────────────────────┬──────────────────────────┬───────────────────────┘
                       │                          │
                       ▼                          ▼
             ┌──────────────────┐       ┌──────────────────────┐
             │ TIMELY ENGINE    │       │ TREND ENGINE         │
             │ event → needs    │       │ trend → products     │
             └────────┬─────────┘       └──────────┬───────────┘
                      │                            │
                      └──────────────┬─────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        OPPORTUNITY ENGINE                               │
│ product concept generation → scoring → ranking → reason codes           │
│ detects "timely", "trending", or "both"                                 │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      MARKETPLACE MATCH BRIDGE                           │
│ generated search phrases → user searches affiliate marketplace          │
│ → selected eligible listing → actual product details/images/link        │
│ → stored as marketplace product                                         │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CREATIVE ENGINE                                 │
│ hooks → captions → CTA → disclosure → image edit/generation → variants  │
│ product fidelity check → compliance/sensitivity check                   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         APPROVAL QUEUE                                  │
│ source evidence + why-now + product + creative + edit/approve/reject     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     EXPORT / PUBLISHING LAYER                           │
│ Manual export first → TikTok Content Posting API later → Meta later      │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS + FEEDBACK LOOP                            │
│ clicks → orders → conversion → revenue → content metrics                │
│ source/category/event/creative performance → ranking weight updates     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Discovery Modes

### 4.1 Trend-Based Opportunity

Purpose: identify products that consumers already appear to be interested in.

Possible signals:

- TikTok Shop Bestsellers API
- Google Trends official API when access is available
- Search-interest datasets
- Public product/category trend APIs
- Seasonal recurrence
- Historical Tr3ndly conversion data
- Approved third-party trend providers later

Example:

```text
Signal:
"portable mini fan" search interest rising

Product concept:
Rechargeable portable mini fan

Reason:
TRENDING

Evidence:
- search velocity rising
- bestseller/category confirmation

Suggested marketplace queries:
- rechargeable mini fan
- portable handheld fan usb
- mini fan rechargeable
```

### 4.2 Timely Opportunity

Purpose: identify practical products whose utility increases because of a current or upcoming situation.

Examples:

- typhoon / heavy rain
- flood risk
- high heat index
- scheduled or recurring power interruptions
- school opening
- holiday/gifting period
- transport disruption
- major public event
- seasonal transition
- new consumer regulation that changes practical needs
- temporary supply/demand changes

Example:

```text
Signal:
Power interruption expected in an affected area

Needs:
- lighting
- device charging
- ventilation

Product concepts:
- rechargeable emergency lamp
- solar light
- power bank
- rechargeable fan

Reason:
TIMELY
```

### 4.3 Combined Opportunity

The same item may be both timely and trending.

Example:

```text
Rechargeable mini fan

Trend Score: 81
Timely Score: 92
Why:
- rising marketplace/search interest
- high temperatures / outage risk

Final Opportunity Score: 100 (capped)
Reason Type: BOTH
```

---

## 5. Signal Ingestion

### 5.1 Source Adapter Contract

Every source implements:

```python
class SignalSource:
    source_id: str

    async def fetch(self, since, region) -> list[RawSignal]: ...

    def normalize(self, raw) -> NormalizedSignal: ...
```

Each normalized signal should contain:

```text
id
source_id
source_type
title
summary
url
published_at
fetched_at
country
region
city (optional)
language
raw_payload
source_confidence
```

### 5.2 Recommended Sources

#### Weather / hazard
- **PAGASA**: authoritative PH tropical cyclone and severe weather information.
- **Open-Meteo**: structured forecast variables for geographic weather context.
- Add other official government alert sources only when permitted and useful.

#### News / events
- **NewsAPI**: convenient development source for recent article discovery.
- **GDELT**: broad global news/event discovery and redundancy.
- Selected authoritative Philippine publishers and government sources can be added through permitted feeds/APIs.

#### Search demand
- **Google Trends API**: preferred when official API access is granted.
- Do not make unofficial `pytrends` a production dependency.

#### Commerce demand
- **TikTok Shop Bestsellers**: use the API scope already available to the project if it returns suitable PH bestseller/category data.
- Additional official commerce/product APIs can be added later.

### 5.3 Schedule

Suggested MVP frequencies:

| Source | Frequency |
|---|---:|
| severe weather / official alerts | every 30–60 min |
| news/events | every 60 min |
| weather forecast | every 3 hours |
| commerce trends | every 4–6 hours |
| search trends | every 6–12 hours |
| analytics ingestion | every 6–24 hours |
| opportunity recalculation | after each meaningful signal batch |

Avoid excessive polling.

---

## 6. Normalization, Deduplication and Event Clustering

Raw news feeds frequently contain the same event from many publishers.

Pipeline:

```text
raw items
  ↓
URL/title normalization
  ↓
exact duplicate removal
  ↓
embedding similarity
  ↓
time + geography compatibility
  ↓
event cluster
```

### 6.1 Embeddings

Use embeddings to compare:

- title + summary
- product concept names
- event clusters
- marketplace product descriptions

Store vectors in PostgreSQL with `pgvector`.

### 6.2 Event Cluster

```text
event_cluster
- id
- canonical_title
- canonical_summary
- event_type
- first_seen_at
- last_seen_at
- country
- regions[]
- source_count
- highest_source_confidence
- sensitivity_level
- business_relevance
- status
```

Several sources confirming the same event increase confidence rather than generating duplicate dashboard cards.

---

## 7. Business-Relevance Filter

Every event must pass an explicit filter before it can create product opportunities.

### 7.1 Event Types Worth Evaluating

```text
WEATHER_HAZARD
HEAT
FLOOD
POWER_INTERRUPTION
WATER_INTERRUPTION
SCHOOL_CALENDAR
HOLIDAY
PUBLIC_EVENT
TRANSPORT_DISRUPTION
SEASONAL_CHANGE
TECH_RELEASE
CONSUMER_POLICY_CHANGE
SUPPLY_DISRUPTION
LOCAL_ACTIVITY
OTHER_DEMAND_SIGNAL
```

### 7.2 Usually Reject

```text
HOMICIDE / ordinary crime
celebrity gossip
personal scandals
graphic tragedy
unrelated political conflict
sensational stories with no practical consumer need
```

This is not a hard keyword blacklist. The system performs classification and records a reason.

### 7.3 Structured AI Output

```json
{
  "business_relevant": true,
  "event_type": "POWER_INTERRUPTION",
  "commerce_relevance": 94,
  "sensitivity": "low",
  "affected_needs": [
    "lighting",
    "charging",
    "ventilation"
  ],
  "eligible_for_product_inference": true,
  "reason": "Likely temporary demand for backup power and lighting products."
}
```

Use Structured Outputs so the model must follow a JSON schema.

---

## 8. Sensitivity and Ethical-Commerce Filter

The system may recommend practical preparedness products around hazardous conditions but must not exploit harm.

### Block or flag:
- references to deaths/injuries as a sales hook
- fear-based urgency such as "buy before disaster strikes"
- guaranteed-safety claims
- price-gouging language
- medical claims without evidence
- products implying emergency protection they cannot provide
- political persuasion
- graphic incident content

### Preferred framing:
- preparedness
- convenience
- practical utility
- seasonal readiness
- comfort
- organization

Example approved angle:

> "Preparing for possible power interruptions? A rechargeable lamp can be useful to keep ready at home."

---

## 9. Timely Opportunity Algorithm

Each event receives normalized 0–100 dimensions.

```text
Freshness F
Geographic relevance G
Affected population / reach R
Consumer-need strength N
Product actionability P
Source confidence C
Expected duration D
Sensitivity penalty S
```

MVP formula:

```text
TimelyScore =
    0.15*F +
    0.15*G +
    0.15*R +
    0.20*N +
    0.20*P +
    0.10*C +
    0.05*D -
    S
```

Clamp result to 0–100.

Suggested sensitivity penalty:

```text
none:      0
low:       0
medium:   15
high:     50
blocked: 100
```

Events under a configurable threshold (e.g. 65) do not generate opportunities.

---

## 10. Trend Opportunity Algorithm

Normalize trend sources into comparable dimensions:

```text
Velocity V         — how quickly interest is increasing
Persistence P      — not merely a one-hour spike
CrossSource X      — confirmation by independent signals
MarketFit M        — likely affiliate-marketplace availability
PurchaseIntent I   — consumer intent vs informational curiosity
Recency R
```

MVP formula:

```text
TrendScore =
    0.30*V +
    0.15*P +
    0.20*X +
    0.15*M +
    0.15*I +
    0.05*R
```

Clamp to 0–100.

Different sources need their own normalization functions before entering this formula.

---

## 11. Combined Opportunity Score

A product does **not** need to be both trending and timely.

Store both scores independently.

```text
final_score = max(TrendScore, TimelyScore)
              + 0.15 * min(TrendScore, TimelyScore)
```

Cap at 100.

Reason types:

```text
TREND
TIMELY
BOTH
```

This gives a synergy bonus without penalizing opportunities that originate from only one engine.

Later, replace fixed coefficients with learned weights after enough conversion data exists.

---

## 12. Product-Need Inference

Timely events first produce **consumer needs**, then product concepts.

Example:

```text
event: power interruption
↓
needs:
- lighting
- charging
- ventilation
↓
product concepts:
- rechargeable emergency lamp
- solar lamp
- power bank
- rechargeable fan
```

Each product concept contains:

```text
name
category
need_solved
target_user
important_features[]
avoid_features[]
target_price_band
search_queries[]
timely_score
trend_score
final_score
reason_type
rationale
opportunity_expiry
```

### Opportunity Expiry

Timely products need an expiry.

Examples:
- typhoon: short-lived; re-evaluate every bulletin
- outage: end after scheduled restoration + buffer
- holiday: expiry after holiday
- heat season: longer
- trend: decay if velocity falls

Never leave all opportunities permanently "trending."

---

## 13. Top 3 Timely Business Signals

The dashboard displays the three highest-value active event clusters, **not the three biggest general news stories**.

Each card contains:

```text
headline
verified summary
event type
affected location
published / last verified time
business relevance
confidence
why it matters for affiliate decisions
consumer needs
top product concepts
source count
expiry
```

Selection constraints:

1. `business_relevant = true`
2. sensitivity not blocked
3. confidence above threshold
4. current / not expired
5. diversity rule to avoid three cards about the same event
6. rank by TimelyScore

---

## 14. Marketplace Match Bridge

This is a deliberate boundary between **opportunity intelligence** and **affiliate eligibility**.

Tr3ndly outputs:

```text
Product concept:
Rechargeable emergency lamp

Search phrases:
- rechargeable emergency light
- led emergency lamp rechargeable
- solar rechargeable lamp
- usb emergency light
```

User then searches Shopee/TikTok Affiliate marketplace and chooses an eligible listing.

### Marketplace listing ingestion

Supported MVP methods:

- manual form
- paste permitted product details
- upload product image(s)
- import approved/exported affiliate CSV where available
- official marketplace API when available

Do not depend on unauthorized scraping.

### Marketplace product record

```text
id
marketplace
marketplace_product_id (nullable)
product_name
seller_name
category
price
commission_rate
affiliate_url
product_url
image_assets[]
selected_from_opportunity_id
eligibility_confirmed_at
notes
```

---

## 15. Product Image Handling

Use the **actual selected listing asset** supplied through a permitted source when generating ads.

Creative generation must preserve:

- product shape
- color
- logo/branding
- visible features
- quantity
- included accessories
- claims printed on the product

AI may change:

- background
- layout
- lighting
- composition
- supporting decorative elements
- text overlays when platform rules allow
- lifestyle scene, provided the product itself is not materially changed

Never generate a visually different product and present it as the exact affiliate item.

---

## 16. Creative Engine

### 16.1 Copy Generation

Generate structured variants:

```text
3 hooks
2 short captions
1 longer description
CTA variants
hashtags
disclosure
content angle
claims to avoid
```

Inputs:

- opportunity reason
- event/trend evidence
- actual product details
- audience
- platform
- desired tone
- creative template

### 16.2 Image Generation / Editing

Recommended OpenAI path:

- **GPT-Image-2.5 Flare** for normal creative variants
- **GPT-Image-2.5 Sunburst** when higher editing fidelity is needed
- product image supplied as high-fidelity input where applicable

Do not make a deprecated video-generation API a core dependency.

### 16.3 Short-Video Generation Without Generative Video

For MVP TikTok/Reels videos:

```text
product images
+ background
+ animated hook
+ zoom/pan
+ feature cards
+ CTA
+ optional TTS/audio later
↓
Remotion or FFmpeg
↓
9:16 MP4
```

This is cheaper, predictable, editable, and suitable for Codex to implement.

---

## 17. AI Model Roles

Use different models by workload.

### Bulk, high-volume classification
Use a cost-efficient model such as **GPT-5.6 Luna**:
- business relevance
- event type
- sensitivity
- basic product extraction
- metadata cleanup

### Deeper opportunity reasoning
Use **GPT-5.6 Terra**:
- consumer-need inference
- product concept generation
- ambiguous relevance decisions
- opportunity rationale
- copy generation where quality matters

### Escalation
Use **GPT-5.6 Sol** only for:
- difficult multi-source reconciliation
- complex prompt/evaluation design
- rare high-value reasoning cases

### Images
- GPT-Image-2.5 Flare: default
- GPT-Image-2.5 Sunburst: precision edit/final premium creative

All AI calls should:
- use versioned prompt templates
- use structured outputs where possible
- save latency, token usage, model, and prompt version

---

## 18. Recommended Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Next.js + TypeScript | strong dashboard ecosystem |
| UI | Tailwind CSS + shadcn/ui | fast, consistent internal SaaS UI |
| Charts | Recharts | simple analytics/dashboard graphs |
| Backend API | Python + FastAPI | excellent AI/data/API integration |
| Validation | Pydantic v2 | structured AI and API schemas |
| Database | PostgreSQL | robust relational core |
| Vector search | pgvector | signal/product semantic matching |
| ORM | SQLAlchemy 2 | mature Python DB layer |
| Migrations | Alembic | controlled schema evolution |
| Auth | Supabase Auth | easy single-user → multi-user path |
| Object storage | Supabase Storage or S3-compatible | product/creative assets |
| Scheduler MVP | dedicated worker + APScheduler | simple, low operational overhead |
| Queue later | Redis + Celery/RQ/Arq | scale background jobs when needed |
| AI | OpenAI Responses API | text/image input, structured JSON, tool support |
| Image | OpenAI GPT Image | generation/editing |
| Video assembly | Remotion and/or FFmpeg | deterministic short-form video |
| Monitoring | Sentry | errors |
| Product analytics | PostHog (optional) | internal feature/product analytics |
| Hosting | Railway/Render/Fly/VPS | simple app + worker deployment |
| CI | GitHub Actions | tests/lint/migrations |
| Testing | pytest + Playwright | backend + end-to-end UI |
| API client | generated OpenAPI TS client | typed frontend/backend contract |

Avoid microservices initially.

Deploy as:

```text
web
api
worker
postgres
object storage
```

---

## 19. Repository Structure

```text
tr3ndly/
├── apps/
│   ├── web/                       # Next.js dashboard
│   └── api/                       # FastAPI application
│
├── services/
│   ├── ingestion/
│   │   ├── news/
│   │   ├── weather/
│   │   ├── trends/
│   │   └── commerce/
│   │
│   ├── signals/
│   │   ├── normalizer/
│   │   ├── dedupe/
│   │   └── clustering/
│   │
│   ├── intelligence/
│   │   ├── business_relevance/
│   │   ├── sensitivity/
│   │   ├── timely_engine/
│   │   ├── trend_engine/
│   │   ├── needs_inference/
│   │   └── opportunity_engine/
│   │
│   ├── marketplace/
│   │   ├── manual/
│   │   ├── shopee/
│   │   └── tiktok/
│   │
│   ├── creative/
│   │   ├── copy/
│   │   ├── image/
│   │   ├── video/
│   │   └── compliance/
│   │
│   ├── publishing/
│   └── analytics/
│
├── packages/
│   ├── db/
│   ├── schemas/
│   ├── prompts/
│   └── clients/
│
├── worker/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── evals/
│   └── e2e/
│
├── scripts/
├── docs/
└── .github/workflows/
```

Codex should work one module/contract at a time.

---

## 20. Database Model

Core tables:

### Identity/config
- `users`
- `accounts`
- `marketplaces`
- `source_configs`

### Signal layer
- `signal_sources`
- `raw_signals`
- `event_clusters`
- `event_cluster_members`
- `trend_signals`

### Intelligence layer
- `consumer_needs`
- `product_concepts`
- `opportunities`
- `opportunity_evidence`
- `opportunity_scores`

### Marketplace layer
- `marketplace_products`
- `product_assets`
- `affiliate_links`

### Creative layer
- `creative_briefs`
- `creative_assets`
- `creative_variants`
- `approvals`

### Publishing
- `posts`
- `post_attempts`

### Analytics
- `post_metrics`
- `affiliate_metrics`
- `conversion_events`
- `performance_rollups`

### AI observability
- `model_runs`
- `prompt_versions`
- `eval_results`

Important relationships:

```text
event_cluster ──┐
                ├──> opportunity ──> product_concept
trend_signal ───┘                         │
                                         ▼
                                marketplace_product
                                         │
                                         ▼
                                    creative_asset
                                         │
                                         ▼
                                        post
                                         │
                                         ▼
                                      metrics
```

---

## 21. Dashboard Information Architecture

### Sidebar

```text
Dashboard
Signals
  ├─ Timely
  └─ Trends
Opportunities
Product Match
Creatives
Approval Queue
Posts
Analytics
Sources
Settings
```

### Main Dashboard

Top section:

```text
TOP 3 TIMELY BUSINESS SIGNALS
[signal 1] [signal 2] [signal 3]
```

Middle:

```text
TOP OPPORTUNITIES NOW
filter: All | Timely | Trending | Both
```

Each opportunity card shows:

- product concept
- final score
- reason type
- why now
- expiry
- location
- source confidence
- suggested marketplace search queries
- `Find Product` action

Side/bottom:

- trending categories
- ingestion health
- pending approvals
- posts scheduled/exported
- recent performance

---

## 22. Opportunity Detail UI

Sections:

1. **Why now**
2. Evidence timeline
3. Score breakdown
4. Consumer needs
5. Suggested product concepts
6. Marketplace search queries
7. Product match
8. Creative history
9. Performance history

A user must always be able to answer:

> "Why is Tr3ndly recommending this product today?"

---

## 23. Creative Studio UI

```text
LEFT
- actual product images
- selected opportunity
- product facts
- editable constraints

CENTER
- image/video preview

RIGHT
- hook variants
- caption
- CTA
- disclosure
- template
- regenerate/edit controls
```

Actions:

```text
Generate variants
Edit image
Change hook
Change tone
Create 9:16 video
Approve
Reject
Export
```

---

## 24. Publishing Strategy

### MVP
Manual export.

Why:
- avoids platform-review blockers
- validates discovery and creative quality first
- keeps operator control

### TikTok later
Use official TikTok Content Posting API.

Important current constraints:
- app and scopes must be approved
- target creator authorizes the scope
- unaudited Direct Post clients are restricted to private visibility
- support both Direct Post and "Upload to TikTok" draft flow

### Facebook/Instagram later
Add official Meta publishing integration after core conversion is validated.

---

## 25. Analytics Feedback

Measure:

```text
impressions
views
watch time
likes
shares
saves
clicks
affiliate clicks
orders
conversion rate
commission
revenue
revenue per 1,000 views
```

Attribute metrics to:

- source type
- source
- event type
- product category
- reason type (trend/timely/both)
- score bands
- hook style
- creative template
- price band
- commission band
- platform

---

## 26. Feedback Algorithm

Do **not** let early noisy data automatically rewrite ranking weights.

MVP:
- fixed scoring formula
- analytics shown to operator
- weekly performance report

After enough observations:
- apply Bayesian/smoothed category performance multipliers
- then consider learning-to-rank/logistic regression

Example:

```text
AdjustedScore =
  BaseOpportunityScore
  * CategoryPerformanceMultiplier
  * SourcePerformanceMultiplier
```

Keep multipliers bounded, e.g. 0.8–1.2.

Only introduce ML after sufficient labeled conversion data exists.

---

## 27. Testing and Evaluation

### Unit tests
- normalization
- scoring
- expiry
- source weighting
- dedupe
- schema validation

### Integration tests
- NewsAPI adapter
- weather adapter
- TikTok bestseller adapter
- OpenAI calls mocked
- storage
- DB migrations

### AI evaluation set
Create a manually labeled corpus of at least 50–100 signals:

```text
signal
business_relevant?
sensitivity
expected event_type
acceptable product needs
unacceptable product suggestions
```

Track:

- relevance precision
- harmful/irrelevant false positives
- duplicate-cluster rate
- product-fit acceptance
- top-3 usefulness
- creative approval rate

### End-to-end
Playwright:
- signal → opportunity
- opportunity → product match
- product → creative
- creative → approval/export

---

## 28. Security

- secrets only in backend environment variables / secret manager
- never expose OpenAI or marketplace secrets to browser
- signed upload URLs
- strict file validation
- audit trail for approvals
- sanitize external HTML/text
- rate limits
- request timeouts/retries
- idempotency keys for publishing/jobs
- role design even for single user so multi-user expansion is easier

---

## 29. Failure Modes

### No useful news today
Do not force three weak signals.
Dashboard may say:
> "Only 1 high-confidence timely opportunity found."

### Conflicting reports
Reduce confidence and require verification.

### Stale event
Expire opportunity.

### Trend spike caused by unrelated news
Purchase-intent classifier lowers score.

### Product not available on affiliate marketplace
Keep concept but mark `no_match`.

### AI image changes the product
Fail fidelity review; do not publish.

### API unavailable
Retry, mark source degraded, continue using other sources.

---

## 30. MVP Boundary

### Included
- PH-focused current signals
- Top 3 timely business signals
- trend signals
- two-path opportunity scoring
- product concepts
- generated marketplace search phrases
- manual affiliate listing match
- product image upload
- hooks/captions/CTA
- AI image edits
- deterministic vertical-video template generation
- approval queue
- manual export
- basic analytics import
- audit/debug pages

### Not required for MVP
- fully automated Shopee product discovery
- TikTok Creator Affiliate API
- automatic public TikTok posting
- automatic Meta posting
- generative AI video
- multi-tenant billing
- complex ML ranking
- mobile app
- microservices/Kubernetes

---

## 31. Future Adapters

The architecture must make these replaceable:

```text
TrendSource
NewsSource
WeatherSource
CommerceSource
AffiliateProductProvider
CreativeProvider
Publisher
AnalyticsProvider
```

This lets Tr3ndly move from manual marketplace matching to official marketplace APIs later without changing the opportunity engine.

---

## 32. Definition of the Product

**Tr3ndly discovers what people are likely to need or want right now, explains why, helps the operator find an affiliate-eligible version of that product, and turns the opportunity into reviewable affiliate content.**
