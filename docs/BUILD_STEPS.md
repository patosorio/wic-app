# Vinyl Platform — Build Steps

> This document is your single source of progress.
> At the start of every Cursor session, paste the current step.
> Mark each step [x] when complete and committed to git.
> Never start the next step until the current one is committed.

---

## How to Use This With Cursor

**Every Cursor session starts with this message:**

```
I am building a vinyl crowdfunding platform. 
Context documents: ARCHITECTURE.md, PRODUCT_FLOWS.md
Current step: [paste the step below]
Relevant rules: [paste the .mdc files relevant to this step]

Build only what is described in this step. 
Explain what you are about to do before writing any code.
Wait for my confirmation before proceeding.
```

**After each step:**
- Review all generated code line by line
- Run it locally and verify it works
- `git add . && git commit -m "step X — description"`
- Mark [x] in this document
- Move to next step

---

## Phase 0 — Environment Setup
> Do this manually. Do not use Cursor for Phase 0.

- [ ] **0.1 — Create monorepo structure**
  ```bash
  mkdir vinyl-platform && cd vinyl-platform
  mkdir -p backend/platform backend/operations backend/shared
  mkdir -p frontend infra docs .cursor/rules
  git init
  ```

- [ ] **0.2 — Copy all docs and cursor rules**
  ```
  docs/
    ARCHITECTURE.md
    PRODUCT_FLOWS.md
    FRONTEND_CONTRACTS.md
    V0_DESIGN_SYSTEM.md
    V0_PROMPT.md

  .cursor/rules/
    architecture.mdc
    backend.mdc
    database.mdc
    payments.mdc
    events.mdc
    frontend.mdc
    testing.mdc
    workflow.mdc
    python.mdc
  ```

- [ ] **0.3 — Create .gitignore**
  ```
  __pycache__/
  *.pyc
  .env
  .env.local
  venv/
  .venv/
  *.egg-info/
  dist/
  .DS_Store
  node_modules/
  .next/
  ```

- [ ] **0.4 — Set up Python environment (Platform service)**
  ```bash
  cd backend/platform
  python3.11 -m venv .venv
  source .venv/bin/activate
  ```

- [ ] **0.5 — Create pyproject.toml (Platform service)**
  Create `backend/platform/pyproject.toml`:
  ```toml
  [project]
  name = "vinyl-service-a"
  version = "0.1.0"
  requires-python = ">=3.11"

  dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "firebase-admin>=6.5.0",
    "google-cloud-pubsub>=2.21.0",
    "google-cloud-firestore>=2.16.0",
    "google-cloud-storage>=2.16.0",
    "google-cloud-tasks>=2.16.0",
    "stripe>=9.9.0",
    "httpx>=0.27.0",
    "python-multipart>=0.0.9",
  ]

  [project.optional-dependencies]
  dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
    "black>=24.4.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
  ]

  [tool.black]
  line-length = 88

  [tool.ruff]
  line-length = 88
  select = ["E","F","I","UP","B","SIM"]

  [tool.mypy]
  strict = true
  ignore_missing_imports = true

  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  ```

  ```bash
  pip install -e ".[dev]"
  ```

- [ ] **0.6 — Create docker-compose for local dev**
  Create `docker-compose.yml` in root:
  ```yaml
  version: "3.9"
  services:
    postgres:
      image: postgres:15
      environment:
        POSTGRES_USER: vinyl
        POSTGRES_PASSWORD: vinyl
        POSTGRES_DB: vinyl_dev
      ports:
        - "5432:5432"
      volumes:
        - postgres_data:/var/lib/postgresql/data

  volumes:
    postgres_data:
  ```

  ```bash
  docker-compose up -d
  # Verify: psql postgresql://vinyl:vinyl@localhost:5432/vinyl_dev
  ```

- [ ] **0.7 — Create .env file (Platform service)**
  Create `backend/platform/.env`:
  ```
  DATABASE_URL=postgresql+asyncpg://vinyl:vinyl@localhost:5432/vinyl_dev
  FIREBASE_PROJECT_ID=your-project-id
  STRIPE_SECRET_KEY=sk_test_...
  STRIPE_WEBHOOK_SECRET=whsec_...
  GCP_PROJECT_ID=your-gcp-project
  SERVICE_B_INTERNAL_URL=http://localhost:8001
  ```

