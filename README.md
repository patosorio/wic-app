# Vinyl Platform

An independent vinyl crowdfunding platform. Artists upload releases, fans pre-order within 30-day campaigns, and physical vinyl production starts only when the minimum target is reached.

Built for independent artists who want to press vinyl without financial risk.

---

## How It Works

```
Artist uploads release
  → Campaign runs for 30 days
    → Fans pre-order at 19.99€
      → Target reached (30 pre-orders) → Production starts
      → Target not reached → Automatic refunds
```

Once funded, the release goes through a 7-stage production workflow — mastering, test pressing, artwork, final pressing — before records ship to buyers.

---

## Architecture

Two independent services, one shared backend core.

```
backend/
  core/             ← shared config, database, auth, events, firestore
  alembic/          ← single migration history
  platform/         ← public API (customers, artists)
  operations/       ← internal API (production, logistics)
  shared/           ← GCP clients, base models
frontend/
  web/              ← Next.js app
infra/              ← GCP configuration
docs/               ← architecture and product documentation
```

### Platform Service (public)
Handles everything customer and artist facing — release uploads, campaigns, pre-orders, My Box, shipping requests, points, discovery.

### Operations Service (internal)
Handles production workflow, inventory allocation, logistics, and shipping management. Never publicly accessible — only called by the Platform service via internal HTTP or Pub/Sub events.

### Communication
- **Pub/Sub push** for async triggers (campaign funded → start production job)
- **Internal HTTP** for synchronous queries (shipping cost calculation)
- **Firestore real-time SDK** for live frontend updates (campaign counters, production stages, box status)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11), async throughout |
| ORM | SQLAlchemy async + Alembic migrations |
| Primary DB | PostgreSQL via Cloud SQL |
| Real-time / Docs | Firestore |
| Auth | Firebase Auth (JWT on every protected route) |
| Payments | Stripe (immediate charge, batch refund on failure) |
| File storage | Cloud Storage (WAV, artwork, masters) |
| Async jobs | Cloud Pub/Sub push + Cloud Tasks |
| Frontend | Next.js 14 (TypeScript), Tailwind CSS |
| Platform | GCP (Cloud Run, Cloud SQL, Firestore, Cloud Storage) |

---

## User Roles

| Role | Access |
|------|--------|
| Customer | Browse, pre-order, My Box, request shipment |
| Artist | Customer + upload releases, campaign dashboard, approve masters and test pressings |
| Admin | Everything — including all production and logistics operations |

---

## Data Model

Two databases with clear ownership boundaries.

**PostgreSQL** owns everything financial and transactional — users, orders, payments, campaigns, inventory, points ledger. Source of truth, always.

**Firestore** owns real-time projections and document-style data — release metadata, live campaign counters, production stage updates, box item status, notifications. Read layer only, never source of truth.

---

## Campaign Economics

| Item | Value |
|------|-------|
| Minimum pre-orders to fund | 30 |
| Default pressing quantity | 150 copies |
| Pre-sale price | 19.99€ |
| Retail price (store) | 25.99€ |
| Campaign duration | 30 days |

Copy allocation per funded release:
```
30 copies → pre-sale buyers
50 copies → wholesale distribution
30 copies → artist
30 copies → platform store
```

---

## Production Workflow

7 stages tracked in the operations dashboard. Two require artist approval.

```
1. Mastering
2. Master approval          ← artist downloads and approves WAV master
3. Test pressing
4. Test pressing approval   ← artist approves physical test record
5. Artwork submission       ← artist uploads final print files (15 day deadline)
6. Final pressing
7. Warehouse arrival → shipping
```

---

## Local Development

**Prerequisites**
- Python 3.11+
- Docker (for local Postgres)
- Node.js 18+ (for frontend)

**Backend setup**
```bash
git clone https://github.com/your-org/vinyl-platform
cd vinyl-platform/backend

python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Start local Postgres
docker-compose up -d

# Copy and configure environment
cp .env.example .env
# Edit .env with your local values

# Run migrations
alembic upgrade head

# Start Platform service
uvicorn platform.main:app --reload --port 8000

# Start Operations service (new terminal)
uvicorn operations.main:app --reload --port 8001
```

**Frontend setup**
```bash
cd frontend/web
npm install
cp .env.local.example .env.local
# Edit .env.local with your Firebase and API values
npm run dev
```

**Environment variables**
```
# backend/.env
DATABASE_URL=postgresql+asyncpg://yourddbblink
FIREBASE_PROJECT_ID=your-project-id
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
GCP_PROJECT_ID=your-gcp-project
OPERATIONS_INTERNAL_URL=http://localhost:8001
PLATFORM_INTERNAL_URL=http://localhost:8000
```

---

## Documentation

Full documentation lives in `docs/`:

| Document | Contents |
|----------|----------|
| `ARCHITECTURE.md` | System architecture, service decomposition, data flows, event catalog |
| `PRODUCT_FLOWS.md` | Artist, customer, and admin flows — every screen state and action |
| `FRONTEND_CONTRACTS.md` | TypeScript types, API routes, Firestore collection paths |
| `BUILD_STEPS.md` | Step-by-step build guide and current progress |
| `V0_DESIGN_SYSTEM.md` | Frontend design language and component specs |

---

## Project Status

🚧 **In development** — Phase 0 environment setup

See `docs/BUILD_STEPS.md` for current progress and next steps.

---

