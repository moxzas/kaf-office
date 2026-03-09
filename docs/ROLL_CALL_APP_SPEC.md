# Roll Call App — Spec

Status: Draft (decisions confirmed 2026-03-09)

## Overview

A tablet PWA (Progressive Web App) for class roll call. Admin selects a session, hands the tablet to the teacher, teacher marks attendance and takes photos — all offline. Data syncs when the session is closed.

Tablets are venue-agnostic — shared ad hoc across venues. Target hardware: iPad 9th gen (2021), 64GB WiFi.

## Why PWA

- Same HTML/JS stack as the rest of the system
- Camera access via browser APIs (getUserMedia)
- Offline via Service Worker + IndexedDB
- Install to iPad home screen — looks and behaves like a native app
- No App Store, no signing, no build tools
- Deploy is just pushing files to the server like everything else

## User Flow

### 1. Admin Setup (requires network)

- Admin opens app on tablet, enters their **PIN** (each admin has a unique PIN)
- Sees list of active classes, grouped by day/venue
- Selects a class — app auto-selects the current session based on term week
  - e.g. if today is Week 3 of Term 1, "Week 3 — Mon 3 Mar 2026" is pre-selected
  - Admin can override if needed (e.g. catching up a missed session)
- App downloads session data to IndexedDB:
  - Student list (names, photos, medical alerts, dietary notes)
  - OSHC flags
  - Authorized pickup people per student (parent + extras)
  - Photo permission status per student
- App enters **locked mode** — full screen, single purpose, no navigation back

### 2. Teacher Roll Call (offline)

Teacher receives the tablet already showing the class roll.

**Screen layout:**
- Top bar: class name, venue, session date, student count (present/total)
- Student list: photo thumbnail, name, status indicators (OSHC, medical alert)
- Each student card has clear tap targets for actions

**Marking attendance:**
- Tap student → mark **arrived** (timestamp recorded)
- OSHC students visually distinct (teacher knows to expect them from OSHC)
- Students without a photo show a camera prompt — tap to take enrollment photo
- Medical/allergy alerts visible at a glance (icon + tap to see details)

**Marking departure:**
- Tap arrived student → mark **departed**
- Select who collected them from authorized pickup list
- If someone not on the list collects → text field to record name + relationship
- Timestamp recorded

**Taking photos:**
- **Enrollment photo**: prompted when student has no photo on first session. Taken once, stored permanently on student record. Used for identification on all future rolls.
- **Artwork/class photos**: teacher can snap photos during class, tagged to student + session. Permission-aware:
  - "Yes - child & artwork" → photos of child and their artwork
  - "Yes - artwork only" → photos of artwork without the child
  - "No photos" → artwork photo still available (no child in frame)
  - Permission level shown on camera screen so teacher knows the rule

### 3. Session Close (requires network)

- Admin (or teacher) taps "Close Session"
- App syncs to server:
  - Attendance records (arrived/departed times, collected by)
  - Enrollment photos → uploaded to Spaces, URL saved to student record
  - Class/artwork photos → uploaded to Spaces with metadata tags
- Session marked as complete
- App returns to class selection screen

If network is unavailable at close time, data stays in IndexedDB. App shows "pending sync" state. Syncs automatically when network returns.

## Sessions

Sessions are auto-generated server-side per class:

- **Term classes**: when a class is created with Term + Sessions in Term (e.g. "Term 1 2026", 10 sessions), the server generates 10 session records with dates calculated from the term start date and day of week.
- **Holiday programs**: single session, date from the class record.

The app auto-selects the current session by matching today's date to the nearest session date. Admin can override.

## Data Model

### Sessions table (new)

| Field | Type | Purpose |
|---|---|---|
| Session Name | Formula | Auto: "Week 3 — Mon 3 Mar 2026" |
| Class | Link | Which class this session belongs to |
| Session Date | Date | The date of this session |
| Week Number | Number | Week within the term (1-10 etc) |
| Status | Select | Scheduled / In Progress / Complete |

### Attendance records

Uses existing **Attendance** table. Fields needed:
- Student (link)
- Class (link)
- Session (link to Sessions table)
- Status (Present / Absent / Late)
- Arrived At (text — time string)
- Departed At (text — time string)
- Collected By (text — name of person who picked up)
- Notes (text)