- [ ] **0.8 — Initial git commit**
  ```bash
  git add .
  git commit -m "step 0 — environment setup"
  ```

---

## Phase 1 — Platform service Foundation
> Start Cursor here. Use: backend.mdc + architecture.mdc + python.mdc

- [ ] **1.1 — Folder scaffold (Platform service)**

  Ask Cursor to create the full empty folder structure:
  ```
  backend/
    alembic/                    ← shared by platform + operations
      env.py
      versions/
    alembic.ini
    core/                       ← shared by platform + operations
      config.py
      database.py
      firebase_auth.py
      events.py
      firestore.py
      exceptions.py
    platform/
      main.py
      auth/
        router.py
        service.py
        models.py
      catalog/
        router.py
        service.py
        models.py
        storage.py
      campaigns/
        router.py
        service.py
        models.py
        state_machine.py
      commerce/
        router.py
        service.py
        models.py
        stripe_client.py
      fulfillment/
        router.py
        service.py
        models.py
      discovery/
        router.py
        service.py
      engagement/
        router.py
        service.py
        models.py
        ledger.py
  ```
  All files empty with correct `__init__.py` files.
  Verify structure looks right. Commit.

- [ ] **1.2 — Config and settings**

  Ask Cursor to build `core/config.py` with pydantic-settings.
  Fields: DATABASE_URL, FIREBASE_PROJECT_ID, STRIPE_SECRET_KEY,
  STRIPE_WEBHOOK_SECRET, GCP_PROJECT_ID, SERVICE_B_INTERNAL_URL.
  Verify `.env` loads correctly. Commit.

- [ ] **1.3 — Database connection**

  Ask Cursor to build `core/database.py`.
  Async SQLAlchemy engine + session factory + `get_db` dependency.
  Test connection to local Postgres. Commit.

- [ ] **1.4 — Base FastAPI app**

  Ask Cursor to build `main.py`.
  FastAPI instance, CORS, health check route `GET /health → {"status": "ok"}`.
  Run with uvicorn locally. Verify `/health` responds. Commit.

- [ ] **1.5 — Firebase Auth middleware**

  Ask Cursor to build `core/firebase_auth.py`.
  `verify_firebase_jwt` dependency that validates Bearer token.
  `require_role(role)` dependency for role enforcement.
  `FirebaseUser` model with uid, email, role.
  Do not test with real Firebase yet — add a dev bypass for local. Commit.

- [ ] **1.6 — Custom exceptions**

  Ask Cursor to build `core/exceptions.py` and register handlers in `main.py`.
  Exceptions: CampaignNotActiveError, InsufficientCapacityError,
  InvalidStateTransitionError, ArtworkDeadlinePassedError. Commit.

- [ ] **1.7 — Alembic setup**

  Ask Cursor to configure Alembic.
  `alembic.ini` pointing to DATABASE_URL from settings.
  `alembic/env.py` importing Base from models.
  Verify `alembic history` runs without error. Commit.

---

## Phase 2 — Auth Module
> Use: backend.mdc + database.mdc + python.mdc

- [ ] **2.1 — User model**

  Ask Cursor to build `auth/models.py`.
  User: id (UUID), firebase_uid (unique), email, role (enum), created_at.
  UserRole enum: customer, artist, admin.
  No logistics role at MVP — admin handles all production and logistics operations.
  Default role on signup: customer. Artist role granted by admin.

  Role permissions (artist inherits customer surface, admin inherits everything):
  ```python
  ROLE_PERMISSIONS = {
      UserRole.CUSTOMER: ["customer"],
      UserRole.ARTIST:   ["customer", "artist"],
      UserRole.ADMIN:    ["customer", "artist", "admin"],
  }
  ```
  Commit.

- [ ] **2.2 — Auth migration**

  Ask Cursor to generate Alembic migration for User table.
  Review the migration file before running.
  `alembic upgrade head`. Verify table exists in Postgres. Commit.

- [ ] **2.3 — Auth service**

  Ask Cursor to build `auth/service.py`.
  Functions: get_or_create_user(firebase_uid, email, role, db),
  get_user(user_id, db), get_user_by_firebase_uid(firebase_uid, db). Commit.

- [ ] **2.4 — Auth router**

  Ask Cursor to build `auth/router.py`.
  POST /auth/register — creates user record after Firebase signup.
  GET  /auth/me — returns current user from JWT.
  Register router in main.py. Test with httpx. Commit.

