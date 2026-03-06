# KAF Office - Kids Art Fun Enrollment & CRM

Enrollment system and CRM for Kids Art Fun, a children's art school in Brisbane, Australia.

## Live System

| Page | URL | Purpose |
|------|-----|---------|
| Enrollment Form | `app.sonzai.com/kaf/enrollment.html` | Parent/student registration (SurveyJS) |
| Class Admin | `app.sonzai.com/kaf/classes.html` | Sophia creates/edits classes, copies reg links |
| Class Registration | `app.sonzai.com/kaf/register.html?class={ID}` | Parents register children for a class |
| Enrollment Admin | `app.sonzai.com/kaf/enrollments.html` | Staff edits existing enrollments |

## Architecture

```
Browser (app.sonzai.com/kaf/*)
  |
  |-- enrollment.html  -- SurveyJS form, direct Airtable CRUD
  |-- classes.html      -- class CRUD, registration link generation
  |-- register.html     -- parent class registration (email lookup)
  |-- enrollments.html  -- admin enrollment editor
  |
  +---> Airtable API (Parents, Students, Classes, Bookings, ...)
  +---> ezeo_otg Server (/api/kaf/audit)
            |
            +---> Airtable (Audit Log)
            +---> Resend API (email notifications)
```

All pages are static HTML/JS with no build step. Airtable is the database. The Dart/Shelf backend (ezeo_otg, separate repo) handles audit logging and email.

## Database (Airtable)

**Base ID:** `appNuMdxaiSYdgxJS`

| Table | Records | Status |
|-------|---------|--------|
| Parents | ~22 | Active - enrollment form |
| Students | ~26 | Active - enrollment form |
| Classes | varies | Active - classes.html |
| Bookings | varies | Active - register.html |
| Venues | 5 | Active - seeded by setup script |
| Teachers | varies | Active - managed in Airtable UI |
| Contacts | 0 (backed up) | CRM/mailing list, cleared for free plan limits |
| Audit Log | active | Enrollment history as JSON blobs |
| Attendance | 0 | Planned, not yet used |

Full schema: [docs/SCHEMA.md](docs/SCHEMA.md)

## Project Structure

```
src/                    # Frontend pages (deployed to server)
  enrollment.html       # SurveyJS enrollment form
  classes.html          # Class admin for Sophia
  register.html         # Parent-facing class registration
  enrollments.html      # Admin enrollment editor
  index.html            # Landing/redirect page

scripts/                # Python utilities
  setup_classes.py      # Create tables, seed venues
  import_contacts.py    # Original Wix contacts import
  reimport_contacts.py  # Re-import from backup JSON
  inspect_actual.py     # Quick schema inspection
  verify_base.py        # Schema validation

docs/                   # Documentation
  SCHEMA.md             # Authoritative Airtable schema (keep current)
  ROADMAP.md            # System roadmap and next steps
  DEPLOYMENT.md         # Deployment guide
  START_HERE.md         # Navigation for new developers
  sample_data/          # CSV test data
  archive/              # Historical docs (phases, handovers, old plans)

intake-forms/           # Scanned PDF enrollment forms (not tracked in git)
data/                   # CSV imports and backups (gitignored, contains PII)
```

## Deployment

Frontend auto-deploys on push to `main` via GitHub Actions:
- Copies `src/*` to the server at `/home/deploy/webremote/kaf/`
- Server: `209.38.86.222` (DigitalOcean Sydney)

```bash
# Manual deploy
scp src/*.html deploy@209.38.86.222:/home/deploy/webremote/kaf/

# Check server
ssh deploy@209.38.86.222 "sudo systemctl status ezeo-otg"
```

Backend (ezeo_otg) is a separate repo, also auto-deploys on push.

## Key Documentation

- **[SCHEMA.md](docs/SCHEMA.md)** - Complete database schema, relationships, API examples
- **[ROADMAP.md](docs/ROADMAP.md)** - What's built, what's next (auth, Stripe, email campaigns)
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Server setup and deploy process

## Roadmap (Summary)

1. Email campaign sender (next)
2. Magic link auth / session management
3. Class browsing + registration improvements
4. Stripe payment integration
5. Deprecate Wix booking

See [ROADMAP.md](docs/ROADMAP.md) for details.
