# Carbon-DEVTrials-Guidewire
#  Carbon — Parametric Income Disruption Insurance
### Guidewire DEVTrails 2026 · Phase 1 Submission · Seed Phase


Carbon is an AI-enabled parametric microinsurance platform purpose-built for **Food Delivery Partners** across India. When an uncontrollable external disruption — a flash flood, a declared curfew, a city-wide platform outage — halts their ability to earn, Carbon automatically detects it, validates it, and transfers the lost wages directly to their UPI account. No claim forms. No adjusters. No waiting.

---

## 📋 Table of Contents

1. [The Problem](#1-the-problem)
2. [Persona & Scenario Workflow](#2-persona--scenario-workflow)
3. [Weekly Premium Model](#3-weekly-premium-model)
4. [Parametric Triggers](#4-parametric-triggers)
5. [AI & ML Integration Plan](#5-ai--ml-integration-plan)
6. [🚨 Market Crash Response — Adversarial Defense & Anti-Spoofing Strategy](#6--market-crash-response--adversarial-defense--anti-spoofing-strategy)
7. [Platform Choice: Why Mobile?](#7-platform-choice-why-mobile)
8. [Coverage Scope & Exclusions](#8-coverage-scope--exclusions)
9. [Insurance Product Policy Summary](#9-insurance-product-policy-summary)
10. [Tech Stack & Development Plan](#10-tech-stack--development-plan)
---

video link https://youtu.be/k3IPFErejSI?si=UUpec16teziKpbC_

## 1. The Problem

India's food delivery ecosystem runs on the backs of delivery partners. An estimated 5–7 million workers operate across food delivery platforms in a purely gig-based model with no guaranteed income, no sick pay, and no protection from forces outside their control.

When a sudden flash flood inundates a zone, when a government-declared curfew shuts down movement, or when a platform-wide outage kills order flow for hours — these workers lose real money immediately. Research indicates such disruptions can erase **20–30% of monthly earnings** with zero recourse.

**Traditional insurance has failed this segment entirely:**
- Monthly or annual premiums don't align with weekly cash cycles
- Manual claims processes take days or weeks — useless for someone who needs money tonight
- No product exists that covers pure income loss from weather/social disruptions for gig workers

**Carbon exists to close this gap.**

---

## 2. Persona & Scenario Workflow

### Target Persona
**Food Delivery Partners** operating across food delivery platforms in Tier 1 & Tier 2 Indian cities. Full-time riders earning ₹8,000–₹18,000/week and part-time riders earning ₹3,000–₹7,000/week.

### The Core Scenario

> Ravi is a full-time food delivery partner in Chennai. It's a Wednesday evening — peak hour. He picks up an order from a restaurant (Point Y) heading to a customer (Point Z). Midway, a flash flood from unseasonal rainfall inundates the route. Roads are impassable. He marks himself online but cannot move. He loses 4 hours of earning time.

**Without Carbon:** Ravi loses ₹600–₹800 in wages with no recourse.

**With Carbon:** Here is what happens silently in the background:

```
[1] PASSIVE MONITORING
    Carbon app runs in background during active shift.
    GPS & accelerometer track movement state.

[2] ROUTE INTELLIGENCE
    Carbon detects active delivery route bounding box
    from intercepted platform push notification.
    Zone: Chennai South → Anna Nagar corridor

[3] TRIGGER CHECK (< 5 minutes)
    Open-Meteo API: Rainfall = 68mm/hr (threshold: ≥50mm/hr ✅)
    TomTom API: Status = "Road Closed" on route ✅
    IMD Feed: No active all-clear signal ✅
    Ravi's platform status: Online, zero orders assigned ✅

[4] AUTOMATED CLAIM INITIATED
    Event classified: STANDARD (duration < 6 hours)
    Fraud engine clears Ravi (GPS authentic, earnings history normal)
    Policy engine confirms: premium paid ✅, waiting period elapsed ✅,
    activity threshold (3+ delivery days this week) ✅

[5] PAYOUT COMPUTED & SENT (within 2–4 hours)
    IDI = ₹10,500 ÷ 7 = ₹1,500/day
    Coverage Rate (Medium Risk Zone): 70%
    Disruption hours: 4hrs → 0.5 disruption days credited
    Payout = ₹1,500 × 70% × 0.5 = ₹525 → UPI transfer initiated

[6] RAVI NOTIFIED
    SMS + in-app: "₹525 credited to your UPI for the Chennai flood
    disruption. Claim Ref: CRB-20260318-00412."
```

Ravi never filed a claim. Carbon did it for him.

---

## 3. Weekly Premium Model

Gig workers operate on a week-to-week cash cycle. Annual or monthly premiums are structurally incompatible with this reality. Carbon's premium is computed fresh every week.

### Premium Formula

```
Weekly Premium = Insured Weekly Income (IWI) × Risk Zone Rate × Stabilization Factor (SF)

+ GST @ 18% (CGST 9% + SGST 9%)
```

**Where:**
- **IWI** = Sum of gross platform earnings in the last 7 days (sourced via platform OAuth API)
- **Risk Zone Rate** = Determined by the worker's primary operating zone (reviewed quarterly):

| Zone Code | Risk Level | Premium Rate | Coverage Rate |
|-----------|-----------|-------------|--------------|
| LR-1 | Low | 0.50% of IWI | 60% of IDI |
| MR-2 | Medium | 1.00% of IWI | 70% of IDI |
| HR-3 | High | 2.00% of IWI | 80% of IDI |

- **Stabilization Factor (SF)** = A temporary multiplier (max 1.15×) applied in early pool cycles to ensure reserve liquidity. SF reduces to exactly 1.0 once the pool achieves its target 20% reserve ratio — at which point it has zero effect on premium.

### Illustrative Weekly Premiums

| Rider Type | Weekly Income | Zone | Rate | SF | Base Premium | GST | Total |
|-----------|--------------|------|------|----|-------------|-----|-------|
| Part-time / Low Risk | ₹5,250 | LR-1 | 0.50% | 1.05 | ₹27.56 | ₹4.96 | ₹32.52 |
| Full-time / Medium Risk | ₹10,500 | MR-2 | 1.00% | 1.00 | ₹105.00 | ₹18.90 | ₹123.90 |
| High-earner / High Risk | ₹17,500 | HR-3 | 2.00% | 1.00 | ₹350.00 | ₹63.00 | ₹413.00 |

### Key Design Decisions
- **Activity Scaling:** A part-time rider earning ₹3,000/week in a medium-risk zone pays ~₹30/week. A full-timer earning ₹15,000/week pays ~₹150/week. The premium is proportional — it is not flat.
- **Auto-Deduction:** Weekly premium auto-debited every Monday via UPI Autopay (NACH mandate) — no manual payment friction.
- **2-Day Waiting Period:** Coverage activates 48 hours after each premium payment. This prevents adverse selection (workers joining only because a storm is forecast).
- **Lapse & Re-activation:** If payment fails, coverage lapses immediately. Re-activation requires paying outstanding premium; a fresh 2-day waiting period applies.

---

## 4. Parametric Triggers

Carbon removes the claims adjuster entirely by using real-time, verifiable API data as the sole arbiter of payout decisions. Three categories of triggers are defined:

### Trigger Category 1 — Environmental (Weather)

| Disruption | Standard Threshold | Severe Threshold | Data Source |
|-----------|-------------------|-----------------|------------|
| Rainfall / Flash Flood | ≥ 50mm/hr for 3+ hours | ≥ 100mm/hr or IMD Red Alert | Open-Meteo API, IMD OpenData |
| Heatwave | ≥ 45°C sustained 3+ hours | ≥ 47°C or state advisory | IMD API |
| Severe Air Pollution | AQI ≥ 301 (PM2.5 basis) | AQI ≥ 401 + work stoppage order | CPCB AQI API |
| Flood Declaration | Local ward/zone flooding | District-level disaster declaration | NDMA / State DM Portal |

### Trigger Category 2 — Social / Governmental

| Disruption | Standard Threshold | Severe Threshold | Data Source |
|-----------|-------------------|-----------------|------------|
| Bandh / Curfew | Notified zone bandh / blockage | City/state-wide curfew or emergency | District Admin Portal / News API |
| Road Closure | Official road blockage on active route | Multi-route / zone-wide closure | TomTom Traffic API |

### Trigger Category 3 — Platform / Market

| Disruption | Standard Threshold | Severe Threshold | Data Source |
|-----------|-------------------|-----------------|------------|
| Platform Outage | Platform API down ≥ 3 hours while driver online | Platform down ≥ 6 hours | Zomato/Swiggy Platform Status API |
| Order Volume Crash | > 50% drop vs. 7-day zone average | > 70% drop across zone | Platform API (aggregated) |

### Event Escalation Model
Events start at **Standard** tier (3–4 day payout cap/week). If a Standard event exceeds 6 continuous hours or spreads to 3+ adjacent zones, it auto-escalates to **Severe** (up to 7-day full-week coverage, no cap). Critically — the worker is never held waiting for a severity verdict. Payouts begin at Standard the moment thresholds are met. If it escalates, a retroactive top-up is applied.

### Crowdsourced SOS Trigger (API Fallback)
When primary APIs are unavailable or event is hyper-local, workers can submit a geo-tagged live camera photo via the app. Carbon requires:
- **Consensus threshold:** 3+ independent SOS reports within a 500m radius within 30 minutes
- **Uniqueness check:** Each submission is perceptual-hashed; duplicate photos (including screen-photographed images) are silently rejected
- **Result:** A parametric "Red Zone" is declared, triggering Standard-tier coverage for that micro-zone

---

## 5. AI & ML Integration Plan

Carbon draws a deliberate architectural distinction between Machine Learning (pattern recognition on historical data) and AI/real-time inference systems (live gatekeeping). This separation ensures capital efficiency and fraud prevention.

### Machine Learning — The Data Crunchers

**1. Dynamic Weekly Premium Engine**
A gradient-boosted regression model (XGBoost) adjusts the weekly premium based on hyper-local historical risk signals for each zone:
- Historical disruption frequency and duration per zone (last 24 months)
- Seasonal rainfall/heat patterns per city micro-zone
- Historical claim loss ratio per zone segment
- Example output: Zone MR-2-South Chennai has 3× higher flood disruption frequency than MR-2-North Chennai → ML adjusts effective zone rate from 1.00% to 1.15% for that sub-zone, while keeping the worker's zone classification fair

**2. Sensor Anomaly Detection (Anti-GPS-Spoofing)**
An LSTM sequence model continuously analyzes the time-series of:
- GPS coordinates (position, speed, trajectory)
- Accelerometer data (vibration signature matching real road movement)
- Gyroscope data (orientation consistent with two-wheeler on road)

Synthetic GPS movement (e.g., from spoofing apps) produces "too smooth" trajectories with abnormal accelerometer silence. The model flags kinematically impossible movement patterns in real time.

**3. Earnings Baseline Model**
A rolling 30-day median model per worker detects IDI inflation attempts. If a worker's claimed IWI suddenly spikes >30% above their 30-day median, the anomaly is flagged and IDI is capped at the verified platform API figure.

### AI — The Real-Time Gatekeepers

**1. Perceptual Image Hashing for SOS Fraud**
Every SOS photo submission is processed through a perceptual hash pipeline (dHash + pHash). Submissions are compared against a rolling cache of recent submissions in the same zone. Near-identical images (hash distance < 10) are automatically rejected as duplicates — catching coordinated syndicate submissions.

**2. Moiré Pattern Detection**
A convolutional neural network scans SOS images for Moiré interference patterns — the telltale artifact that appears when a photo is taken of a digital screen (laptop, phone, monitor). This instantly blocks the simplest form of image fraud: photographing a fake disruption image from another device's screen. Live camera captures are enforced at the OS level (gallery uploads blocked), and this CV layer provides a second line of defense.

**3. Real-Time Fraud Scoring**
Every claim event passes through a multi-layer fraud scoring pipeline before payout approval:

| FRAUD SIGNAL | DETECTION METHOD | OUTCOME |
|--------------|------------------|---------|
| GPS Spoofing | Cell-tower triangulation cross-check + ML kinematic anomaly model | Claim void; account flagged |
| Fake Weather Claim | Requires ≥10 worker corroboration in same zone | Suspended pending zone validation |
| Duplicate SOS Photo | SHA-256 hash + pHash similarity | Silently rejected |
| Screen Photo | Moiré CNN detection | Rejected; worker warned |
| Inactive During Event | Platform API: zero orders received, not merely unassigned | Payout adjusted/rejected |
| Premium Abuse (join-during-alert) | 2-day waiting period + serial enrollment timing analytics | Payout blocked; repeat offenders barred |
| Earnings Inflation | IDI vs. 30-day platform median | IDI capped at verified figure |

---

## 6. 🚨 Market Crash Response — Adversarial Defense & Anti-Spoofing Strategy

> **Scenario:** A coordinated fraud ring of 500 delivery partners is using fake GPS signals to claim payouts during fabricated disruptions. Simple GPS verification is dead. The liquidity pool is under attack.

This section documents Carbon's architectural response to exactly this threat vector.

### The Attacker's Playbook

A coordinated fraud ring targeting a parametric insurance pool has three primary attack vectors:

1. **GPS Spoofing at Scale** — Using mock location apps or hardware spoofers to place themselves "on route" during a genuine disruption, even if they were home
2. **Synthetic Disruption Farming** — Coordinating SOS reports across fake or real accounts to artificially trigger a Red Zone in areas with no actual disruption
3. **Earnings Inflation Before a Known Storm** — Temporarily inflating earnings in the days before a forecast storm to increase IDI and therefore maximize payout

Carbon's defense is layered, probabilistic, and designed around a core principle: **It is extremely difficult to fake multiple independent, physics-consistent signals simultaneously.**

---

### Layer 1 — Kinematic Consistency Engine (Catching the Faker)

A genuine stranded delivery rider exhibits a highly specific behavioral signature:
- GPS position: stationary or very slow drift
- Accelerometer: micro-vibrations consistent with an idling two-wheeler engine (3–8 Hz vibration band)
- Gyroscope: small-angle oscillations consistent with a vehicle in idle
- Platform status: online, ping active, zero orders assigned/completed

A GPS spoofer sitting at home exhibits:
- GPS position: matches spoofed location
- Accelerometer: **silence** — no road vibration, no engine idle signature, possibly steady (person sitting in a chair)
- Gyroscope: **flat** — no two-wheeler micro-corrections

**The ML model does not look at GPS alone. It evaluates the entire kinematic fingerprint.** A synthetic GPS track cannot replicate the physics of a real two-wheeler sitting in floodwater. This is the primary GPS anti-spoofing mechanism.

**Secondary check:** Cell tower triangulation. The device's connected cell towers are cross-referenced against the spoofed GPS coordinates. In dense urban environments, the cell tower network provides ~100–200m positional accuracy. If the spoofed GPS says "Anna Nagar" but the cell towers say "Tambaram," the claim is flagged immediately.

**Honest worker protection:** A genuinely stranded rider will have authentic accelerometer + gyroscope data, authentic cell tower positioning, and an authentic engine-idle vibration signature. The model is tuned with a high recall for genuine claims — false negatives (rejecting real workers) are treated as the costlier error than false positives.

---

### Layer 2 — Zone Corroboration Requirement (Catching the Syndicate)

A lone GPS spoofer can fake being in a flood zone. A coordinated ring of 500 spoofers can theoretically all claim to be in the same zone. Carbon addresses this with a critical protocol:

**For environmental triggers (weather/flood), Carbon requires independent corroboration from ≥10 workers in the zone before any payouts are issued.**

However, "corroboration" is defined strictly:
- Each of the 10+ workers must show an **independent kinematic fingerprint** (no two fingerprints can be suspiciously similar)
- The corroborating workers must be **spatially distributed** across the zone, not clustered at one GPS point
- The corroboration must be **temporally staggered** — all 10 simultaneous reports from accounts that were created within 48 hours of each other is a red flag, not validation

**What catches a fraud ring of 500:**
- 500 accounts all spoofing to within a 200m radius → spatial clustering alert triggers
- 500 accounts all showing identical accelerometer silence → kinematic homogeneity flag
- 500 accounts with enrollment dates within the same 2-week window + all claiming simultaneously → syndicate enrollment pattern detected

**Cross-reference with primary API data:** Carbon never relies solely on worker reports. If 500 workers claim a flood disruption but the Open-Meteo API shows 2mm of rainfall in that zone, the environmental trigger fails. No workers can manufacture an API-verified weather event. This is the single most powerful defense against synthetic disruption farming.

---

### Layer 3 — Behavioral Timeline Analysis (Catching the Opportunist)

**Premium Abuse (Join-Before-Storm):**
Carbon's 2-day waiting period is the first line of defense. But it is strengthened by a behavioral pattern detector:
- Workers who enroll 48–72 hours before a forecast weather event (detectable via public IMD/weather API forecast data) are flagged as "adversarial enrollment" candidates
- Their first claim event is subject to enhanced review — kinematic fingerprint is analyzed with stricter thresholds
- Workers with 3+ instances of this pattern are permanently barred from the pool

**Earnings Inflation (IDI Manipulation):**
A worker may attempt to do unusually high-volume deliveries in the 3–5 days before a known storm to inflate their IWI and thus IDI.
- Carbon's IDI calculation uses the 7-day earnings window, but the anomaly model checks this against a 30-day rolling median
- If the 7-day IWI is >30% above the 30-day median, the IDI used for payout is **capped at the median-based figure**, not the inflated 7-day figure
- The worker is notified of the cap transparently in their policy dashboard

---

### Layer 4 — SOS Photo Integrity (Catching Image Fraud)

This is documented in Section 5 (AI Integration) but summarized here in the fraud-defense context:

| Attack | Detection | Response |
|--------|-----------|----------|
| Submitting the same photo multiple times | Perceptual hash (dHash + pHash) — hash distance check | Silently rejected; counter incremented |
| Photographing a screen showing a fake flood image | Moiré pattern CNN | Rejected; worker warned |
| Using a gallery image instead of live camera | OS-level live camera enforcement | Blocked before submission |
| Coordinated identical images across accounts | Cross-account hash similarity clustering | Red flag; zone suspended; fraud investigation opened |

---

### Layer 5 — Pool-Level Anomaly Monitoring (Catching the Drain)

Carbon monitors the Income Protection Pool in real-time for anomalous drain patterns:
- **Sudden spike in claims from a single zone** → Triggers enhanced kinematic review for all claims in that zone for that event
- **Claim rate > 2× the historical zone average for that disruption type** → Event is temporarily paused; primary API data is re-validated before payouts resume
- **Loss ratio trending above 65%** → Actuarial alert triggered; SF may be temporarily adjusted per IRDAI guidelines

**The pool has a reinsurance layer** for catastrophic events (major cyclones, multi-city shutdowns) that exceed the pool's self-retention limit (trigger: >₹80,000 in a single event window for the illustrative 1,000-worker pool). This protects against both genuine catastrophic events and against coordinated attacks designed to drain the pool in a single event.

---

### How Carbon Tells the Faker from the Genuinely Stranded Worker

The decision tree is probabilistic, not binary:

| SIGNAL | GENUINE WORKER | SPOOFER / FRAUD |
|--------|----------------|-----------------|
| GPS position | Matches zone | Matches zone (spoofed) |
| Cell tower position | Matches GPS ✅ | Contradicts GPS ❌ |
| Accelerometer signature | Idle engine vibration ✅ | Silence / sitting pattern ❌ |
| Gyroscope | Small corrections ✅ | Flat ❌ |
| Platform status | Online, no orders ✅ | Online, no orders (same) |
| Spatial distribution | Distributed in zone | Clustered at one point ❌ |
| Zone corroboration (≥10) | Diverse fingerprints ✅ | Homogeneous fingerprints ❌ |
| Primary API (weather/traffic) | Confirms event ✅ | Confirms event (can't fake this) ✅ |
| Enrollment timing | Normal history | Recent enrollment pre-storm ❌ |
| IWI vs. 30-day median | Normal ✅ | Inflated ❌ |

A genuine worker will pass nearly all signals. A spoofer will fail multiple independent signals simultaneously. The fraud engine requires a **weighted confidence score** across all signals — not a single-point check. This is why it cannot be defeated by fixing just one signal.

---

### No Honest Workers Punished

Carbon's fraud system is explicitly designed to minimize false positives:
- **Recall over precision** — the cost of wrongly denying a genuine claim (losing a worker's trust, brand damage, potential regulatory action) outweighs the cost of paying a borderline claim
- **Transparent flagging** — if a claim is held for enhanced review, the worker is notified immediately with a reference ID and a 48-hour resolution commitment
- **Human review escalation** — any worker can request a human review of an automated decision within 30 days
- **Zone-level decisions protect individual workers** — a fraud investigation triggered by a syndicate does not automatically deny individual workers in the zone; their claims are reviewed independently

---

## 7. Platform Choice: Why Mobile?

Carbon is built as a **Flutter (Dart) mobile application**, not a web platform. This is a functional necessity, not a design preference.

| Requirement | Why Mobile is the Only Option |
|-------------|-------------------------------|
| Background GPS tracking | Web browsers cannot run persistent background location processes. A native mobile app is required to silently track a rider's GPS position during their active shift. |
| Accelerometer + Gyroscope access | Browser APIs for motion sensors are unreliable, permission-heavy, and iOS-restricted. Native mobile apps have direct, always-on hardware sensor access — essential for the kinematic anti-spoofing engine. |
| Push notification interception | Intercepting food delivery platform push notifications to extract route data (pickup → drop coordinates) requires deep OS-level integration. Only native apps can do this reliably on Android. |
| Live Camera enforcement | Blocking gallery uploads and forcing live-capture-only for SOS photos requires native camera API control. Web `<input type="file">` cannot enforce live camera. |
| UPI deep-linking | Initiating UPI payment confirmations and mandate setup requires native deep-link integration with UPI apps (GPay, PhonePe, Paytm). |
| Worker demographic | Delivery partners are exclusively mobile-first. No laptop, no desktop, no web browser during shifts. |

---

## 8. Coverage Scope & Exclusions

Carbon covers **INCOME LOSS ONLY** arising from verified external disruptions. This is a core product constraint and a financial sustainability necessity.

### What Carbon Covers ✅
- Income lost during verified environmental disruptions (rainfall, flood, heatwave, severe pollution)
- Income lost during verified social/governmental disruptions (curfew, declared bandh, official road closures)
- Income lost during verified platform/market disruptions (extended outages, severe order volume crashes)

### What Carbon Strictly Excludes ❌
These exclusions are non-negotiable and encoded in the product policy:
- Medical bills, illness, hospitalisation, injury, accident, disability, or death
- Vehicle breakdown, vehicle damage, fuel costs, or any repair/maintenance expense
- Voluntary inactivity, personal rest days, or self-imposed work stoppage
- Normal or seasonal demand fluctuation or ordinary market slowdown
- Personal disputes or domestic emergencies
- Events occurring during the mandatory 2-day waiting period
- Weeks in which the minimum 3-active-delivery-day threshold is not met
- Any fraudulent activity or wilful misrepresentation

---

## 9. Insurance Product Policy Summary

Carbon's product policy is a prototype document defining the full coverage architecture, premium mechanics, payout logic, and fraud provisions for the platform.

| Parameter | Details |
|-----------|---------|
| Product Type | Parametric Microinsurance — Income Disruption Cover |
| Target Beneficiary | Food Delivery Partners |
| Coverage Basis | Loss of Income ONLY due to verified external disruptions |
| Premium Cycle | Weekly — aligned to gig worker earnings cycle |
| Payout Mechanism | Fully automated parametric trigger — zero manual claims |
| Payout Rate | 60%–80% of Insured Daily Income (zone-dependent) |
| Waiting Period | 2 days from premium payment date |
| Minimum Activity | 3 active delivery days in preceding 7-day period |
| Payout Timeline | 2–4 hours from trigger confirmation |

The complete Product Policy Wording  governs all coverage terms, premium mechanics, payout logic, eligibility, fraud provisions, and grievance redressal which was written by team carbon, see  https://drive.google.com/file/d/1EWhg2ZPwrNTImWZpWwpxyc4IkzJhNHVm/view?usp=sharing
---

## 10. Tech Stack & Development Plan

### Core Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Mobile Frontend | Flutter (Dart) | Cross-platform (Android/iOS), hardware sensor access, background processes, single codebase |
| Backend API | FastAPI (Python 3.11) | Async support for low-latency concurrent API calls; ideal for the real-time trigger monitoring pipeline |
| Database | PostgreSQL | Robust ACID compliance for financial ledger, wallet, and policy records |
| ML Model Serving | FastAPI + ONNX Runtime | Lightweight, fast model inference without heavy ML framework overhead in production |
| Containerization | Docker / Podman | Reproducible cloud deployment; microservices separation for trigger engine, fraud engine, payout engine |

### External Integrations

| Integration | Purpose | Implementation |
|-------------|---------|----------------|
| Open-Meteo API | Real-time rainfall, temperature, weather data | Free tier — REST API polling every 5 minutes per active zone |
| IMD OpenData API | Official Indian Meteorological Dept. feeds (Red Alert, flood declarations) | Official govt. API |
| CPCB AQI API | Real-time Air Quality Index data | Free government API |
| TomTom Traffic API | Road closure detection, severe congestion, route blockages | Free tier for hackathon; Wildcard API upgrade available |
| Food Delivery Platform Status API | Order volume data, platform uptime, driver activity logs | OAuth integration — simulated for Phase 1 |
| Razorpay UPI Sandbox | Premium collection, payout disbursement, UPI mandate setup | Test/sandbox mode for Phase 1 |
| DigiLocker / CKYC | KYC verification (Aadhaar + PAN) at onboarding | Simulated for Phase 1 |