---

## Phase 3 — Catalog Module
> Use: backend.mdc + database.mdc + python.mdc

- [ ] **3.1 — Release model (Postgres)**

  Ask Cursor to build `catalog/models.py`.
  Release: id, artist_id (FK users), firestore_doc_id, status (enum),
  format (enum: 10in/12in/2x12in), created_at. Commit.

- [ ] **3.2 — Release migration**

  Generate and review migration. Run it. Verify table. Commit.

- [ ] **3.3 — Firestore release document**

  Ask Cursor to define the ReleaseDoc Pydantic model in `catalog/models.py`.
  Fields from FRONTEND_CONTRACTS.md: title, artist_name, catalog_number,
  format, audio_urls, artwork_urls, label_color, tracklist, description, tags.
  This is the Firestore document shape — not a DB table. Commit.

- [ ] **3.4 — Cloud Storage helper**

  Ask Cursor to build `catalog/storage.py`.
  Functions: upload_audio(file, release_id, side) → url,
  upload_artwork(file, release_id, type) → url.
  Use signed URLs for private files. Commit.

- [ ] **3.5 — Catalog service**

  Ask Cursor to build `catalog/service.py`.
  Functions: create_release(data, artist_id, db),
  get_release(release_id, db), list_releases(filters, db).
  Write Firestore doc on create via core/firestore.py. Commit.

- [ ] **3.6 — Catalog router**

  Ask Cursor to build `catalog/router.py`.
  POST /releases/ (artist only)
  GET  /releases/
  GET  /releases/{id}
  Register in main.py. Test all routes. Commit.

---

## Phase 4 — Campaign Module
> Use: backend.mdc + database.mdc + python.mdc

- [ ] **4.1 — Campaign models**

  Ask Cursor to build `campaigns/models.py`.
  Campaign: id, release_id (FK), status (enum), target (default 30),
  current_count (default 0), presale_price, retail_price, starts_at, ends_at.
  CampaignEvent: id, campaign_id (FK), from_status, to_status,
  triggered_by, occurred_at. Commit.

- [ ] **4.2 — Campaign migration**

  Generate, review, run. Verify both tables. Commit.

- [ ] **4.3 — Campaign state machine**

  Ask Cursor to build `campaigns/state_machine.py`.
  Valid transitions only (see ARCHITECTURE.md section 5 state machine reference).
  Every transition logs a CampaignEvent. Raises InvalidStateTransitionError
  for illegal transitions. Unit test all transitions. Commit.

- [ ] **4.4 — Firestore campaign projection**

  Ask Cursor to build the projection writer in `core/firestore.py`.
  Function: write_campaign_projection(campaign_id, data).
  Fields: status, current_count, target, percentage, days_remaining,
  presale_price, ends_at. Commit.

- [ ] **4.5 — Campaign service**

  Ask Cursor to build `campaigns/service.py`.
  Functions: create_campaign(release_id, db),
  get_campaign(campaign_id, db),
  increment_counter(campaign_id, db) — checks if target reached → triggers funded flow,
  list_active_campaigns(db), list_almost_funded(db), list_trending(db). Commit.

- [ ] **4.6 — Campaign router**

  GET  /campaigns/
  GET  /campaigns/{id}
  GET  /campaigns/trending/
  GET  /campaigns/almost-funded/
  Register in main.py. Test. Commit.

- [ ] **4.7 — Day-30 Cloud Tasks job**

  Ask Cursor to build the campaign evaluation endpoint.
  POST /jobs/evaluate-campaign/{id} — internal endpoint triggered by Cloud Tasks.
  Checks campaign status, transitions ACTIVE → FAILED if target not met.
  Publishes campaign.failed event. Commit.

---

## Phase 5 — Commerce Module (Stripe)
> Use: backend.mdc + database.mdc + payments.mdc + python.mdc

- [ ] **5.1 — Order and PaymentEvent models**

  Ask Cursor to build `commerce/models.py`.
  Order: id, campaign_id (FK), customer_id (FK), status (enum),
  amount (Decimal), stripe_payment_intent_id (unique), created_at.
  PaymentEvent: id, order_id (FK), stripe_event_id (unique, idempotency key),
  event_type, payload (JSONB), processed_at.
  OrderStatus enum: pending_campaign, in_production, refunded, completed. Commit.

