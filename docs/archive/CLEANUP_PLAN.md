# Cleanup Plan - Art & Craft School CRM

**Date:** 2025-11-05
**Base ID:** appNuMdxaiSYdgxJS

---

## 1. Airtable Base vs SCHEMA_V2.md Comparison

### Summary
The actual base is **90% aligned** with SCHEMA_V2.md but has a **custom Households table** design pattern that's actually an improvement over the schema. It deduplicates address data for families.

### Key Differences

#### ✅ Better Than Schema (Keep As-Is)
1. **Households Table** (not in schema)
   - Centralizes family addresses
   - Parents and Students lookup addresses from Households
   - Prevents duplicate address entry for siblings/families
   - **Recommendation:** Keep this design, update schema docs to reflect it

#### ⚠️ Missing Fields (Add These)
1. **Parents Table:**
   - Missing: `Created Date` (created time field)

2. **Students Table:**
   - Missing: `Primary Parent` (single link to Parents) - important for determining which parent's household to use
   - Missing: `Active Enrollments` (rollup count)
   - Missing: `Total Classes Attended` (rollup count)

3. **Teachers Table:**
   - Has extra: `Address`, `Suburb`, `Postcode` (not in schema, but useful)
   - Missing: `Active Classes Count` (rollup)

4. **Venues Table:**
   - Missing: `Active Classes Count` (rollup)

5. **Classes Table:**
   - Missing: `Revenue (Projected)` (formula: `{Current Enrollment} * {Price}`)

#### ℹ️ Schema Deviations (Intentional)
1. **Parents.Attendance** link exists (not in schema) - allows quick access from parent to attendance records
2. **Students.General Notes** instead of **Students.Notes** (minor naming difference)
3. Address fields in Parents/Students are **lookups from Households** instead of direct fields or lookups from Primary Parent

---

## 2. Documentation Cleanup Plan

### Files to KEEP (Active Documentation)
- ✅ `SCHEMA_V2.md` - Primary schema reference (needs update for Households)
- ✅ `VIEWS.md` - View configurations
- ✅ `IMPLEMENTATION_CHECKLIST.md` - Useful for tracking
- ✅ `START_HERE.md` - Navigation guide
- ✅ `QUICKSTART.md` - Build instructions
- ✅ `TODO.md` - Project tracking
- ✅ `sample_data/` directory - Test data

### Files to DELETE (Obsolete/Wrong)
- ❌ `README.md` - Generic, outdated (START_HERE is better)
- ❌ `SCHEMA.md` - Old version (V2 is current)
- ❌ `COMPARISON.md` - One-time analysis, no longer needed
- ❌ `MIGRATION.md` - Not migrating, starting fresh
- ❌ `ADD_HOUSEHOLDS.md` - Task already completed
- ❌ `MANUAL_FIXUP.md` - Historical fixes, no longer relevant
- ❌ `NEXT_SESSION.md` - Session notes, completed
- ❌ `RECREATE_FORMS.md` - One-time task docs
- ❌ `schema_inspection_app1MhJmZGREczxSx.json` - Old base dump
- ❌ `schema_inspection_appj6RU7hVn11srUi.json` - Old base dump

### Files to UPDATE
- 📝 `SCHEMA_V2.md` → Add Households table documentation
- 📝 `START_HERE.md` → Update to mention 8 tables (not 7)
- 📝 `QUICKSTART.md` → Update table count and Households workflow
- 📝 Create new `README.md` → Clean project overview for Flutter web app

---

## 3. Python Scripts Cleanup

### Scripts to KEEP
- ✅ `inspect_actual.py` - Useful for future schema checks
- ✅ `inspect_existing_base.py` - Reusable inspection tool
- ✅ `verify_base.py` - Validation tool
- ✅ `requirements.txt` - Dependencies

### Scripts to DELETE
- ❌ `setup_airtable.py` - One-time setup, base already exists
- ❌ `auto_build.py` - Build script for old setup
- ❌ `build_base.py` - Old base builder
- ❌ `check_forms.py` - One-time check
- ❌ `check_live_data.py` - Ad-hoc script
- ❌ `check_rollups.py` - Ad-hoc script
- ❌ `add_teacher_address.py` - One-time migration script
- ❌ `fix_via_api.py` - One-time fix script
- ❌ `data_summary.py` - Ad-hoc analysis

