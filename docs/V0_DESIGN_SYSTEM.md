# Vinyl Platform — V0 Design System & UI Brief

> Share this document alongside ARCHITECTURE.md when prompting V0.
> The architecture doc defines WHAT to build. This doc defines HOW it looks.

---

## Design Philosophy

Minimal. Editorial. Honest.

This platform serves independent artists and vinyl collectors — people with taste.
The UI should feel like a well-designed independent record label website or a high-end
arts publication. Not a startup SaaS product. Not a streaming app.

**The reference point:** Think Céline, A.P.C., or Kinfolk magazine applied to a web platform.
White space is intentional. Typography carries the design. Everything earns its place.

---

## Visual Language

### Color Palette

```
Background:     #FFFFFF  (pure white — always)
Primary text:   #0A0A0A  (near black)
Secondary text: #6B6B6B  (mid grey)
Muted text:     #A0A0A0  (light grey — captions, metadata)
Borders:        #E5E5E5  (thin, light)
Dividers:       #F0F0F0  (barely there)
Accent:         #0A0A0A  (same as text — no color accents)
Error:          #C0392B  (used sparingly, text only)
Success:        #27AE60  (used sparingly, text only)
```

No gradients. No shadows. No rounded corners beyond 2px.
No color fills on buttons — use borders and text.

### Typography

**Primary font:** Inter (Google Fonts)
**Secondary font:** Playfair Display (for editorial headings, artist names, release titles)

```
Display heading (release title):    Playfair Display, 32–48px, normal weight, tight tracking
Section heading:                    Inter, 11px, uppercase, 0.15em letter-spacing, #6B6B6B
Body text:                          Inter, 14px, 400 weight, 1.6 line-height
Small / metadata:                   Inter, 12px, 400 weight, #A0A0A0
Price:                              Inter, 16px, 500 weight, #0A0A0A
Button text:                        Inter, 12px, 500 weight, uppercase, 0.08em tracking
```

### Spacing System

Base unit: 8px
```
xs:   4px
sm:   8px
md:   16px
lg:   24px
xl:   40px
2xl:  64px
3xl:  96px
```

Use generous white space. Sections breathe. Content is never cramped.

---

## Components

### Buttons

Two variants only:

**Primary button**
```
Border: 1px solid #0A0A0A
Background: #0A0A0A
Text: #FFFFFF
Padding: 10px 24px
Font: Inter 12px, 500, uppercase, 0.08em tracking
Hover: background #333333
No border-radius (or max 2px)
```

**Secondary / Ghost button**
```
Border: 1px solid #0A0A0A
Background: transparent
Text: #0A0A0A
Padding: 10px 24px
Same font as primary
Hover: background #F5F5F5
```

No icon-only buttons. No filled colored buttons. No pill shapes.

### Progress Bar (Campaign Funding)

The most important UI element. Must be elegant, not gamified.

```
Track:          1px height, #E5E5E5, full width
Fill:           1px height, #0A0A0A
No animation on load — just render current state
Above bar:      "22 of 30 pre-orders" — Inter 12px, #6B6B6B
Below bar:      "8 days remaining" — Inter 11px, #A0A0A0, right-aligned
```

Thin. Understated. The number tells the story, not the bar.

### Release Card

Used in grids on homepage, search, artist pages.

```
Layout:         vertical, no border, no shadow
Artwork:        square image, full width of card, no border-radius
Artist name:    Inter 11px, uppercase, 0.12em tracking, #6B6B6B — below artwork, 12px margin-top
Release title:  Playfair Display 16px, normal, #0A0A0A — below artist name, 4px margin-top
Price:          Inter 13px, 500, #0A0A0A — below title, 8px margin-top
Status pill:    Inter 10px, uppercase, border 1px solid — right of price
  Active:       border #0A0A0A, text #0A0A0A
  Funded:       border #27AE60, text #27AE60
  Last days:    border #C0392B, text #C0392B
```

Grid: 4 columns desktop, 2 columns tablet, 1 column mobile.
Gap between cards: 40px horizontal, 48px vertical.

### Campaign Page Layout