- [ ] **5.2 — Commerce migration**

  Generate, review, run. Verify tables and JSONB column. Commit.

- [ ] **5.3 — Stripe client wrapper**

  Ask Cursor to build `commerce/stripe_client.py`.
  Functions: create_payment_intent(amount, customer_id) → PaymentIntent,
  issue_refund(payment_intent_id) → Refund.
  All amounts in Decimal, convert to cents internally.
  Never call stripe SDK outside this file. Commit.

- [ ] **5.4 — Stripe webhook handler**

  Ask Cursor to build the webhook handler in `commerce/service.py`.
  Signature verification first, always.
  Idempotency check against PaymentEvent table, always.
  Insert PaymentEvent before processing, always.
  Handle: payment_intent.succeeded, payment_intent.payment_failed.
  Unit test idempotency — same event twice must not double-process. Commit.

- [ ] **5.5 — Order service**

  Ask Cursor to build order creation in `commerce/service.py`.
  create_order(campaign_id, customer_id, db):
    - Verify campaign is ACTIVE
    - Verify capacity not exceeded
    - Create Stripe PaymentIntent
    - Create Order record
    - Return order
  batch_refund_campaign(campaign_id, db) — resumable, idempotent. Commit.

- [ ] **5.6 — Commerce router**

  POST /orders/ — create pre-order
  POST /webhooks/stripe — Stripe webhook (no auth, signature verified internally)
  GET  /orders/{id}
  Register in main.py. Test order creation end to end with Stripe test mode. Commit.

---

## Phase 6 — Fulfillment Module
> Use: backend.mdc + database.mdc + python.mdc

- [ ] **6.1 — Fulfillment models**

  Ask Cursor to build `fulfillment/models.py`.
  Box: id, customer_id (FK).
  BoxItem: id, box_id (FK), order_id (FK), status (enum), updated_at.
  Shipment: id, box_id (FK), status (enum), tracking_number,
  shipping_cost (Decimal), destination (JSONB), requested_at.
  BoxItemStatus enum: pre_order, in_production, ready, in_box, shipped, delivered.
  ShipmentStatus enum: requested, processing, dispatched, delivered. Commit.

- [ ] **6.2 — Fulfillment migration**

  Generate, review, run. Commit.

- [ ] **6.3 — Fulfillment service**

  Ask Cursor to build `fulfillment/service.py`.
  Functions: get_or_create_box(customer_id, db),
  add_item_to_box(order_id, customer_id, db),
  get_box(customer_id, db),
  request_shipment(box_item_ids, destination, customer_id, db),
  update_box_items_status(campaign_id, new_status, db).
  Firestore projection write on every status change. Commit.

- [ ] **6.4 — Fulfillment router**

  GET  /box/
  POST /box/ship
  GET  /shipments/{id}
  Register in main.py. Test. Commit.

---

## Phase 7 — Engagement Module
> Use: backend.mdc + database.mdc + python.mdc

- [ ] **7.1 — Points ledger model**

  Ask Cursor to build `engagement/models.py`.
  PointsLedger: id, user_id (FK), delta (integer), action (varchar),
  reference_id (UUID), occurred_at.
  Append-only. No update operations ever. Commit.

- [ ] **7.2 — Engagement migration**

  Generate, review, run. Commit.

- [ ] **7.3 — Ledger service**

  Ask Cursor to build `engagement/ledger.py`.
  earn_points(user_id, action, reference_id, db) — appends row, never updates.
  get_balance(user_id, db) → sum of all deltas.
  get_level(balance) → supporter level string.
  Unit test: verify balance is always a sum, never stored. Commit.

- [ ] **7.4 — Notification service**

  Ask Cursor to build notification writing in `engagement/service.py`.
  send_notification(user_id, type, message) — writes to Firestore only.
  Reference notification types from PRODUCT_FLOWS.md section 4. Commit.

- [ ] **7.5 — Engagement router**

  GET /points/ — returns PointsSummary
  Register in main.py. Test. Commit.

---

## Phase 8 — Pub/Sub Events (Platform service side)
> Use: events.mdc + backend.mdc + python.mdc

