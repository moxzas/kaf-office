# KAF Office - Start Here

For a project overview, see the root [README.md](../README.md).

## Key Documentation

| Document | What it covers |
|----------|----------------|
| [SCHEMA.md](SCHEMA.md) | Authoritative Airtable schema - all 9 tables, fields, relationships, API examples |
| [ROADMAP.md](ROADMAP.md) | Current state, target architecture, implementation order |
| [DEPLOYMENT.md](DEPLOYMENT.md) | How the frontend deploys, server details, troubleshooting |

## Codebase Quick Reference

**Frontend pages** (`src/`):
- `enrollment.html` - SurveyJS multi-step enrollment form. Supports create (`/enrollment.html`) and edit (`?parent={ID}`) modes. Calls Airtable directly for Parents/Students CRUD, calls ezeo_otg for audit + email.
- `classes.html` - Sophia's class admin. Create/edit classes, set venues/teachers/pricing, copy registration links. Supports term classes and holiday programs.
- `register.html` - Parent-facing registration. Loaded via `?class={ID}`. Parent enters email, selects children, creates Booking records.
- `enrollments.html` - Admin view/edit of existing enrollments. Sets `editedBy: "admin"` in audit trail.

**Scripts** (`scripts/`):
- `setup_classes.py` - Bootstraps Classes/Bookings/Venues/Attendance tables. Run with `create-tables` or `seed-venues`.
- `import_contacts.py` - One-time Wix CSV import to Contacts table.
- `reimport_contacts.py` - Re-import from `data/contacts_reimport.json` backup.

**Data** (`data/`, gitignored):
- `contacts.csv`, `bookings.csv` - Original Wix exports (PII)
- `contacts_reimport.json` - Backup of all 1,944 contact records

## Common Tasks

**Add/edit a class:** Sophia uses `classes.html` in the browser.

**Register a student for a class:** Sophia copies the registration link from `classes.html` and shares it. Parents open `register.html?class={ID}`.

**Edit an enrollment:** Use `enrollments.html` or edit directly in Airtable.

**Deploy frontend changes:** Push to `main`. GitHub Actions copies `src/*` to the server automatically.

**Inspect the Airtable schema:** `python scripts/inspect_actual.py`

## Historical Docs

Older phase-specific docs (Nov 2025 handovers, phase checklists, Flutter plans) are in [docs/archive/](archive/). They have historical context but don't reflect the current system.