```
Left column (60%):
  - Release artwork (square, large)
  - Audio preview player (minimal — waveform or simple play button)
  - Track listing

Right column (40%):
  - Artist name (Inter 11px, uppercase, #6B6B6B)
  - Release title (Playfair Display 36px)
  - Catalog number (Inter 11px, #A0A0A0)
  - Format badge (10" / 12" / 2x12")
  - Divider line (#E5E5E5)
  - Progress bar section
  - Price (Inter 20px, 500)
  - Pre-order button (primary, full width)
  - Campaign end date (Inter 11px, #A0A0A0)
  - Divider
  - Artist bio (Inter 14px, #6B6B6B)
```

### Navigation

Top navigation only. No sidebar.

```
Left:   Platform wordmark — Playfair Display, 18px, italic
Center: Releases | Artists | Store (Inter 12px, uppercase, 0.1em tracking)
Right:  Search icon | My Box (with count badge) | Account
Height: 64px
Border bottom: 1px solid #E5E5E5
Background: #FFFFFF
Position: sticky
```

No hamburger menus on desktop. Mobile: hamburger opens full-screen overlay.

### My Box

Customer's personal collection/storage page.

```
Header: "My Box" — Playfair Display 32px
Subheader: "3 records" — Inter 13px, #6B6B6B

Each record row:
  - Artwork thumbnail (48x48px, square)
  - Release title — Inter 14px, 500
  - Artist name — Inter 12px, #6B6B6B
  - Status badge
  - Right side: "Request Shipment" button or status text

Status badges (text only, no fills):
  Pre-order:          #A0A0A0
  In production:      #6B6B6B
  Ready to ship:      #0A0A0A, bold
  Shipped:            #27AE60
  Delivered:          #A0A0A0
```

### Production Stage Tracker (Artist View)

9-stage horizontal timeline.

```
Stages displayed as dots connected by thin lines
Completed:    filled dot (#0A0A0A)
Current:      outlined dot with pulse (subtle)
Pending:      outlined dot (#E5E5E5)
Line:         1px, #E5E5E5 between dots, #0A0A0A for completed sections

Stage label:  Inter 10px, uppercase, below dot, #6B6B6B
Current stage label: #0A0A0A
```

### Forms & Inputs

```
Input:
  Border: 1px solid #E5E5E5
  Focus border: 1px solid #0A0A0A
  Background: #FFFFFF
  Padding: 10px 12px
  Font: Inter 14px
  No border-radius (or 2px max)
  Label: Inter 11px, uppercase, 0.1em tracking, #6B6B6B, above input

Validation error:
  Border: 1px solid #C0392B
  Error text: Inter 11px, #C0392B, below input
```

---

## Page Inventory

These are the pages V0 should be able to generate. Each prompt should reference
this design system and the architecture doc for context.

| Page | Route | Notes |
|------|-------|-------|
| Homepage | `/` | 4 sections: trending, almost funded, recommended, new |
| Campaign page | `/releases/[id]` | SSR, with live progress bar client component |
| Artist profile | `/artists/[id]` | Artist bio + release grid |
| Store | `/store` | Platform's 30-copy inventory |
| My Box | `/box` | Customer collection + shipment requests |
| Artist dashboard | `/dashboard` | Campaign stats, upload, production stages |
| Upload release | `/dashboard/upload` | Multi-step form |
| Logistics dashboard | `/ops` | Internal, production workflow |
| Login / Sign up | `/auth` | Minimal, email + Google |
| Checkout / Pre-order | Modal or `/checkout` | Stripe Elements embedded |

---

## V0 Prompting Guide

When generating a screen in V0, always include:

1. The page name and route
2. The specific component or section you want
3. Any dynamic data to mock (e.g. "campaign at 22/30, 8 days left")
4. Reference to this design system

**Example prompt for V0:**

> Using the vinyl platform design system (white background, Inter + Playfair Display,
> thin lines, no color accents, minimal aesthetic), generate the campaign page for a
> 12" vinyl release. Mock data: artist "Burial", title "Antidawn EP", catalog "HYP013",
> campaign at 22 of 30 pre-orders, 8 days remaining, price 19.99€, status active.
> Include the progress bar, pre-order button, and artwork placeholder.
> Left/right two-column layout as specified.

---

## What to Avoid

- No card shadows (box-shadow)
- No gradient backgrounds or buttons
- No rounded pill buttons
- No color-filled status badges (borders only)
- No decorative icons — only functional ones
- No animation beyond subtle hover states
- No dark mode (white only)
- No hero banners with overlaid text on images
- No sidebar navigation
- No emoji in UI
- No loading skeletons with color pulses — use simple opacity fade
