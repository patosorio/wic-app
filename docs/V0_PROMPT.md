# V0 Master Prompt — Vinyl Platform Frontend

---

## How to use this prompt

Paste the block below into V0. Also attach these three files:
- `ARCHITECTURE.md` — domain understanding
- `V0_DESIGN_SYSTEM.md` — visual language
- `FRONTEND_CONTRACTS.md` — exact TypeScript types and API routes

Then use the per-screen prompts at the bottom for each individual page.

---

## Master Prompt (paste this first)

```
I am building a vinyl crowdfunding platform — think a mix of Bandcamp, Qrates, and Kickstarter for independent vinyl releases. Artists upload releases, fans pre-order within 30-day campaigns, and physical vinyl production starts only when the minimum target of 30 pre-orders is reached.

I have attached three reference documents:
1. ARCHITECTURE.md — explains the full system, domain entities, and data flows
2. V0_DESIGN_SYSTEM.md — defines the exact visual language to follow
3. FRONTEND_CONTRACTS.md — defines the exact TypeScript types, field names, API routes, and Firestore collections

Rules you must follow for every screen you generate:

DESIGN:
- White background (#FFFFFF) always, no exceptions
- Primary font: Inter. Display/titles font: Playfair Display
- No color accents — black and grey only
- Thin borders (#E5E5E5), no shadows, no rounded corners beyond 2px
- No gradient backgrounds or buttons
- No color-filled badges — borders only
- Generous white space — minimal, editorial aesthetic

CODE STRUCTURE:
- Next.js 14 App Router with TypeScript strict mode
- Each page is a Server Component by default
- Any component that uses Firestore real-time subscriptions is a Client Component with "use client"
- All API calls go through a typed client in /lib/api/ — never fetch() directly in components
- All Firestore subscriptions go through custom hooks in /hooks/ — never onSnapshot() directly in components
- Auth token always retrieved via getAuthToken() from /lib/auth.ts
- All TypeScript types come from /types/api.ts — use exact field names from FRONTEND_CONTRACTS.md
- Environment variables: NEXT_PUBLIC_API_URL for backend, NEXT_PUBLIC_FIREBASE_PROJECT_ID for Firebase

API INTEGRATION:
- All backend calls are placeholder functions in /lib/api/ — use the exact route paths from FRONTEND_CONTRACTS.md
- Firestore subscriptions use the exact collection paths from FRONTEND_CONTRACTS.md
- Do not hardcode any URLs — always use process.env.NEXT_PUBLIC_API_URL
- Every API function must accept and forward the Firebase auth token

SEPARATION OF CONCERNS:
- /lib/api/        → typed async functions that call Service A endpoints
- /lib/firebase.ts → Firebase app initialisation only
- /lib/auth.ts     → getAuthToken() and auth helpers only
- /hooks/          → custom React hooks for Firestore real-time subscriptions
- /types/api.ts    → all TypeScript interfaces (from FRONTEND_CONTRACTS.md)
- /components/     → reusable UI components, no data fetching
- /app/            → page components, data fetching at page level

Generate all components with placeholder data so the UI is fully visible and interactive. The API and Firestore connections will be wired to the real backend later — the structure just needs to be in place.
```

---

## Per-Screen Prompts

Use each prompt individually after the master prompt is established.

---

### 1. Homepage `/`

```
Generate the homepage with four sections in this order:
1. "Trending Releases" — horizontal scroll of release cards, mock 4 campaigns
2. "Almost Funded" — grid of campaigns close to target (mock: 25/30, 27/30, 28/30)
3. "Recommended for You" — grid of release cards
4. "New Releases" — grid of release cards

Use the CampaignProjection type for real-time data.
The progress bar in each card must use the CampaignProjection fields:
current_count, target, percentage, days_remaining.
Campaign status badge uses the status field.
Include the sticky top navigation with: wordmark left, nav center, icons right.
Mock artist names and release titles using real-sounding vinyl release names.
```

---

### 2. Campaign Page `/releases/[id]`

```
Generate the campaign page for a vinyl release.
Two-column layout: artwork left (60%), details right (40%).
Right column must include in this order:
  - artist_name (Inter 11px uppercase grey)
  - title (Playfair Display 36px)
  - catalog_number (Inter 11px muted)
  - format badge (format field: "12in")
  - thin divider
  - live progress bar (uses CampaignProjection: current_count, target, percentage, days_remaining)
  - presale_price
  - Pre-Order button (primary, full width)
  - campaign ends_at date
  - thin divider
  - description / artist bio

The progress bar component must be a Client Component using useCampaignRealtime(campaignId) hook.
The hook subscribes to Firestore /campaigns/{campaign_id} (CampaignProjection type).
The rest of the page is a Server Component.

Mock data: artist "Burial", title "Antidawn EP", catalog "HYP013", format "12in",
current_count 22, target 30, percentage 73, days_remaining 8, presale_price 19.99.
```

---

### 3. Artist Profile `/artists/[id]`

```
Generate the artist profile page.
Top section: artist name (Playfair Display large), bio, stats row.
Below: grid of their releases using the Release and CampaignProjection types.
Each card shows: artwork, title, catalog_number, format, campaign status.
Use ReleaseDoc fields for display: title, artist_name, artwork_urls.cover, description.
```

---

### 4. Platform Store `/store`

```
Generate the store page.
Header: "Store" in Playfair Display.
Subheader: "Limited pressings from funded campaigns."
Grid of release cards using retail_price (25.99) instead of presale_price.
Each card shows stock availability as a small text label.
Add to cart button uses the secondary/ghost button style.
```

---

### 5. My Box `/box`