- [ ] **8.1 — Pub/Sub publisher**

  Ask Cursor to build `core/events.py`.
  One publish function per event topic from the event catalog.
  All use the standard EventEnvelope.
  Topics: campaign.funded, campaign.failed, campaign.presale_incremented,
  record.arrived_warehouse, shipment.dispatched,
  payment.refund_initiated, payment.refund_completed. Commit.

- [ ] **8.2 — Wire events into services**

  Ask Cursor to add event publishes into the relevant service functions:
  - campaign funded → publish campaign.funded in campaigns/service.py
  - campaign failed → publish campaign.failed
  - pre-order confirmed → publish campaign.presale_incremented
  Do one at a time. Review each. Commit after all three. Commit.

---

## Phase 9 — Operations service Foundation
> New service. Mirror Phase 1 for Operations service. Use: backend.mdc + architecture.mdc

- [ ] **9.1 — Operations service scaffold**

  ```
  backend/operations/
    main.py
    core/
      config.py
      database.py
      events.py          ← Pub/Sub subscriptions
      pubsub_auth.py     ← JWT verification for push endpoints
    production/
      router.py
      service.py
      models.py
      state_machine.py
    logistics/
      router.py
      service.py
    inventory/
      router.py
      service.py
      models.py
    shipping/
      router.py
      service.py
      calculator.py
    alembic/
  ```
  Commit.

- [ ] **9.2 — Operations service config, database, main.py**

  Same pattern as Platform service.
  Runs on port 8001 locally.
  Health check at GET /health. Commit.