### Admin PINs

New **Admins** table or field on existing table:

| Field | Type | Purpose |
|---|---|---|
| Name | Text | Admin name |
| PIN | Text | 4-6 digit PIN for tablet login |
| Active | Checkbox | Can this admin log in? |

### Photo Storage — DigitalOcean Spaces

Photos stored in DigitalOcean Spaces (S3-compatible, already on DigitalOcean).

**Bucket structure:**
```
kaf-photos/
  enrollment/
    {student_id}.jpg          — one per student, overwritten if retaken
  classes/
    {class_id}/{session_date}/
      {timestamp}_{student_id}.jpg  — artwork/class photos
```

**Metadata in Airtable:**

New **Photos** table:

| Field | Type | Purpose |
|---|---|---|
| URL | URL | Spaces public URL or signed URL |
| Student | Link | Which student |
| Class | Link | Which class (null for enrollment photos) |
| Session | Link | Which session (null for enrollment photos) |
| Type | Select | Enrollment / Artwork / Class |
| Photo Permission | Text | Permission level at time of capture |
| Taken By | Link | Which admin/teacher took it |
| Taken At | DateTime | When the photo was taken |

Students table gets a new `Photo URL` field (text/URL) pointing to their enrollment photo in Spaces.

## Photo Repository

The Photos table doubles as a tagged repository for multiple use cases:

- **Roll call**: enrollment photos displayed on the attendance list for student identification
- **Marketing**: filter by "child & artwork" permission → pull photos for social media, website, flyers
- **Sales to parents**: filter by student/parent → end-of-term album, prints, t-shirts with their child's artwork
- **Class records**: browse by class + session to see what was done that day

Permission is captured at time of photo so it's always clear what can be used for what, even if the parent changes their preference later.

## Offline Architecture

```
┌─────────────────────────────┐
│  Service Worker             │
│  - Caches app shell (HTML,  │
│    CSS, JS)                 │
│  - Intercepts fetch for     │
│    offline support          │
└─────────────────────────────┘

┌─────────────────────────────┐
│  IndexedDB                  │
│  - Session data (students,  │
│    photos, pickup lists)    │
│  - Attendance state         │
│  - Queued photos (blobs)    │
│  - Pending sync queue       │
└─────────────────────────────┘

┌─────────────────────────────┐
│  Sync Manager               │
│  - On "Close Session":      │
│    POST attendance → server │
│    Upload photos → Spaces       │
│    Mark session complete    │
│  - Retry on network failure │
└─────────────────────────────┘
```

## Security Considerations

- Admin PIN authentication — not high security, but prevents accidental misuse
- Session data contains PII (student names, photos, medical info) — stored only in IndexedDB, cleared after successful sync
- Photos captured via getUserMedia (not file picker) — avoids saving to camera roll
- Use iOS Guided Access to lock tablet to Safari/PWA during class
- Spaces bucket: private by default, photos served via signed URLs or through the server as a proxy

## Server-Side Requirements

The existing Dart/Shelf server needs new endpoints:

- `POST /api/kaf/pin-auth` — validate admin PIN, return session token
- `GET /api/kaf/sessions?class={id}` — list sessions for a class
- `POST /api/kaf/sessions/generate` — auto-generate sessions for a class
- `GET /api/kaf/roll?session={id}` — download full roll data for offline use
- `POST /api/kaf/roll/sync` — upload attendance + mark session complete
- `POST /api/kaf/photos/upload` — upload photo to Spaces, save metadata to Airtable
- `GET /api/kaf/photos?student={id}` — get photos for a student

## Implementation Order

1. Sessions table + auto-generation logic (server-side)
2. Basic PWA shell with Service Worker and install-to-home-screen
3. Admin PIN auth + class/session selection screen
4. Student list display with attendance marking (online first)
5. Offline support (IndexedDB + sync)
6. Spaces setup + enrollment photo capture and upload
7. Departure tracking (collected by whom)
8. Artwork/class photo capture with permission awareness
9. Photo browsing (Sophia can view photos by class/student)
10. Polish (medical alerts, OSHC indicators, Guided Access instructions)