```
Generate the My Box page. This is the customer's personal record storage.
Header: "My Box" Playfair Display 32px.
Subheader: "{n} records" Inter 13px grey.

Each box item row (BoxItemProjection type) shows:
  - artwork_url thumbnail (48x48px square)
  - release_title (Inter 14px 500)
  - artist_name (Inter 12px grey)
  - status badge (text only, colour from design system based on status value)
  - right side: "Request Shipment" button if status === "ready", otherwise status text

Status colour mapping:
  pre_order → #A0A0A0
  in_production → #6B6B6B
  ready → #0A0A0A bold
  shipped → #27AE60
  delivered → #A0A0A0

The entire box list must be a Client Component using useBoxRealtime(customerId) hook.
The hook subscribes to Firestore /box_items/{customer_id} (BoxProjection type).

Include a shipping address modal triggered by "Request Shipment".
The modal form uses the ShippingAddress type fields exactly.
Below the form, show a shipping cost placeholder fetched from GET /shipping/calculate.
```

---

### 6. Artist Dashboard `/dashboard`

```
Generate the artist dashboard.
Left sidebar navigation: Overview, My Releases, Upload Release, Production.
Main area defaults to Overview tab.

Overview tab shows:
  - Stats row: total campaigns, funded campaigns, total pre-orders, total earnings
  - Active campaigns list with progress bars (CampaignProjection type)

Production tab shows the 9-stage production timeline (ProductionStageProjection type).
Stages: mastering, master_approval, lacquer_cutting, galvanic, test_pressing,
test_pressing_approval, final_pressing, warehouse_arrival, shipping.
Display as horizontal dot timeline.
Stages requiring approval (master_approval, test_pressing_approval) show an "Approve" button
when status === "awaiting_approval".
The timeline must be a Client Component using useProductionStages(jobId) hook.
The hook subscribes to Firestore /production_stages/{job_id} (ProductionStageProjection type).
```

---

### 7. Upload Release `/dashboard/upload`

```
Generate the multi-step upload form for artists. Three steps:

Step 1 — Release Info:
  Fields matching CreateReleaseRequest + ReleaseDoc:
  title, artist_name, catalog_number, format (select: 10in / 12in / 2x12in), description

Step 2 — Audio:
  Upload WAV for side_a, upload WAV for side_b.
  Show file name and duration after upload.
  Max 15 minutes per side — validate and show error if exceeded.

Step 3 — Artwork:
  Upload cover artwork (square).
  Upload label artwork side A.
  Upload label artwork side B.
  label_color select: black / white.

Progress indicator at top showing current step.
Each step has Back and Continue buttons.
Final step has Submit button (primary).
All field names must match ReleaseDoc and Release types exactly.
```

---

### 8. Auth Page `/auth`

```
Generate the auth page. Minimal — centered card on white background.
Platform wordmark at top (Playfair Display italic).
Two tabs: "Sign In" and "Create Account".

Sign In: email input, password input, Sign In button (primary), Google sign-in button (ghost).
Create Account: email input, password input, confirm password, full name, 
role select (customer / artist), Create Account button (primary).

No decorative elements. No background patterns. Just the form.
Error messages use Inter 11px #C0392B below the relevant field.
```

---

### 9. Notifications Dropdown (component)

```
Generate a notifications dropdown component for the top navigation.
Triggered by a bell icon in the nav bar. Shows unread count badge.
Dropdown lists Notification items from Firestore /notifications/{user_id}/items.
Each item shows: type icon (minimal), message text, created_at relative time.
Unread items have a subtle left border in #0A0A0A.
Mark all as read button at top of dropdown.
Must be a Client Component using useNotifications(userId) hook.
The hook subscribes to Firestore /notifications/{user_id}/items (Notification type).
```

---

## Folder Structure V0 Should Produce

```
frontend/
├── app/
│   ├── page.tsx                    ← Homepage
│   ├── releases/[id]/page.tsx      ← Campaign page
│   ├── artists/[id]/page.tsx       ← Artist profile
│   ├── store/page.tsx              ← Platform store
│   ├── box/page.tsx                ← My Box
│   ├── dashboard/page.tsx          ← Artist dashboard
│   ├── dashboard/upload/page.tsx   ← Upload release
│   └── auth/page.tsx               ← Login / signup
├── components/
│   ├── nav/                        ← TopNav, NotificationsDropdown
│   ├── campaigns/                  ← CampaignCard, ProgressBar, CampaignDetail
│   ├── releases/                   ← ReleaseCard, ReleaseGrid
│   ├── box/                        ← BoxItem, ShipmentModal
│   ├── production/                 ← StageTimeline, ApprovalButton
│   └── ui/                         ← Button, Input, Badge, Divider, Modal
├── hooks/
│   ├── useCampaignRealtime.ts      ← Firestore /campaigns/{id}
│   ├── useBoxRealtime.ts           ← Firestore /box_items/{customer_id}
│   ├── useProductionStages.ts      ← Firestore /production_stages/{job_id}
│   └── useNotifications.ts         ← Firestore /notifications/{user_id}/items
├── lib/
│   ├── api/
│   │   ├── campaigns.ts            ← getCampaign, getCampaigns, getTrending
│   │   ├── orders.ts               ← createOrder
│   │   ├── releases.ts             ← getRelease, getReleases, createRelease
│   │   ├── box.ts                  ← getBox, requestShipment
│   │   ├── shipping.ts             ← calculateShipping
│   │   ├── points.ts               ← getPoints
│   │   └── store.ts                ← getStoreReleases
│   ├── firebase.ts                 ← Firebase app init
│   └── auth.ts                     ← getAuthToken, useAuth
└── types/
    └── api.ts                      ← All interfaces from FRONTEND_CONTRACTS.md
```
