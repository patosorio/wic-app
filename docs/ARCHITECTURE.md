# Vinyl Platform — System Architecture

> Version 1.0 | Status: Approved for Development
> Stack: FastAPI · PostgreSQL · Firestore · Next.js · GCP · Stripe

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Service Decomposition & Module Map](#2-service-decomposition--module-map)
3. [Database Ownership Boundaries](#3-database-ownership-boundaries)
4. [Event Catalog](#4-event-catalog)
5. [Critical Data Flows](#5-critical-data-flows)
6. [Tech Stack Reference](#6-tech-stack-reference)

---

## 1. System Overview

The platform enables independent artists to press vinyl records through a pre-sale crowdfunding model. Artists upload releases, fans pre-order within a 30-day campaign window, and physical production begins only when the minimum target is reached.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                           │
│                                                                 │
│   Next.js (TypeScript)          Firestore SDK (real-time)       │
│   - Campaign pages              - Live campaign counters        │
│   - Artist dashboard            - Production stage updates      │
│   - My Box                      - Box status updates            │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────────┐
│                    SERVICE A — PLATFORM API                     │
│                  FastAPI · Cloud Run · Public                   │
│                                                                 │
│  auth │ catalog │ campaigns │ commerce │ fulfillment │          │
│  discovery │ engagement                                         │
│                                                                 │
│  → Writes source of truth to PostgreSQL                         │
│  → Writes real-time projections to Firestore                    │
│  → Publishes domain events to Pub/Sub                           │
└──────────┬───────────────────────────┬──────────────────────────┘
           │ Pub/Sub (async)           │ Internal HTTP (sync queries)
┌──────────▼───────────────────────────▼──────────────────────────┐
│                  SERVICE B — OPERATIONS API                     │
│                FastAPI · Cloud Run · Internal only              │
│                                                                 │
│  production │ logistics │ inventory │ shipping                  │
│                                                                 │
│  → Subscribes to Pub/Sub events from Platform service                  │
│  → Manages production workflow state machine                    │
│  → Exposes internal endpoints for Platform service queries             │
└─────────────────────────────────────────────────────────────────┘
           │                           │
┌──────────▼──────────┐   ┌────────────▼──────────────────────────┐
│   PostgreSQL        │   │   Firestore                           │
│   Cloud SQL         │   │                                       │
│                     │   │  - Release metadata (documents)       │
│  - Orders           │   │  - Real-time projections              │
│  - Payments         │   │  - Notification history               │
│  - Campaigns        │   │  - User preferences / wishlists       │
│  - Inventory        │   │                                       │
│  - Points ledger    │   └───────────────────────────────────────┘
│  - Users / Auth     │
└─────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                     SUPPORTING SERVICES                         │
│                                                                 │
│  Firebase Auth     → JWT issuance, social login, role claims    │
│  Stripe            → Payments, refunds, webhook events          │
│  Cloud Storage     → WAV files, artwork, label images           │
│  Cloud Tasks       → Scheduled day-30 campaign evaluation jobs  │
│  Cloud Pub/Sub     → Async event bus between services           │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Model

| Unit | Type | Visibility | Runtime |
|------|------|------------|---------|
| Platform service | Cloud Run container | Public (HTTPS) | FastAPI async |
| Operations service | Cloud Run container | Internal only | FastAPI async |
| Frontend | Vercel or Cloud Run | Public | Next.js SSR |
| DB | Cloud SQL (Postgres) | Private VPC | Managed |
| Documents | Firestore | Private (SDK auth) | Managed |

### Monorepo Structure

```
/
├── backend/
│   ├── shared/          ← GCP clients, base models, exceptions
│   ├── platform_api/   ← Platform API
│   └── operations/       ← Operations API
├── frontend/            ← Next.js app
├── infra/               ← Cloud Run, Pub/Sub, Cloud Tasks configs
├── .cursor/
│   └── rules/           ← Cursor AI rules per domain
└── docs/
    └── ARCHITECTURE.md  ← this file
```

---

## 2. Service Decomposition & Module Map

### Core Principle

Modules never cross-import each other's internals. All inter-module communication goes through the module's public service interface (`module/service.py`). This contract can become an HTTP call or Pub/Sub topic in the future without rewriting business logic.

### Platform service — Platform API

```
backend/platform_api/
│
├── core/
│   ├── firebase_auth.py     ← JWT verification middleware (all routes)
│   ├── events.py            ← All Pub/Sub publish calls (single location)
│   ├── firestore.py         ← All Firestore projection writes (single location)
│   └── config.py            ← Settings, env vars
│
├── auth/
│   ├── router.py            ← /auth/* endpoints
│   ├── service.py           ← Role resolution, session management
│   └── models.py            ← User, Role (Postgres)
│
├── catalog/
│   ├── router.py            ← /releases/* endpoints
│   ├── service.py           ← Release creation, audio/artwork upload
│   ├── models.py            ← Release (Postgres FK), ReleaseDoc (Firestore)
│   └── storage.py           ← Cloud Storage upload helpers
│
├── campaigns/
│   ├── router.py            ← /campaigns/* endpoints
│   ├── service.py           ← Campaign lifecycle management
│   ├── models.py            ← Campaign, CampaignEvent (Postgres)
│   └── state_machine.py     ← Explicit state transitions (NOT status fields)
│
├── commerce/
│   ├── router.py            ← /orders/*, /payments/* endpoints
│   ├── service.py           ← Order creation, payment capture, refunds
│   ├── models.py            ← Order, PaymentEvent (Postgres)
│   └── stripe_client.py     ← Stripe SDK wrapper + webhook handler
│
├── fulfillment/
│   ├── router.py            ← /box/*, /shipments/* endpoints
│   ├── service.py           ← Box management, shipment requests
│   └── models.py            ← Box, BoxItem, Shipment (Postgres)
│
├── discovery/
│   ├── router.py            ← /homepage, /search endpoints
│   └── service.py           ← Feed composition, trending logic
│
└── engagement/
    ├── router.py            ← /points/*, /notifications/* endpoints
    ├── service.py           ← Points earn/spend, notification dispatch
    ├── models.py            ← PointsLedger (append-only, Postgres)
    └── ledger.py            ← Ledger operations (never direct balance update)
```

### Operations service — Operations API

```
backend/operations/
│
├── core/
│   ├── events.py            ← All Pub/Sub subscriptions (single location)
│   └── config.py
│
├── production/
│   ├── router.py            ← /production/* endpoints (internal)
│   ├── service.py           ← Production job management
│   ├── models.py            ← ProductionJob, Stage, Approval (Postgres)
│   └── state_machine.py     ← 9-stage production workflow
│
├── logistics/
│   ├── router.py            ← /logistics/* endpoints (internal)
│   └── service.py           ← Logistics dashboard data
│
├── inventory/
│   ├── router.py            ← /inventory/* endpoints (internal)
│   ├── service.py           ← Copy allocation management
│   └── models.py            ← InventoryLot, Allocation (Postgres)
│
└── shipping/
    ├── router.py            ← /shipping/* endpoints (internal)
    ├── service.py           ← Shipment processing
    └── calculator.py        ← Cost calculation by location + quantity
```

### Shared Library

```
backend/shared/
├── gcp/
│   ├── pubsub.py            ← Pub/Sub client (publish + subscribe base)
│   ├── firestore.py         ← Firestore client initialisation
│   ├── storage.py           ← Cloud Storage client
│   └── tasks.py             ← Cloud Tasks client
├── models/
│   └── base.py              ← Base Pydantic models, common types
└── exceptions/
    └── base.py              ← Common exception types
```

### User Roles & Surface Access

| Role | Service | Access |
|------|---------|--------|
| Customer | Platform service | Browse, pre-order, My Box, shipping |
| Artist | Platform service | Upload releases, campaign dashboard, approve masters |
| Logistics | Operations service | Production workflow, inventory, shipments |
| Admin | Platform service + B | Full system, statistics, user management |

---

## 3. Database Ownership Boundaries

### Rule

Each module owns its tables exclusively. No module queries another module's tables directly. Cross-module data access goes through the owning module's service interface.

```python
# WRONG — direct cross-module DB query
from platform_api.auth.models import User
user = db.query(User).filter(User.id == user_id).first()

# CORRECT — through the owning module's service
from platform_api.auth.service import get_user
user = await get_user(user_id, db)
```

---

### PostgreSQL — Relational Source of Truth

**auth module**
```
users
  id              UUID PK
  firebase_uid    VARCHAR UNIQUE      ← Firebase Auth link
  email           VARCHAR UNIQUE
  role            ENUM (customer, artist, logistics, admin)
  created_at      TIMESTAMP
```

**catalog module**
```
releases
  id              UUID PK
  artist_id       UUID FK → users.id
  firestore_doc   VARCHAR             ← Firestore document ID for metadata
  status          ENUM (draft, active, archived)
  format          ENUM (10in, 12in, 2x12in)
  created_at      TIMESTAMP
```

**campaigns module**
```
campaigns
  id              UUID PK
  release_id      UUID FK → releases.id
  status          ENUM (draft, active, funded, failed, refunding, closed)
  target          INTEGER DEFAULT 30
  current_count   INTEGER DEFAULT 0
  presale_price   DECIMAL(10,2)
  retail_price    DECIMAL(10,2)
  starts_at       TIMESTAMP
  ends_at         TIMESTAMP

campaign_events                       ← State transition audit log
  id              UUID PK
  campaign_id     UUID FK → campaigns.id
  from_status     VARCHAR
  to_status       VARCHAR
  triggered_by    VARCHAR             ← system | user_id
  occurred_at     TIMESTAMP
```

**commerce module**
```
orders
  id              UUID PK
  campaign_id     UUID FK → campaigns.id
  customer_id     UUID FK → users.id
  status          ENUM (pending_campaign, in_production, refunded, completed)
  amount          DECIMAL(10,2)
  stripe_payment_intent_id  VARCHAR UNIQUE
  created_at      TIMESTAMP

payment_events                        ← Idempotency log — NEVER skip this
  id              UUID PK
  order_id        UUID FK → orders.id
  stripe_event_id VARCHAR UNIQUE      ← Idempotency key
  event_type      VARCHAR
  payload         JSONB
  processed_at    TIMESTAMP
```

**fulfillment module**
```
boxes
  id              UUID PK
  customer_id     UUID FK → users.id

box_items
  id              UUID PK
  box_id          UUID FK → boxes.id
  order_id        UUID FK → orders.id
  status          ENUM (pre_order, in_production, ready, in_box, shipped, delivered)
  updated_at      TIMESTAMP

shipments
  id              UUID PK
  box_id          UUID FK → boxes.id
  status          ENUM (requested, processing, dispatched, delivered)
  tracking_number VARCHAR
  shipping_cost   DECIMAL(10,2)
  destination     JSONB
  requested_at    TIMESTAMP
```

**engagement module**
```
points_ledger                         ← Append-only. NEVER update a row.
  id              UUID PK
  user_id         UUID FK → users.id
  delta           INTEGER             ← positive = earn, negative = spend
  action          VARCHAR             ← pre_order, wishlist, store_purchase
  reference_id    UUID                ← order_id or campaign_id
  occurred_at     TIMESTAMP
```

**production module** (Operations service)
```
production_jobs
  id              UUID PK
  campaign_id     UUID
  release_id      UUID
  status          ENUM (pending, in_progress, completed)
  pressing_qty    INTEGER
  created_at      TIMESTAMP

production_stages
  id              UUID PK
  job_id          UUID FK → production_jobs.id
  stage           ENUM (mastering, master_approval, lacquer_cutting, galvanic,
                        test_pressing, test_pressing_approval, final_pressing,
                        warehouse_arrival, shipping)
  status          ENUM (pending, in_progress, awaiting_approval, approved, completed)
  started_at      TIMESTAMP
  completed_at    TIMESTAMP

production_approvals
  id              UUID PK
  stage_id        UUID FK → production_stages.id
  approved_by     UUID                ← artist user_id
  approved_at     TIMESTAMP
  notes           TEXT
```

**inventory module** (Operations service)
```
inventory_lots
  id              UUID PK
  production_job_id UUID FK → production_jobs.id
  total_qty       INTEGER
  created_at      TIMESTAMP

inventory_allocations
  id              UUID PK
  lot_id          UUID FK → inventory_lots.id
  bucket          ENUM (presale_buyers, wholesale, artist, platform_store)
  quantity        INTEGER
  allocated_at    TIMESTAMP
```

---

### Firestore — Documents & Real-Time Projections

**Rule:** Firestore is never the source of truth. It is a read model. PostgreSQL owns authoritative state. Platform service writes projections to Firestore on every state change.

```
/releases/{release_id}
  title           string
  artist_name     string
  catalog_number  string
  format          string
  audio_urls      map        ← Cloud Storage signed URLs
  artwork_urls    map
  label_color     string
  tracklist       array
  description     string
  tags            array

/campaigns/{campaign_id}               ← Real-time projection
  release_id      string
  status          string
  current_count   number               ← Incremented on every pre-order
  target          number
  percentage      number
  days_remaining  number
  presale_price   number
  ends_at         timestamp

/production_stages/{job_id}            ← Real-time projection
  release_id      string
  current_stage   string
  stages          array of {stage, status, completed_at}

/box_items/{customer_id}               ← Real-time projection
  items           array of {order_id, release_title, status, artwork_url}

/notifications/{user_id}/items/{id}
  type            string
  message         string
  read            boolean
  created_at      timestamp

/user_preferences/{user_id}
  wishlists       array
  notification_settings  map
```

---

## 4. Event Catalog

All Pub/Sub events are published from `core/events.py` and consumed in `operations/core/events.py`. Event names follow `domain.entity.action` convention.

| Topic | Published by | Consumed by | Trigger |
|-------|-------------|-------------|---------|
| `campaign.funded` | Platform service | Operations service | Campaign reaches 30 pre-orders |
| `campaign.failed` | Platform service | Platform service | Day-30 job, target not reached |
| `campaign.presale_incremented` | Platform service | Platform service | New pre-order placed |
| `production.stage_updated` | Operations service | Platform service | Logistics updates a stage |
| `production.approval_required` | Operations service | Platform service | Stage needs artist sign-off |
| `production.completed` | Operations service | Platform service | Final pressing done, warehouse arrival |
| `record.arrived_warehouse` | Operations service | Platform service | Records received at warehouse |
| `shipment.dispatched` | Operations service | Platform service | Shipment sent to customer |
| `payment.refund_initiated` | Platform service | — | Refund issued to Stripe |
| `payment.refund_completed` | Platform service | — | Stripe confirms refund |

### Event Payload Convention

Every event includes a standard envelope:

```json
{
  "event_id": "uuid-v4",
  "topic": "campaign.funded",
  "occurred_at": "2025-01-01T12:00:00Z",
  "version": "1.0",
  "payload": {
    // domain-specific fields
  }
}
```

### Side Effects Per Event

**`campaign.funded`**
- Operations service: Create `ProductionJob`, set first stage to `in_progress`
- Platform service: Update all orders status → `in_production`
- Platform service: Write Firestore projection update
- Platform service: Send notifications to all pre-order customers

**`campaign.failed`**
- Platform service: Batch Stripe refunds (idempotent — check `payment_events` first)
- Platform service: Update all orders status → `refunded`
- Platform service: Send refund notifications to customers
- Platform service: Archive release in catalog

**`production.stage_updated`**
- Platform service: Write Firestore `/production_stages/{job_id}` projection
- Platform service: Send notification to artist if approval required

**`record.arrived_warehouse`**
- Platform service: Update all `box_items` status → `ready`
- Platform service: Write Firestore `/box_items/{customer_id}` projections
- Platform service: Send notifications to all box item owners

**`shipment.dispatched`**
- Platform service: Update `box_items` status → `shipped`
- Platform service: Write Firestore projection
- Platform service: Send shipping notification with tracking number

---

## 5. Critical Data Flows

### Flow 1 — Customer Pre-Order

```
1. Customer clicks "Pre-Order" on campaign page
   Frontend → POST /orders/  (Platform service)

2. Platform service — commerce.service
   a. Verify Firebase JWT → resolve customer_id
   b. Check campaign status = ACTIVE
   c. Check campaign has not reached max (150)
   d. Create Order (status: PENDING_CAMPAIGN)
   e. Create Stripe PaymentIntent (immediate charge, 19.99€)
   f. Store stripe_payment_intent_id on Order

3. Stripe processes charge
   Stripe → POST /webhooks/stripe  (Platform service)

4. Platform service — stripe webhook handler
   a. Verify Stripe signature
   b. Check payment_events for stripe_event_id (idempotency)
   c. Insert PaymentEvent row
   d. Update Order status → PENDING_CAMPAIGN confirmed
   e. Increment campaigns.current_count
   f. Publish event: campaign.presale_incremented

5. Platform service — core/events.py handler
   a. Write Firestore /campaigns/{id} projection
      current_count++, percentage updated
   b. Earn 10 points → append to points_ledger
   c. Send pre-order confirmation notification

6. Frontend receives Firestore update
   Campaign progress bar updates in real-time (<1 second)

7. If current_count reaches 30
   campaigns state_machine transitions: ACTIVE → FUNDED
   Publish event: campaign.funded
   → See Flow 2
```

### Flow 2 — Campaign Funding & Production Start

```
1. Event received: campaign.funded
   Payload: { campaign_id, release_id, final_count }

2. Platform service — side effects
   a. Update all Orders for this campaign → IN_PRODUCTION
   b. Write Firestore /campaigns/{id} → status: funded
   c. Send "Campaign Funded!" notification to all pre-order customers
   d. Send notification to artist

3. Operations service — production.service (Pub/Sub consumer)
   a. Create ProductionJob (pressing_qty: 150)
   b. Create all 9 ProductionStages (status: pending)
   c. Set Stage 1 (mastering) → in_progress
   d. Publish event: production.stage_updated

4. Platform service — receives production.stage_updated
   a. Write Firestore /production_stages/{job_id}
   b. Artist dashboard updates in real-time

5. Logistics team works through stages in Operations service dashboard
   Each stage completion → production.stage_updated event
   Artist-required approvals → production.approval_required event

6. Artist approves master / test pressing
   POST /production/{job_id}/approve  (Operations service internal)
   Stage status → approved → next stage begins

7. Stage 8 — Warehouse Arrival
   Logistics marks records as arrived
   Publish event: record.arrived_warehouse
   → See Flow 3

8. Day-30 Cloud Tasks job (if campaign NOT funded)
   Cloud Tasks → POST /jobs/evaluate-campaign/{id}  (Platform service)
   campaign state_machine: ACTIVE → FAILED
   Publish event: campaign.failed
   Batch refund job runs against payment_events (idempotent)
```

### Flow 3 — Records Arrive & Customer Shipment

```
1. Event received: record.arrived_warehouse
   Payload: { production_job_id, campaign_id, qty_arrived }

2. Platform service — side effects
   a. Allocate inventory buckets:
      - 30 → presale_buyers
      - 50 → wholesale
      - 30 → artist
      - 30 → platform_store
   b. Update box_items status → READY for all campaign pre-orders
   c. Write Firestore /box_items/{customer_id} for each buyer
   d. Send "Your record is ready!" notification to each buyer

3. Customer sees "Ready in Warehouse" status in My Box (real-time)

4. Customer requests shipment
   POST /box/ship  (Platform service)
   Body: { box_item_ids: [...], destination: {...} }

5. Platform service — fulfillment.service
   a. Call Operations service: GET /shipping/calculate
      (sync HTTP — needs immediate response)
      Returns: { cost: 6.50, currency: EUR }
   b. Charge customer for shipping (new Stripe PaymentIntent)
   c. Create Shipment record (status: REQUESTED)
   d. Publish internal event to Operations service

6. Operations service — shipping.service
   a. Processes shipment request
   b. Updates Shipment → DISPATCHED
   c. Stores tracking number
   d. Publish event: shipment.dispatched

7. Platform service — receives shipment.dispatched
   a. Update box_items → SHIPPED
   b. Write Firestore projections
   c. Send shipping notification with tracking number
```

---

## 6. Tech Stack Reference

### Backend

| Layer | Technology | Justification |
|-------|-----------|---------------|
| API Framework | FastAPI (Python) | Async-native, Cloud Run optimised, auto OpenAPI docs |
| ORM | SQLAlchemy (async) | Async sessions, compatible with FastAPI |
| Migrations | Alembic | Standard with SQLAlchemy |
| Validation | Pydantic v2 | Native FastAPI integration |
| Task scheduling | Cloud Tasks | GCP-native, managed, reliable day-30 jobs |
| Async workers | Cloud Pub/Sub push | Serverless, no Celery/Redis needed on Cloud Run |
| Auth verification | firebase-admin SDK | JWT verification middleware |
| Payments | stripe SDK | Option A: immediate charge, batch refund on failure |

### Frontend

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Framework | Next.js 14+ (TypeScript) | SSR for SEO on campaign pages, App Router |
| Real-time | Firestore SDK | GCP-native, sub-second updates, no WebSocket infra |
| Auth | Firebase Auth SDK | Matches backend JWT verification |
| State | Zustand or React Query | Lightweight, pairs well with Firestore subscriptions |
| Styling | Tailwind CSS | Standard, fast, V0-compatible |

### GCP Services

| Service | Purpose |
|---------|---------|
| Cloud Run | Platform service + Operations service containers (auto-scaling) |
| Cloud SQL (PostgreSQL 15) | Relational source of truth |
| Firestore | Documents + real-time projections |
| Firebase Auth | JWT issuance, social login |
| Cloud Storage | WAV files, artwork, label images |
| Cloud Pub/Sub | Async event bus between services |
| Cloud Tasks | Scheduled campaign evaluation (day-30) |
| Secret Manager | Stripe keys, service credentials |
| Artifact Registry | Docker images for Cloud Run |
| VPC / Cloud NAT | Private connectivity, Cloud SQL access |

### Stripe Integration

| Pattern | Implementation |
|---------|---------------|
| Charge model | Option A: immediate charge on pre-order |
| Idempotency | `payment_events` table keyed on `stripe_event_id` |
| Webhooks | `POST /webhooks/stripe` — signature verified before any processing |
| Refunds | Batch job on campaign failure — checks `payment_events` before each refund |
| Shipping charges | Separate PaymentIntent at shipment request time |

### Key Architectural Rules (Summary)

1. **PostgreSQL is always the source of truth** for anything financial or transactional
2. **Firestore is a projection layer** — written by Platform service on state changes, never the origin of truth
3. **Modules never cross-query** each other's database tables
4. **All Pub/Sub publishes** go through `core/events.py` only
5. **All Stripe webhook processing** must check `payment_events` for idempotency first
6. **Campaign state transitions** are explicit events logged in `campaign_events` — never bare status field updates
7. **Points ledger is append-only** — balance is always computed as a sum, never stored directly
8. **Operations service is never called directly** by the frontend — only Platform service is public-facing

---

*This document is the reference contract for both backend (Cursor) and frontend (V0) development. API contracts and request/response schemas should be derived from Platform service's OpenAPI output at `/docs`.*