---

## 4. Non-Destructive Cleanup Steps

### Phase 1: Archive Before Deleting
```bash
# Create archive directory
mkdir archive_2025-11-05

# Move obsolete files (don't delete yet)
mv README.md SCHEMA.md COMPARISON.md MIGRATION.md archive_2025-11-05/
mv ADD_HOUSEHOLDS.md MANUAL_FIXUP.md NEXT_SESSION.md RECREATE_FORMS.md archive_2025-11-05/
mv schema_inspection_*.json archive_2025-11-05/
mv setup_airtable.py auto_build.py build_base.py archive_2025-11-05/
mv check_*.py add_teacher_address.py fix_via_api.py data_summary.py archive_2025-11-05/
```

### Phase 2: Update Active Docs
1. Update `SCHEMA_V2.md` to add Households table
2. Update `START_HERE.md` to reflect 8 tables
3. Update `QUICKSTART.md` with correct counts
4. Create new `README.md` for Flutter web project

### Phase 3: Create New Flutter Project Structure
```bash
# Option A: Create new Flutter project and move docs
cd ..
flutter create kaf_office_web
cd kaf_office_web
mkdir docs
cp ../KAF-Office/SCHEMA_V2.md docs/
cp ../KAF-Office/VIEWS.md docs/
cp -r ../KAF-Office/sample_data docs/
# Copy cleaned Python scripts
mkdir scripts
cp ../KAF-Office/inspect_actual.py scripts/
cp ../KAF-Office/inspect_existing_base.py scripts/
cp ../KAF-Office/verify_base.py scripts/
cp ../KAF-Office/requirements.txt scripts/
```

---

## 5. Recommended Next Steps

1. ✅ **Non-destructive cleanup** (archive old files)
2. ✅ **Update documentation** (SCHEMA_V2.md, START_HERE.md, etc.)
3. ✅ **Add missing Airtable fields** (rollups, formulas, Primary Parent)
4. ✅ **Initialize git repo** in current directory OR new Flutter project
5. ✅ **Create Flutter web project** structure
6. ✅ **Build Flutter web app** with Airtable integration

---

## 6. Airtable Fields to Add (Non-Destructive)

### Parents Table
- [ ] Add: `Created Date` (Created time field)

### Students Table
- [ ] Add: `Primary Parent` (Link to Parents, single link)
- [ ] Add: `Active Enrollments` (Rollup from Enrollments, COUNTA where Class→Status="Active")
- [ ] Add: `Total Classes Attended` (Rollup from Enrollments→Attendance Records, COUNTA where Status="Present")

### Teachers Table
- [ ] Add: `Active Classes Count` (Rollup from Classes, COUNTA where Status="Active")

### Venues Table
- [ ] Add: `Active Classes Count` (Rollup from Classes, COUNTA where Status="Active")

### Classes Table
- [ ] Add: `Revenue (Projected)` (Formula: `{Current Enrollment} * {Price}`)

---

## 7. Post-Cleanup File Structure

```
KAF-Office/  (or new Flutter project)
├── docs/
│   ├── SCHEMA_V2.md          # Updated with Households
│   ├── VIEWS.md
│   ├── IMPLEMENTATION_CHECKLIST.md
│   ├── START_HERE.md         # Updated
│   ├── QUICKSTART.md         # Updated
│   └── sample_data/
├── scripts/
│   ├── inspect_actual.py
│   ├── inspect_existing_base.py
│   ├── verify_base.py
│   └── requirements.txt
├── lib/                      # Flutter app code
├── web/                      # Flutter web assets
├── README.md                 # New Flutter project README
└── archive_2025-11-05/       # Old files (can delete after testing)
```

---

## Decision Point: Current Project vs New Flutter Project?

**Option A: Clean current project**
- Faster (30 mins)
- Keep git history (if any)
- Mix of web assets + Flutter

**Option B: New Flutter project**
- Clean start (1 hour)
- Proper Flutter structure
- Move only needed files

**Recommendation:** Option B - Create new Flutter project, it will be cleaner for web development.
