# Frontend Data Contracts

> These are the exact TypeScript types that match the backend API responses.
> V0 must use these field names exactly when building components.
> All data comes from Platform service (Platform API) unless noted.
> Real-time fields come from Firestore and are marked [REALTIME].

---

## Auth

```typescript
// Firebase Auth user — available via useAuthState()
interface FirebaseUser {
  uid: string
  email: string
  displayName: string | null
  photoURL: string | null
}

// Role attached to Firebase custom claims
type UserRole = "customer" | "artist" | "logistics" | "admin"
```

---

## Releases

```typescript
// POST /releases/  GET /releases/{id}
interface Release {
  id: string
  artist_id: string
  status: "draft" | "active" | "archived"
  format: "10in" | "12in" | "2x12in"
  created_at: string
}

// Firestore /releases/{id}  [REALTIME]
interface ReleaseDoc {
  title: string
  artist_name: string
  catalog_number: string
  format: "10in" | "12in" | "2x12in"
  audio_urls: {
    side_a: string
    side_b: string
  }
  artwork_urls: {
    cover: string
    label_a: string
    label_b: string
  }
  label_color: "black" | "white" | "custom"
  tracklist: TrackItem[]
  description: string
  tags: string[]
}

interface TrackItem {
  side: "A" | "B"
  position: number
  title: string
  duration_seconds: number
}
```

---

## Campaigns

```typescript
// GET /campaigns/{id}  GET /campaigns/  
interface Campaign {
  id: string
  release_id: string
  status: "draft" | "active" | "funded" | "failed" | "refunding" | "closed"
  target: number              // always 30
  current_count: number
  presale_price: number       // 19.99
  retail_price: number        // 25.99
  starts_at: string
  ends_at: string
}

// Firestore /campaigns/{id}  [REALTIME]
// Subscribe to this for live progress bar updates
interface CampaignProjection {
  release_id: string
  status: string
  current_count: number       // live counter
  target: number
  percentage: number          // 0-100
  days_remaining: number
  presale_price: number
  ends_at: string
}
```

---

## Orders

```typescript
// POST /orders/
interface CreateOrderRequest {
  campaign_id: string
}

// Response
interface OrderResponse {
  id: string
  campaign_id: string
  status: "pending_campaign" | "in_production" | "refunded" | "completed"
  amount: number
  created_at: string
}
```

---

## My Box

```typescript
// GET /box/
interface Box {
  id: string
  customer_id: string
  items: BoxItem[]
}

interface BoxItem {
  id: string
  order_id: string
  status: "pre_order" | "in_production" | "ready" | "in_box" | "shipped" | "delivered"
  updated_at: string
}

// Firestore /box_items/{customer_id}  [REALTIME]
// Subscribe to this for live box status updates
interface BoxProjection {
  items: BoxItemProjection[]
}

interface BoxItemProjection {
  order_id: string
  release_title: string
  artist_name: string
  artwork_url: string
  status: "pre_order" | "in_production" | "ready" | "in_box" | "shipped" | "delivered"
}

// POST /box/ship
interface ShipmentRequest {
  box_item_ids: string[]
  destination: ShippingAddress
}

interface ShippingAddress {
  full_name: string
  line1: string
  line2?: string
  city: string
  postal_code: string
  country: string             // ISO 3166-1 alpha-2
}

// GET /shipping/calculate — returns cost before confirming
interface ShippingCostResponse {
  cost: number
  currency: string            // "EUR"
  estimated_days: number
}
```

---

## Shipments

```typescript
interface Shipment {
  id: string
  status: "requested" | "processing" | "dispatched" | "delivered"
  tracking_number: string | null
  shipping_cost: number
  destination: ShippingAddress
  requested_at: string
}
```

---

## Production Stages (Artist View)

```typescript
// Firestore /production_stages/{job_id}  [REALTIME]
interface ProductionStageProjection {
  release_id: string
  current_stage: ProductionStageName
  stages: ProductionStageItem[]
}

type ProductionStageName =
  | "mastering"
  | "master_approval"
  | "lacquer_cutting"
  | "galvanic"
  | "test_pressing"
  | "test_pressing_approval"
  | "final_pressing"
  | "warehouse_arrival"
  | "shipping"

interface ProductionStageItem {
  stage: ProductionStageName
  status: "pending" | "in_progress" | "awaiting_approval" | "approved" | "completed"
  completed_at: string | null
}

// POST /production/{job_id}/approve  (Artist only)
interface ApprovalRequest {
  stage: ProductionStageName
  notes?: string
}
```

---

## Notifications

```typescript
// Firestore /notifications/{user_id}/items/{id}  [REALTIME]
interface Notification {
  id: string
  type:
    | "preorder_confirmed"
    | "campaign_funded"
    | "production_update"
    | "approval_required"
    | "record_ready"
    | "shipment_dispatched"
    | "refund_confirmed"
  message: string
  read: boolean
  created_at: string
}
```

---

## Points & Engagement

```typescript
// GET /points/
interface PointsSummary {
  total: number
  level: "listener" | "supporter" | "collector" | "vinyl_digger" | "super_supporter"
  next_level_threshold: number
  records_supported: number
  artists_supported: number
}
```

---

## API Routes Reference

```
Base URL: process.env.NEXT_PUBLIC_API_URL

Auth header: Authorization: Bearer {firebase_id_token}

// Releases
GET    /releases/                     → Release[]
GET    /releases/{id}                 → Release
POST   /releases/                     → Release         (artist only)

// Campaigns
GET    /campaigns/                    → Campaign[]
GET    /campaigns/{id}                → Campaign
GET    /campaigns/trending/           → Campaign[]
GET    /campaigns/almost-funded/      → Campaign[]

// Orders
POST   /orders/                       → OrderResponse

// Box
GET    /box/                          → Box
POST   /box/ship                      → Shipment

// Shipping
GET    /shipping/calculate            → ShippingCostResponse

// Points
GET    /points/                       → PointsSummary

// Artist
GET    /dashboard/campaigns/          → Campaign[]      (artist only)
POST   /production/{job_id}/approve   → void            (artist only)

// Store
GET    /store/                        → Release[]

// Webhooks (internal — never call from frontend)
POST   /webhooks/stripe
```

---

## Firestore Collections Reference

```
/releases/{release_id}              → ReleaseDoc
/campaigns/{campaign_id}            → CampaignProjection      [REALTIME]
/production_stages/{job_id}         → ProductionStageProjection [REALTIME]
/box_items/{customer_id}            → BoxProjection            [REALTIME]
/notifications/{user_id}/items/{id} → Notification             [REALTIME]
/user_preferences/{user_id}         → UserPreferences
```

---

## Environment Variables (Frontend)

```
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
```