- [ ] **9.3 — Pub/Sub JWT verification**

  Ask Cursor to build `core/pubsub_auth.py`.
  Middleware that verifies GCP-signed JWT on all /internal/events/* routes.
  Dev bypass for local testing. Commit.

---

## Phase 10 — Production Workflow (Operations service)
> Use: backend.mdc + database.mdc + events.mdc + python.mdc

- [ ] **10.1 — Production models**

  ProductionJob: id, campaign_id, release_id, status, pressing_qty,
  blank_labels (boolean, default false), created_at.
  ProductionStage: id, job_id (FK), stage (enum 7 stages), status (enum),
  started_at, completed_at.
  ProductionApproval: id, stage_id (FK), approved_by, approved_at, notes.
  Stage enum: mastering, master_approval, test_pressing,
  test_pressing_approval, artwork_submission, final_pressing,
  warehouse_arrival. Commit.

- [ ] **10.2 — Production migration**

  Generate, review, run. Commit.

- [ ] **10.3 — Production state machine**

  Ask Cursor to build `production/state_machine.py`.
  Valid stage progressions. Artist approval gates.
  Artwork 15-day timeout logic. Raises InvalidStateTransitionError. Commit.

- [ ] **10.4 — Production service**

  create_job(campaign_id, release_id, db),
  advance_stage(job_id, db),
  approve_stage(job_id, stage, approved_by, notes, db),
  reject_stage(job_id, stage, feedback, db),
  handle_artwork_timeout(job_id, db). Commit.

- [ ] **10.5 — Pub/Sub event consumer: campaign.funded**

  Ask Cursor to build the push endpoint in `core/events.py`:
  POST /internal/events/campaign-funded
  Verifies Pub/Sub JWT, parses envelope, calls production_service.create_job.
  Idempotent — check for existing job first. Commit.

- [ ] **10.6 — Production router (internal)**

  POST /production/{job_id}/advance   (logistics)
  POST /production/{job_id}/approve   (artist)
  POST /production/{job_id}/reject    (artist)
  GET  /production/{job_id}
  Register in main.py. Commit.

---

## Phase 11 — Inventory & Shipping (Operations service)
> Use: backend.mdc + database.mdc + python.mdc

- [ ] **11.1 — Inventory models and migration**

  InventoryLot: id, production_job_id (FK), total_qty, created_at.
  InventoryAllocation: id, lot_id (FK), bucket (enum), quantity, allocated_at.
  Bucket enum: presale_buyers, wholesale, artist, platform_store. Commit.

- [ ] **11.2 — Inventory service**

  allocate_inventory(job_id, db) — splits 150 copies into 4 buckets.
  Default split from ARCHITECTURE.md: 30/50/30/30. Commit.

- [ ] **11.3 — Shipping calculator**

  Ask Cursor to build `shipping/calculator.py`.
  calculate_cost(destination, item_count) → Decimal.
  Start with simple flat rates by country. Can be made complex later. Commit.

- [ ] **11.4 — Shipping router**

  GET /shipping/calculate — sync query called by Platform service. Commit.

- [ ] **11.5 — Pub/Sub consumer: record.arrived_warehouse**

  POST /internal/events/record-arrived
  Calls allocate_inventory, then publishes back to Platform service via HTTP. Commit.

---

## Phase 12 — Discovery Module (Platform service)
> Use: backend.mdc + python.mdc

- [ ] **12.1 — Discovery service**

  get_trending(db), get_almost_funded(db), get_new_releases(db).
  almost_funded = campaigns with percentage >= 70, sorted by closest to target. Commit.

- [ ] **12.2 — Homepage router**

  GET /homepage/ — returns all four sections in one response.
  Minimise DB queries — use a single efficient query per section. Commit.

---

## Phase 13 — Integration Testing
> Use: testing.mdc

- [ ] **13.1 — Test the pre-order flow end to end**

  Manually test: upload release → campaign live → pre-order → counter increments →
  Firestore updates → My Box shows item.
  Fix any issues found. Commit.

- [ ] **13.2 — Test the campaign funding flow**

  Manually push campaign to 30 orders → verify funded transition →
  Operations service receives event → ProductionJob created. Commit.

- [ ] **13.3 — Test the refund flow**

  Manually trigger campaign failure → batch refund runs →
  idempotency check works → orders marked refunded. Commit.

- [ ] **13.4 — Write unit tests for state machines**

  Campaign state machine: all valid and invalid transitions.
  Production state machine: all stage progressions and approval gates.
  Points ledger: verify balance is always a sum. Commit.

---

## Phase 14 — Frontend Integration
> Now bring in V0 output. Use: frontend.mdc

- [ ] **14.1 — Scaffold Next.js app**
  ```bash
  cd frontend
  npx create-next-app@latest web --typescript --tailwind --app
  cd web
  npm install firebase
  ```

- [ ] **14.2 — Set up Firebase and Auth**

  `lib/firebase.ts` — Firebase app init.
  `lib/auth.ts` — getAuthToken(), useAuth() hook. Commit.

- [ ] **14.3 — Set up API client layer**

  `lib/api/` — one file per module from FRONTEND_CONTRACTS.md.
  All placeholder functions pointing to NEXT_PUBLIC_API_URL. Commit.

- [ ] **14.4 — Set up Firestore hooks**

  `hooks/useCampaignRealtime.ts`
  `hooks/useBoxRealtime.ts`
  `hooks/useProductionStages.ts`
  `hooks/useNotifications.ts`
  All pointing to correct Firestore collection paths. Commit.

- [ ] **14.5 — Paste V0 output, page by page**

  Paste one page at a time from V0.
  Verify field names match FRONTEND_CONTRACTS.md.
  Fix any naming mismatches in Cursor. Commit per page.

- [ ] **14.6 — Wire each page to real API**

  Replace placeholder functions with real endpoint calls one page at a time.
  Start with: homepage → campaign page → My Box → artist dashboard. Commit per page.

---

## Phase 15 — Pre-launch Checklist
> Before any real traffic.

- [ ] Remove all dev bypasses (Firebase auth bypass, local-only shortcuts)
- [ ] Verify Stripe webhook signature check is active in production
- [ ] Verify all secrets are in Secret Manager, not in .env
- [ ] Verify Operations service is not publicly accessible (internal Cloud Run only)
- [ ] Set up Cloud Tasks queue for day-30 campaign jobs in GCP
- [ ] Configure Pub/Sub topics and push subscriptions in GCP
- [ ] Run full end-to-end test in staging environment
- [ ] Verify refund batch job is idempotent (run it twice, check no double refunds)
- [ ] Set up error alerting (Cloud Monitoring or Sentry)
- [ ] git tag v0.1.0

---

## Quick Reference — Cursor Session Template

Copy this at the start of every Cursor session:

```
Project: Vinyl crowdfunding platform
Docs: See docs/ARCHITECTURE.md and docs/PRODUCT_FLOWS.md

Current step: [STEP NUMBER AND TITLE]
[PASTE STEP CONTENT HERE]

Rules in effect:
- One thing at a time — build only what this step describes
- Explain before you generate — tell me what you will build and wait for my ok
- After building — tell me what to review and what comes next (but don't build it)
- If anything is ambiguous — ask me, don't assume
```
