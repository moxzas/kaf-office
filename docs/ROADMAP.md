# KAF System Roadmap

## Current State (Feb 2026)

- **Enrollment form** — live at app.sonzai.com/kaf/enrollment.html. One-time family registration (parent + children). Saves to Airtable.
- **Contacts/CRM** — 1,944 contacts imported from Wix. Segmented by venue, interest, email status.
- **Email campaigns** — planned (see plan file), not yet built. Simple template-based sender via Resend.
- **Class booking** — still on Wix. Sophia publishes promo tiles on Wix, parents book and pay through Wix.
- **Three intake processes today:** (1) Wix booking, (2) emailed PDF/photo of paper form, (3) physical form (rare now).

## Target Architecture

### Goal
Single system where families enrol once, then register children for classes and pay — all off Wix.

### Flow
1. Sophia publishes promo tiles on Wix (keeps her existing workflow)
2. "Register" button on Wix links to our system
3. If we recognise the family (cookie/session) → go straight to class registration
4. If not → login or enrol first, then register for class
5. Payment via Stripe at checkout

### Key Components to Build

#### 1. Email Campaign Sender (next up)
- Campaign composer page (campaign.html)
- Backend send via Resend
- Unsubscribe handling
- See plan file for full details

#### 2. Auth / Identity
- Need to identify returning families without a complex auth system
- **Magic link auth** (preferred): parent enters email → gets a link via Resend → clicks it → session cookie set. No password to remember.
- Optional password creation for frequent users (families registering for multiple classes)
- Password reset flow
- Could use Supabase if magic links aren't enough, but try to keep it simple on existing stack first
- Cookie-based session management

#### 3. Class Registration
- Browse available classes (from Airtable Classes table)
- Filter by venue, day, age group
- Select class → creates Enrollment record linking Student to Class
- Support multiple children registering for multiple classes
- Pre-fill from known family data

#### 4. Stripe Payment
- Checkout when registering for a class
- Handle: single class, multi-class, term packages
- Stripe Checkout (hosted) is simplest — redirect to Stripe, webhook confirms payment
- Update Enrollment payment status in Airtable on webhook

#### 5. Wix Integration Point
- Sophia's promo tiles on Wix link to: `app.sonzai.com/kaf/register?class={CLASS_ID}`
- Our system handles everything from there
- No Wix API integration needed — just outbound links

## Implementation Order

1. Email campaigns (planned, ready to build)
2. Magic link auth + session management
3. Class browsing + registration page
4. Stripe payment integration
5. Deprecate Wix booking (keep Wix site for marketing only)

## Design Principles

- Low digital literacy audience — keep everything simple
- Minimal screens, clear labels, no jargon
- No build tools — static HTML/JS like enrollment.html
- Airtable stays as the database (familiar to Sophia)
- Backend stays on existing Dart/Shelf server
- Resend for all transactional email
