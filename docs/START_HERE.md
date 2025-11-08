# KAF Office - Start Here

Welcome to the KAF Art & Craft School Enrollment System!

## 🎯 Quick Status

**✅ System Live:** https://app.sonzai.com/kaf/enrollment.html
**📊 Database:** Airtable (appNuMdxaiSYdgxJS)
**🚀 Status:** Phase 3 Complete - Ready for Sophia's Feedback

## 📖 Navigation for New Developers

### Essential Reading (Start Here!)
1. **SESSION_HANDOVER_2025-11-07.md** ⭐ **READ THIS FIRST**
   - Complete current status
   - Architecture overview
   - Known issues and fixes
   - Troubleshooting guide

### Implementation Documentation
2. **PHASE_2_COMPLETE.md** - Edit mode feature documentation
3. **PHASE_3_TODO.md** - Phase 3 completion checklist
4. **PHASE_3_SETUP.md** - Audit trail and email setup details

### Database Schema
5. **SCHEMA.md** - Complete Airtable schema (authoritative, updated Nov 7)

### Historical Context (Optional)
6. **HANDOVER.md** - Original Flutter plan (Nov 5) - *Outdated, we pivoted to SurveyJS*
7. **archive_schema_2025-11-07/** - Old schema versions (local only, not in git)

## 🏗️ What Was Built

### Frontend: SurveyJS Enrollment Form
- **File:** `/src/enrollment.html`
- **Live URL:** https://app.sonzai.com/kaf/enrollment.html
- **Features:**
  - 5-page multi-step form
  - Direct Airtable integration
  - Edit mode via `?parent={RECORD_ID}` URLs
  - Client-side validation

### Backend: Dart/Shelf Server (ezeo_otg)
- **Repo:** https://github.com/moxzas/ezeo_otg
- **Location:** `/packages/server/lib/handlers/kaf/`
- **Endpoint:** `POST /api/kaf/audit`
- **Features:**
  - Audit logging with JSON blobs
  - Email notifications via Resend
  - Deployed to VPS via GitHub Actions

### Database: Airtable
- **Base ID:** appNuMdxaiSYdgxJS
- **Tables:** Parents, Students, Audit Log
- **Note:** Households table was removed (addresses now in Parents)

## 🔧 Critical Information

### Deployment
```bash
# Frontend (KAF-Office)
git push origin main  # Auto-deploys to GitHub Pages

# Backend (ezeo_otg)
git push origin main  # Auto-deploys to app.sonzai.com via SSH

# Check deployment status
gh run list --limit 1
```

### Environment Variables
- `AIRTABLE_API_KEY` - Hardcoded in enrollment.html (line ~20)
- `AIRTABLE_BASE_ID` - Hardcoded in enrollment.html (line ~21)
- Server gets these via GitHub Secrets → systemd environment

### Access
- **Airtable:** https://airtable.com/appNuMdxaiSYdgxJS
- **Resend:** https://resend.com/emails
- **Server:** `ssh deploy@209.38.86.222`
- **Repos:**
  - KAF-Office: https://github.com/moxzas/kaf-office
  - ezeo_otg: https://github.com/moxzas/ezeo_otg

## ⚠️ Known Issues & Next Steps

### Immediate Action Required
1. **Add "Incomplete" to Audit Log Action field** (2 min manual task)
   - Go to Airtable → Audit Log table
   - Edit "Action" field → Add "Incomplete" option

### Awaiting Feedback
2. Get Sophia's feedback on form UX
3. Monitor first real enrollments for issues

### Future Enhancements
- Email domain setup (replace onboarding@resend.dev)
- PDF enrollment summaries
- SMS notifications
- Class scheduling integration

## 🐛 Recent Bug Fixes (Nov 7)

### Student Records Not Being Created
**Problem:** School field accepted invalid values (e.g., "ISS")
**Fix:** Changed to dropdown with valid Airtable options
**Commits:** `f4b270e`, `ce984c1`

### Silent Error Handling
**Problem:** Student creation failures were swallowed
**Fix:** Added error logging and exception throwing
**Commit:** `f4b270e`

## 🧪 Testing Commands

```bash
# Test form
open https://app.sonzai.com/kaf/enrollment.html

# Check server status
ssh deploy@209.38.86.222 "sudo systemctl status ezeo-otg"

# Watch server logs
ssh deploy@209.38.86.222 "sudo journalctl -u ezeo-otg -f | grep -i kaf"

# Check recent audit logs
python3 -c "
import urllib.request, json
url = 'https://api.airtable.com/v0/appNuMdxaiSYdgxJS/Audit%20Log?maxRecords=5'
req = urllib.request.Request(url, headers={'Authorization': 'Bearer patYJhlgK2q6sAnyZ...'})
with urllib.request.urlopen(req) as r:
    print(json.dumps(json.loads(r.read()), indent=2))
"
```

## 📚 Architecture Summary

```
┌─────────────────────────────────────────────────┐
│  Browser (app.sonzai.com/kaf/enrollment.html)  │
│  - SurveyJS form                                │
│  - Direct Airtable API calls (CRUD)            │
└─────────────────┬───────────────────────────────┘
                  │
                  ├──→ Airtable API (Parents, Students)
                  │
                  └──→ ezeo_otg Server (/api/kaf/audit)
                        │
                        ├──→ Airtable (Audit Log)
                        └──→ Resend API (Emails)
```

## 🎯 Current Status (Nov 7, 2025)

### ✅ Complete
- [x] Phase 1: Basic enrollment form
- [x] Phase 2: Editable enrollments
- [x] Phase 3: Audit trail + email notifications
- [x] Critical bug fixes (school validation, error logging)
- [x] End-to-end testing
- [x] Production deployment

### 🚧 In Progress
- [ ] Sophia's feedback collection
- [ ] Add "Incomplete" option to Audit Log

### 📋 Backlog
- [ ] Email domain setup
- [ ] PDF enrollment summaries
- [ ] Class scheduling integration
- [ ] Payment processing

---

**Last Updated:** 2025-11-07
**Next Session:** Collect Sophia's feedback and iterate on UX

**Questions?** See `SESSION_HANDOVER_2025-11-07.md` for complete details.
