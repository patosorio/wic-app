# Vinyl Platform — Product Flows

> Reference document for V0 (screen generation) and Cursor (state machine implementation).
> Covers all three user flows: Artist, Customer, Admin.
> Every screen state, action, data field, and notification is defined here.

---

## Table of Contents

1. [Artist Flow](#1-artist-flow)
2. [Customer Flow](#2-customer-flow)
3. [Admin Flow](#3-admin-flow)
4. [Notification Reference](#4-notification-reference)
5. [State Machine Reference](#5-state-machine-reference)

---

## 1. Artist Flow

### Overview

```
Upload Release
  → Campaign Live (waiting for funds)
    → Campaign Funded → Production Stages
      → Mastering
      → Master Approval       ← artist action required
      → Test Pressing Sent
      → Test Pressing Approval ← artist action required
      → Artwork Submission     ← artist action required (15 day deadline)
      → Final Pressing
      → Warehouse Arrival
      → Shipping to Buyers
    → Campaign Failed → Archived after 30 days
```

---

### Screen 1.1 — Upload Release

**Route:** `/dashboard/upload`

**Description:**
Multi-step form. Artist fills in all release information before the campaign goes live.
Campaign goes live automatically after submission — no admin approval needed.

**Step 1 — Release Info**
```
Fields:
  title               string, required
  artist_name         string, required
  catalog_number      string, required
  format              select: 10in / 12in / 2x12in, required
  description         textarea, required

UI:
  Step indicator at top (Step 1 of 3)
  Continue button (primary)
```

**Step 2 — Audio**
```
Fields:
  audio_side_a        WAV upload, required, max 15 min
  audio_side_b        WAV upload, required, max 15 min

Validation:
  Show file name and duration after upload
  Show error if duration exceeds 15 minutes: "Side A exceeds the 15 minute maximum"
  Both sides required before continuing

UI:
  Upload zones for each side
  Duration indicator after upload
  Back / Continue buttons
```

**Step 3 — Artwork**
```
Fields:
  artwork_cover       image upload, required, must be square
  artwork_label_a     image upload, optional
  artwork_label_b     image upload, optional
  label_color         select: black / white

Note:
  Artwork can also be updated during the production Artwork Submission stage.
  Initial upload here is a starting point.

UI:
  Upload zones with preview
  label_color selector
  Back / Submit buttons
  On submit: "Your release has been submitted. Your campaign is now live."
```

---

### Screen 1.2 — Campaign Live (Waiting for Funds)

**Route:** `/dashboard/releases/[id]`

**Description:**
The artist's view of their active campaign. Real-time counter. Read only — no actions.

**Data displayed:**
```
From CampaignProjection [REALTIME]:
  current_count       "22 pre-orders"
  target              "of 30"
  percentage          progress bar fill
  days_remaining      "8 days remaining"
  presale_price       19.99€
  ends_at             campaign deadline date

From ReleaseDoc:
  title
  artist_name
  catalog_number
  format
  artwork_urls.cover
```

**States:**
```
ACTIVE:
  Progress bar live, counter updating in real time
  Status label: "Campaign Active"
  No actions available

FUNDED:
  Status label: "Funded ✓"
  Counter shows final count
  Message: "Your campaign reached its target. Production has started."
  CTA: "View Production Status" → links to Screen 1.3

FAILED:
  Status label: "Campaign Closed"
  Message: "This campaign did not reach its target. All pre-orders have been refunded."
  Counter shows final count reached
  No relaunch option
  Release stays visible in this state for 30 days then disappears
  After removal: only metadata visible in artist history as "Failed — [date]"
```

---

### Screen 1.3 — Production Status

**Route:** `/dashboard/releases/[id]/production`

**Description:**
The artist's production tracking view. Shows all stages. Artist takes action on
approval stages directly from this screen.

**Stage Timeline Component:**
```
Horizontal dot timeline showing all 7 stages:
  1. Mastering
  2. Master Approval      ← artist action
  3. Test Pressing
  4. Test Pressing Approval ← artist action
  5. Artwork Submission   ← artist action
  6. Final Pressing
  7. Shipping to Buyers

Dot states:
  pending             empty dot, grey line
  in_progress         filled dot, pulsing
  awaiting_approval   outlined dot, black border, "Action Required" label
  approved            filled dot, black
  completed           filled dot, black, checkmark

Data from ProductionStageProjection [REALTIME]:
  current_stage
  stages[].stage
  stages[].status
  stages[].completed_at
```

---

### Screen 1.3a — Stage: Mastering

**Stage:** `mastering`

**Artist view:**
```
Status: "Mastering in progress"
Description: "Your audio files are being mastered by our team."
No actions required.
Notification sent when stage completes → moves to Master Approval.
```

---

### Screen 1.3b — Stage: Master Approval

**Stage:** `master_approval`
**Status:** `awaiting_approval`

**Artist view:**
```
Header: "Master Ready for Approval"
Description: "Listen to the mastered audio carefully before approving.
              This is your last chance to request changes before lacquer cutting."

Download section:
  Button: "Download Master" (ghost button)
  → Triggers secure download link from Cloud Storage
  File format: WAV
  File label: "{catalog_number}_master.wav"

Action section:
  Button: "Approve Master" (primary)
  Button: "Request Changes" (ghost, red border)

Request Changes modal:
  textarea: "Describe the changes needed" (required)
  Submit button
  On submit: stage status → rejected
             Admin receives notification with feedback text
             Artist sees: "Changes requested. Awaiting revised master."

On Approve:
  Confirmation modal: "Once approved, lacquer cutting begins immediately. Are you sure?"
  Confirm button
  Stage status → approved → next stage begins automatically
```

**Rejected state view:**
```
Status: "Changes Requested"
Message: "Your feedback has been sent. The team will upload a revised master."
Shows feedback text submitted by artist
Stays in this state until admin uploads new master
When new master uploaded: returns to awaiting_approval
Artist receives notification: "Revised master is ready for your review"
```

---

### Screen 1.3c — Stage: Test Pressing

**Stage:** `test_pressing`

**Artist view:**
```
Status: "Test Pressing in Production"
Description: "A test pressing is being produced. It will be shipped to your
              registered address for listening approval."

Shows registered shipping address:
  {user.full_name}
  {user.address.line1}
  {user.address.city}, {user.address.postal_code}
  {user.address.country}

Link: "Update address" → profile address settings
Note: "Address must be updated before the test pressing ships."

When admin marks test pressing as shipped:
  Status changes to: "Test Pressing Shipped"
  Tracking number displayed if available
  Notification sent to artist
```

---

### Screen 1.3d — Stage: Test Pressing Approval

**Stage:** `test_pressing_approval`
**Status:** `awaiting_approval`

**Artist view:**
```
Header: "Test Pressing Received?"
Description: "Once you have received and listened to your test pressing,
              approve or report any issues."

Action section:
  Button: "Approve Test Pressing" (primary)
  Button: "Report Issue" (ghost, red border)

Report Issue modal:
  textarea: "Describe the issue with the test pressing" (required)
  Submit button
  On submit: stage status → rejected
             Admin notified with feedback
             Artist sees: "Issue reported. The team will review and respond."

On Approve:
  Confirmation modal: "Approving will begin final pressing of all copies. Confirm?"
  Confirm button
  Stage → approved → Artwork Submission stage begins
```

**Rejected state:**
```
Status: "Issue Reported"
Message: "The team has been notified of your feedback."
Shows feedback submitted
Stays until admin resolves and resets stage
When reset: returns to awaiting_approval
Artist notified: "Your test pressing issue has been reviewed. Please check again."
```

---

### Screen 1.3e — Stage: Artwork Submission

**Stage:** `artwork_submission`
**Status:** `awaiting_approval` (artist must act)

**Artist view:**
```
Header: "Submit Final Artwork"
Description: "Upload your final print-ready artwork files.
              You have 15 days from today to submit. After this deadline,
              blank labels will be used for the pressing."

Deadline banner:
  "Deadline: {artwork_deadline_date} — {n} days remaining"
  Changes to red when 3 days or fewer remain
  Changes to: "Deadline passed — blank labels will be used" after 15 days

Warning notifications sent at:
  Day 10 (5 days left): "Reminder: 5 days left to submit artwork"
  Day 13 (2 days left): "Urgent: 2 days left to submit artwork"
  Day 15 (deadline):    "Artwork deadline passed. Blank labels will be used."

Upload section:
  artwork_cover       image upload, square, print resolution
  artwork_label_a     image upload, label format
  artwork_label_b     image upload, label format
  artwork_insert      image upload, optional (inner sleeve)

Shows current uploaded artwork as previews if already uploaded in Step 3.
Artist can replace any file.

Submit button: "Submit Final Artwork" (primary)
On submit: stage status → approved → Final Pressing begins
           Admin notified: "Artist has submitted final artwork for {release_title}"

After 15 days with no submission:
  System automatically advances stage with blank label flag
  Admin notified: "Artwork deadline passed for {release_title}. Proceeding with blank labels."
  Artist sees deadline passed banner, no more upload option
```

---

### Screen 1.3f — Stage: Final Pressing

**Stage:** `final_pressing`

**Artist view:**
```
Status: "Final Pressing in Production"
Description: "Your record is being pressed. This typically takes 4–6 weeks."
No actions required.
Progress is read only.
Notification sent when pressing completes and records arrive at warehouse.
```

---

### Screen 1.3g — Stage: Warehouse Arrival & Shipping

**Stage:** `warehouse_arrival` → `shipping`

**Artist view:**
```
Warehouse Arrival:
  Status: "Records Arrived at Warehouse"
  Message: "Your records have arrived. Shipping to buyers will begin shortly."
  Shows:
    Total copies pressed: {pressing_qty}
    Copies going to pre-sale buyers: 30
    Copies going to wholesale: 50
    Your copies: 30 → "Will be shipped to your registered address"
    Platform store copies: 30

Shipping:
  Status: "Shipping to Buyers"
  Message: "Records are being shipped to all pre-order customers."
  Artist copy status: shows tracking for artist's own 30 copies

Completed:
  Status: "Complete ✓"
  Message: "All records have been shipped. Congratulations on your release."
```

---

## 2. Customer Flow

### Overview

```
Browse & Discover
  → Pre-Order (campaign active)
    → Campaign Funded → Production wait → Ready → Request Shipment → Delivered
    → Campaign Failed → Automatic refund → Removed from box

Store Purchase
  → Immediate → Ready → Request Shipment → Delivered
```

---

### Screen 2.1 — Browse & Discovery

**Route:** `/`

**Description:**
Homepage with four sections. All campaign data is real-time via Firestore.

```
Section 1: Trending Releases
  Horizontal scroll of CampaignProjection cards
  Shows: artwork, title, artist_name, current_count/target, days_remaining

Section 2: Almost Funded
  Campaigns with percentage >= 70
  Urgency label: "X copies to go"
  Sorted by closest to target first

Section 3: Recommended for You
  Personalised (MVP: most recent active campaigns)
  Same card component

Section 4: New Releases
  Sorted by starts_at descending
  Same card component
```

---

### Screen 2.2 — Campaign Page

**Route:** `/releases/[id]`

**Description:**
Full campaign page. SSR for SEO. Progress bar is client component (Firestore).

```
Left column (60%):
  Release artwork (full width square)
  Audio preview player
    - Play/pause button
    - Side A / Side B toggle
    - Track listing

Right column (40%):
  artist_name (uppercase small)
  title (Playfair Display large)
  catalog_number (muted small)
  format badge
  ─────────────────────────────
  Progress bar [REALTIME]
    current_count of target pre-orders
    percentage bar
    days_remaining
  ─────────────────────────────
  presale_price
  Pre-Order button (primary, full width)
  "Retail price after campaign: {retail_price}€"
  Campaign ends: {ends_at}
  ─────────────────────────────
  About this release
  description

Button states:
  Campaign ACTIVE:   "Pre-Order — 19.99€" (primary, enabled)
  Campaign FUNDED:   "Campaign Funded — Available in Store" (ghost, links to store)
  Campaign FAILED:   "Campaign Closed" (disabled)
  Already ordered:   "Pre-Ordered ✓" (disabled)
```

---

### Screen 2.3 — Pre-Order Checkout

**Trigger:** Customer clicks Pre-Order button
**Type:** Modal overlay (not a separate page)

```
Modal content:
  Release summary:
    artwork thumbnail
    title
    artist_name
    format

  Price breakdown:
    Pre-order price:    19.99€
    Shipping:           Calculated later
    Total charged now:  19.99€

  Notice:
    "Your card will be charged 19.99€ now.
     Shipping is paid separately when your record is ready.
     If the campaign does not reach its target, you will be
     automatically refunded within 5–10 business days."

  Stripe payment element (embedded)

  Confirm Pre-Order button (primary)
  Cancel link

On success:
  Modal closes
  Shows success state: "Pre-order confirmed. Your record is in your box."
  Campaign progress bar increments in real time
```

---

### Screen 2.4 — My Box

**Route:** `/box`

**Description:**
All customer records in one place — pre-orders, store purchases, all statuses.
Real-time via Firestore. Records can be bundled into one shipment.

```
Header:
  "My Box"
  "{n} records"

Filter tabs:
  All | Waiting | Ready to Ship | Shipped

Record list (BoxItemProjection [REALTIME]):
  Each item shows:
    artwork_url         48x48 square thumbnail
    release_title       Inter 14px 500
    artist_name         Inter 12px grey
    format              small badge
    status              text, colour by status (see design system)

  Status display:
    pre_order           "Campaign in progress" — grey
    in_production       "Being pressed" — grey
    ready               "Ready to Ship" — black bold
    in_box              "In your box" — grey
    shipped             "Shipped" → shows tracking link
    delivered           "Delivered ✓" — green

  Right side action:
    status = ready      checkbox (for multi-select) + "Ship this" button
    status = shipped    "Track Shipment" link
    others              status text only

Multi-select shipment:
  When one or more items are "ready":
    Banner appears at bottom: "{n} records selected — Ship together"
    "Request Shipment" button (primary)
    Estimated shipping cost shown: "~€{cost} estimated"
```

---

### Screen 2.5 — Shipment Request

**Trigger:** Customer clicks "Request Shipment"
**Type:** Modal or dedicated page `/box/ship`

```
Step 1 — Confirm Records:
  List of selected records with artwork thumbnails
  Total: {n} records

Step 2 — Shipping Address:
  Saved address displayed (if exists):
    full_name
    line1, line2
    city, postal_code, country
  "Ship to this address" button (primary)
  "Use a different address" link → shows address form

  Address form fields (ShippingAddress type):
    full_name
    line1
    line2 (optional)
    city
    postal_code
    country (select)
  "Save as default address" checkbox

Step 3 — Cost & Confirm:
  Records being shipped: list
  Shipping to: address summary
  Shipping cost: {cost}€ (from GET /shipping/calculate)
  Total charged: {cost}€

  "Confirm & Pay Shipping" button (primary)
  Stripe payment element for shipping charge

On success:
  "Shipment requested. You will receive a tracking number when dispatched."
  Box items update to "shipped" status in real time
```

---

### Screen 2.6 — Campaign Failure (Customer View)

**Trigger:** Campaign fails — customer had a pre-order

```
Notification received:
  "The campaign for {release_title} did not reach its target.
   Your payment of 19.99€ has been refunded.
   Refunds typically appear within 5–10 business days."

My Box:
  Record disappears from active box
  Visible in "Past" tab for 30 days as:
    artwork (greyed out)
    "{release_title} — Campaign did not fund"
    "Refunded {date}"
  Removed completely after 30 days
```

---

### Screen 2.7 — Store

**Route:** `/store`

**Description:**
Platform's 30 copies per funded release, sold at retail price.

```
Header:
  "Store"
  "Limited pressings from funded campaigns"

Grid of release cards:
  Same card component as homepage
  Shows retail_price (25.99€) instead of presale_price
  Stock indicator: "12 left" / "Last copy" / "Sold out"

Release detail page in store context:
  Same layout as campaign page
  Button: "Add to Cart — 25.99€" (primary)
  No progress bar
  "Ships from warehouse" notice

Checkout:
  Same modal as pre-order
  Shipping address selection (same Screen 2.5 flow)
  Immediate charge + shipping charge
  Goes directly to My Box as "ready" status
```

---

## 3. Admin Flow

### Overview

```
Dashboard (production jobs + active campaigns)
  → Manage production stages
  → Upload master files
  → Mark test pressing shipped
  → Manage artwork deadline
  → Mark warehouse arrival
  → Strategic campaign support (complete near-target campaigns)
  → Platform store management
  → User & order management
```

---

### Screen 3.1 — Admin Dashboard

**Route:** `/ops`

**Description:**
First screen on login. Two primary panels side by side.

```
Left panel — Production Jobs Needing Action:
  List of production jobs with pending admin actions
  Each item shows:
    release_title
    artist_name
    current_stage
    action_required     "Upload Master" / "Mark Shipped" / "Mark Arrived" / "Awaiting Artist"
    days_in_stage       how long it has been in current stage

  Sorted by: action_required first, then days_in_stage descending
  Click → opens production job detail (Screen 3.3)

Right panel — Active Campaigns:
  List of live campaigns
  Each item shows:
    release_title
    artist_name
    current_count / target
    percentage bar
    days_remaining
    flag if close to target (>= 70%): "Almost Funded" badge

  At bottom: "Complete Campaign" button for flagged campaigns (strategic support)
  Click on campaign → opens campaign detail
```

---

### Screen 3.2 — Campaign Management

**Route:** `/ops/campaigns`

**Description:**
Full list of all campaigns across all statuses.

```
Filter tabs:
  Active | Funded | Failed | All

Campaign list columns:
  release_title
  artist_name
  status badge
  current_count / target
  percentage
  days_remaining / ended_at
  total_revenue (funded campaigns)
  action button

Actions per status:
  ACTIVE:   "View" | "Complete Campaign" (if >= 70%)
  FUNDED:   "View Production"
  FAILED:   "View" (read only)

Complete Campaign modal (strategic support):
  "This campaign has {current_count} pre-orders.
   The platform will purchase {30 - current_count} copies to reach the target.
   Cost to platform: {(30 - current_count) × 19.99}€
   These copies will go to platform store inventory."
  Confirm button (primary)
  Cancel
```

---

### Screen 3.3 — Production Job Detail

**Route:** `/ops/production/[job_id]`

**Description:**
Admin's control panel for a single release in production.
Every stage is managed from this screen.

```
Header:
  release_title (Playfair Display)
  artist_name
  catalog_number
  format
  pressing_qty

Stage timeline (same visual as artist view but with admin actions)

Current stage panel — changes based on active stage:
```

**Stage: mastering**
```
Admin action:
  Button: "Mark Mastering Complete" (primary)
  On confirm: stage → completed, next stage (master_approval) → awaiting_approval
  Artist notified: "Your master is ready for review"

Upload field:
  "Upload Master File (WAV)"
  File upload input
  Button: "Upload & Notify Artist"
  On upload: file stored in Cloud Storage
             download link made available on artist's screen
             stage → awaiting_approval
             artist notified
```

**Stage: master_approval — awaiting artist**
```
Admin view:
  Status: "Waiting for artist approval"
  Artist name + email shown
  Days waiting counter
  Uploaded master file name shown
  Option: "Re-upload Master" (if artist requested changes)

If artist rejected:
  Status: "Changes Requested"
  Artist feedback text displayed in a box
  "Re-upload Master" button becomes primary
  On re-upload: artist notified, stage returns to awaiting_approval
```

**Stage: test_pressing**
```
Admin action:
  Input: Tracking number (optional)
  Shipping address shown (artist's registered address):
    {artist.full_name}
    {artist.address}

  Button: "Mark Test Pressing Shipped" (primary)
  On confirm: stage → in_progress (shipped state)
              artist notified with tracking number if provided
```

**Stage: test_pressing_approval — awaiting artist**
```
Admin view:
  Status: "Waiting for artist to approve test pressing"
  Days waiting counter
  Artist address where it was sent

If artist rejected:
  Status: "Issue Reported"
  Artist feedback displayed
  Options:
    "Ship New Test Pressing" (primary) → returns stage to test_pressing
    "Resolve & Override" (ghost) → admin can force advance with a note (rare)
```

**Stage: artwork_submission**
```
Admin view:
  Deadline date shown
  Days remaining counter (red if <= 3)
  Current artwork files shown if submitted

  If submitted:
    Artwork previews shown
    Button: "Approve Artwork & Begin Final Pressing" (primary)
    On confirm: stage → approved, final_pressing begins

  If not submitted and deadline not passed:
    Status: "Waiting for artist artwork"
    Warning notifications sent automatically at day 10 and day 13

  If deadline passed:
    Status: "Deadline Passed — Blank Labels"
    Button: "Proceed with Blank Labels" (primary)
    On confirm: stage → approved with blank_labels flag
                Final pressing begins
```

**Stage: final_pressing**
```
Admin action:
  Button: "Mark Final Pressing Complete" (primary)
  On confirm: stage → completed, warehouse_arrival begins
```

**Stage: warehouse_arrival**
```
Admin action:
  Input: Actual quantity received (default: pressing_qty)
  Button: "Mark Records Arrived at Warehouse" (primary)
  On confirm:
    Inventory allocated automatically:
      presale_buyers: 30
      wholesale:      50
      artist:         30
      platform_store: 30
    All buyer box_items → ready
    All buyers notified
    Artist notified
    Stage → completed
    Shipping stage begins automatically
```

---

### Screen 3.4 — Platform Store Management

**Route:** `/ops/store`

```
List of platform's inventory (30 copies per release):
  release_title
  copies_available
  copies_sold
  revenue_to_date
  status: active / sold_out

Actions:
  Toggle listing visibility
  Edit retail price (default 25.99€)
  View orders for this release
```

---

### Screen 3.5 — Users & Orders

**Route:** `/ops/users`

```
User list with filters:
  All | Customers | Artists

Per user:
  name, email, role, joined_date
  For customers: total orders, total spent
  For artists: total releases, funded releases

Click → user detail:
  Full order history
  Box contents
  Points balance
  Manual refund button (with reason field)
```

---

### Screen 3.6 — Finance Overview

**Route:** `/ops/finance`

```
Summary cards:
  Active presale float (total held in pending campaigns)
  Production payments due (campaigns in production × 600€)
  Platform store revenue MTD
  Total refunds issued MTD

Active production payments:
  List of releases in production
  Deposit paid: 600€ ✓
  Remaining due: 600€ — due on warehouse arrival
  Days in production

Campaign performance:
  Total campaigns this period
  Success rate %
  Average pre-orders per campaign
```

---

## 4. Notification Reference

All notifications are stored in Firestore `/notifications/{user_id}/items/{id}`.

| Event | Recipient | Message |
|-------|-----------|---------|
| Pre-order confirmed | Customer | "Your pre-order for {title} is confirmed." |
| Campaign funded | Customer | "{title} reached its target. Production has started." |
| Campaign failed | Customer | "{title} did not reach its target. Your refund is on its way." |
| Record ready to ship | Customer | "Your copy of {title} is ready. Request shipment from your box." |
| Shipment dispatched | Customer | "Your record is on its way. Tracking: {tracking}" |
| Campaign funded | Artist | "Your campaign for {title} has funded. Production is starting." |
| Campaign failed | Artist | "Your campaign for {title} did not reach its target." |
| Master ready | Artist | "Your master for {title} is ready for review and download." |
| Revised master ready | Artist | "A revised master for {title} is ready for your review." |
| Test pressing shipped | Artist | "Your test pressing for {title} has been shipped to your address." |
| Artwork reminder (day 10) | Artist | "5 days left to submit artwork for {title}." |
| Artwork reminder (day 13) | Artist | "Urgent: 2 days left to submit artwork for {title}." |
| Artwork deadline passed | Artist | "The artwork deadline for {title} has passed. Blank labels will be used." |
| Records at warehouse | Artist | "Your records for {title} have arrived at the warehouse." |
| Master uploaded | Admin | "{artist_name} — master uploaded for {title}. Awaiting artist approval." |
| Artist approved master | Admin | "{artist_name} approved the master for {title}." |
| Artist rejected master | Admin | "{artist_name} requested changes to the master for {title}." |
| Artist approved test pressing | Admin | "{artist_name} approved the test pressing for {title}." |
| Artist rejected test pressing | Admin | "{artist_name} reported an issue with the test pressing for {title}." |
| Artwork submitted | Admin | "{artist_name} submitted final artwork for {title}." |
| Artwork deadline passed | Admin | "Artwork deadline passed for {title}. Proceeding with blank labels." |

---

## 5. State Machine Reference

### Campaign States

```
DRAFT → ACTIVE                    on: release submitted
ACTIVE → FUNDED                   on: current_count >= target (30)
ACTIVE → FAILED                   on: day-30 Cloud Tasks job, count < target
FAILED → ARCHIVED                 on: 30 days after failure (data purge, metadata kept)
```

### Production Stage States

```
pending → in_progress             on: admin advances stage
in_progress → awaiting_approval   on: admin uploads file / marks shipped
awaiting_approval → approved      on: artist approves
awaiting_approval → rejected      on: artist rejects with feedback
rejected → awaiting_approval      on: admin re-uploads / resolves
approved → (next stage pending)   on: approval confirmed
```

### Artwork Stage Special Rules

```
artwork_submission → approved     on: artist submits + admin approves
artwork_submission → approved*    on: day 15 timeout, system advances with blank_labels=true
* blank_labels flag stored on ProductionJob
```

### Box Item States

```
pre_order → in_production         on: event campaign.funded
in_production → ready             on: event record.arrived_warehouse
ready → shipped                   on: customer requests + pays shipment
shipped → delivered               on: admin marks delivered (or carrier webhook)
pre_order → [removed]             on: event campaign.failed (after 30 day grace in history)
```
