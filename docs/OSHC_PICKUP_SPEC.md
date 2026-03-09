# OSHC Pickup — Design Spec

Status: Ready to implement (confirmed with Sophia 2026-03-09)

## Background

Some students attend OSHC (Outside School Hours Care) at the school where KAF runs classes. KAF staff need to know this to account for students correctly. The arrangement varies by venue:

| Venue | How it works | Fee |
|---|---|---|
| Ironside | KAF staff picks up child from OSHC and returns them after class | $30 |
| Good News | OSHC staff drop off and pick up the child | Free |
| Yeronga | OSHC staff drop off and pick up the child | Free |

In all cases, KAF needs to know which students are coming from OSHC so staff can account for them.

## Data Model

### Venue table (new fields)

| Field | Type | Purpose |
|---|---|---|
| OSHC Available | Boolean | Does this venue have an OSHC arrangement? |
| OSHC Fee | Currency | Fee charged to parent (0 if free) |
| OSHC Notes | Text | Description of arrangement for staff (e.g. "KAF staff collects and returns" vs "OSHC staff handles drop-off/pickup") |

### Booking table (new field)

| Field | Type | Purpose |
|---|---|---|
| OSHC | Boolean | Is this student coming from/returning to OSHC for this class? |

Lives on the booking because:
- Can change term to term
- Not relevant for holiday classes
- Different children in same family may differ

### Enrollment form

Remove the current OSHC checkbox. OSHC is not an enrollment concern — it's a per-booking decision made at class registration time.

### Registration flow (register.html)

When booking a class:
- Look up the class's venue
- If `OSHC Available = true`, show: "Will [child] be attending from OSHC for this class?"
- Save to the Booking record
- Parent never sees pricing — fee is handled separately by Sophia

### Class roll / staff view

When viewing a class's bookings, OSHC students should be clearly marked so staff know to expect them from OSHC (and at Ironside, to go collect them).

## Implementation Steps

1. Add `OSHC Available`, `OSHC Fee`, `OSHC Notes` fields to Venues table
2. Set values: Ironside (true, $30, "KAF staff collects and returns"), Good News (true, $0, "OSHC staff handles"), Yeronga (true, $0, "OSHC staff handles")
3. Add `OSHC` boolean field to Bookings table
4. Remove OSHC checkbox from enrollment form (enrollment.html)
5. Add OSHC question to registration flow (register.html) — conditional on venue
6. Show OSHC flag in booking panel (classes.html) so Sophia can see it
