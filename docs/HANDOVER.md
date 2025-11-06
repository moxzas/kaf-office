# Project Handover Document - KAF Art & Craft School CRM

**Date:** 2025-11-05
**For:** New Flutter Web Project
**Airtable Base ID:** `appNuMdxaiSYdgxJS`
**API Key Location:** See `inspect_actual.py:6` (or set as environment variable)

---

## 🎯 Project Overview

This is a **Flutter web application** for managing a small art & craft school in Australia. The backend is **Airtable**, which serves as both database and admin interface. The Flutter web app will be the parent-facing enrollment and student management portal.

**Business Model:**
- Small art/craft school teaching primary school children
- Runs term-based classes (10 weeks) and holiday programs (1 week)
- Categories: Pottery, Painting, Drawing, Sculpture, Mixed Media
- Locations: Mix of school venue rentals and home studio
- Australian-specific features: OSHC (Outside School Hours Care) collection, local schools

---

## 📊 Current State Summary

### ✅ What's Complete

1. **Airtable Base Structure (90% Complete)**
   - 8 tables fully set up with relationships
   - Auto-numbering for Student IDs and Enrollment IDs working
   - Formula fields, rollups, and lookups configured
   - **Empty database** - no real data yet, ready for first enrollments

2. **Documentation**
   - Complete schema documentation (SCHEMA_V2.md)
   - View configurations (VIEWS.md)
   - Implementation checklist for tracking
   - Sample data for testing

3. **Cleanup**
   - Old/obsolete files archived in `archive_2025-11-05/`
   - Only active, necessary files remain

### 🚧 What's Needed

1. **Airtable Field Additions** (Minor - 5 fields missing, see section below)
2. **Flutter Web App** (Not started)
   - Parent enrollment flow
   - Student management
   - Attendance tracking interface
   - Payment tracking

---

## 🗄️ Airtable Schema Overview

### The 8 Tables

1. **Parents** (14 fields)
   - Contact info, authorized pickup flag
   - Links to Households for address lookup
   - Interest tracking for marketing

2. **Students** (18 fields)
   - Auto-generated Student ID (STU-001, STU-002...)
   - Medical/dietary notes
   - Links to Parents and Households
   - Age calculated from DOB

3. **Venues** (7 fields)
   - Schools and home studio locations
   - Capacity tracking

4. **Teachers** (8 fields)
   - Instructor contact info
   - Address fields included

5. **Classes** (17 fields)
   - Term/Holiday type
   - Day, time, duration
   - Capacity and enrollment tracking
   - Price and revenue formulas

6. **Enrollments** (24 fields)
   - Junction table: Student ↔ Class
   - Payment tracking (Paid, Pending, Overdue, etc.)
   - Emergency contacts (2 contacts per enrollment)
   - Photo permissions (Yes with child, artwork only, no photos)
   - OSHC collection flag
   - Marketing source tracking

7. **Attendance** (10 fields)
   - Individual session attendance records
   - Sign-in/sign-out times
   - Pickup person tracking
   - Status: Present, Absent, Late, Excused

8. **Households** (7 fields) ⭐
   - **Custom addition not in original schema**
   - Centralizes family addresses
   - Parents and Students lookup addresses from here
   - Prevents duplicate entry for siblings/families

### Key Relationships

```
Households (1) ←→ (many) Parents
                     ↓
                 (many) Students
                     ↓
                 (many) Enrollments (junction) ←→ (many) Classes
                     ↓                              ↑
                 (many) Attendance              Teachers (1-2)
                     ↓                              ↑
              Pickup Person (Parents)           Venues (1)
```

### Important Design Patterns

1. **Households Table**
   - Parents.Address, Parents.Suburb, Parents.Postcode = Lookup from Households
   - Students.Address, Students.Suburb, Students.Postcode = Lookup from Households
   - This allows multiple parents/students at same address to share one record
   - Better than the original schema which duplicated addresses

2. **Auto-Numbering**
   - Students.Student ID Number (auto number) → Students.Student ID (formula)
   - Formula: `"STU-" & RIGHT("000" & {Student ID Number}, 3)`
   - Same pattern for Enrollments (auto number → formatted ID)

3. **Emergency Contacts**
   - Stored in Enrollments table (not Students)
   - Allows different emergency contacts per class enrollment
   - Fields: Name, Relationship, Phone (× 2 contacts)

4. **Pickup Authorization**
   - Parents.Authorized for Pickup (checkbox)
   - Attendance.Pickup Person (link to Parents)
   - Validates only authorized people are collecting children

---

## 📋 Missing Airtable Fields (To Add)

These fields are documented in SCHEMA_V2.md but not yet added to the live base:

### Parents Table
- [ ] `Created Date` (Created time field) - Auto-tracks when parent record was created

### Students Table
- [ ] `Primary Parent` (Link to Parents, single link) - Determines which parent's household to use for address
- [ ] `Active Enrollments` (Rollup) - Count of enrollments where Class→Status="Active"
- [ ] `Total Classes Attended` (Rollup) - Count from Enrollments→Attendance Records where Status="Present"

### Teachers Table
- [ ] `Active Classes Count` (Rollup) - Count from Classes where Status="Active"

### Venues Table
- [ ] `Active Classes Count` (Rollup) - Count from Classes where Status="Active"

### Classes Table
- [ ] `Revenue (Projected)` (Formula) - `{Current Enrollment} * {Price}`

**Note:** These are nice-to-haves, not blockers. The base is functional without them.

---

## 📁 Files to Move to New Flutter Project

### Essential Documentation (Move to `docs/`)
```
SCHEMA_V2.md                    # PRIMARY REFERENCE - Complete field specs
VIEWS.md                        # Airtable view configurations
IMPLEMENTATION_CHECKLIST.md     # Field tracking checklist
START_HERE.md                   # Navigation guide
QUICKSTART.md                   # Manual setup instructions
TODO.md                         # Project tracking
CLEANUP_PLAN.md                 # This cleanup's details
HANDOVER.md                     # This file
```

### Python Scripts (Move to `scripts/`)
```
inspect_actual.py               # Quick schema inspection (has hardcoded API key!)
inspect_existing_base.py        # Detailed schema inspector
verify_base.py                  # Validation tool
requirements.txt                # pyairtable>=2.3.0, requests>=2.31.0
```

### Sample Data (Move to `docs/sample_data/`)
```
sample_data/
├── parents.csv
├── students.csv
├── venues.csv
├── teachers.csv
├── classes.csv
├── enrollments.csv
└── attendance.csv
```

### Optional (Reference Only)
```
CUSTOM_APPS_PLAN.md            # Ideas for custom Airtable apps
archive_2025-11-05/            # Old files (can delete after confirming Flutter app works)
```

### DO NOT Move (Old Web Project Artifacts)
```
node_modules/                  # Node.js dependencies (not needed for Flutter)
package.json, package-lock.json
webpack.*.js                   # Old build configs
css/, js/, img/                # Old web assets
index.html, 404.html           # Old HTML
favicon.ico, icon.*, site.webmanifest, robots.txt
.editorconfig, .gitattributes  # (Can recreate for Flutter project)
```

---

## 🔑 Critical Information

### Airtable API Access

**Base ID:** `appNuMdxaiSYdgxJS`

**API Key:**
- Currently hardcoded in `inspect_actual.py` line 6 (⚠️ remove before committing!)
- Generate new token: https://airtable.com/create/tokens
- Required scopes: `data.records:read`, `data.records:write`, `schema.bases:read`

**API Endpoint Pattern:**
```
GET  https://api.airtable.com/v0/meta/bases/{baseId}/tables
GET  https://api.airtable.com/v0/{baseId}/{tableName}
POST https://api.airtable.com/v0/{baseId}/{tableName}
```

**Table IDs (from inspect_actual.py output):**
- Run `python3 scripts/inspect_actual.py` to get current IDs
- Table IDs change if tables are recreated

### Australian-Specific Features

1. **OSHC Collection** (Enrollments.OSHC Collection)
   - "Outside School Hours Care" - after-school childcare program
   - Only for Ironside State School venue
   - If checked, teacher collects child from OSHC, not classroom

2. **Schools List** (Students.School dropdown)
   - Chapel Hill Art Studio
   - Ironside State School
   - St Lucia Kindergarten
   - Yeronga State School
   - Good News Lutheran
   - Other

3. **Address Format**
   - Address (street)
   - Suburb (not "city")
   - Postcode (4 digits, e.g., "4101")

### Payment Workflow

**Status Options:**
- Paid - Full payment received
- Pending - Awaiting payment
- Partial - Some payment received
- Overdue - Payment past due
- Refunded - Money returned

**Fields:**
- Enrollments.Payment Status (dropdown)
- Enrollments.Amount Paid (currency)
- Classes.Price (currency)
- Enrollments.Sessions Included (number)

### Photo Permissions

**Options:**
- "Yes - child & artwork" - Can photograph child and their work
- "Yes - artwork only" - Only photograph the artwork, not the child
- "No photos" - No photography allowed

**Field:** Enrollments.Photo Permission

---

## 🎨 Flutter Web App Requirements

### User Stories (Priority Order)

#### Phase 1: Parent Enrollment Flow
1. **As a parent, I want to browse available classes**
   - Filter by: Category (Pottery, Painting, etc.), Type (Term/Holiday), Day of Week
   - Show: Class name, time, venue, spots remaining, price
   - Mark full classes clearly

2. **As a parent, I want to enroll my child**
   - Step 1: Enter parent contact info (or login if returning)
   - Step 2: Add/select student info (DOB, school, medical notes)
   - Step 3: Select class(es) to enroll in
   - Step 4: Enter emergency contacts
   - Step 5: Set photo permissions
   - Step 6: Submit (creates records in Airtable)

3. **As a parent, I want to view my enrollments**
   - See all my children's current enrollments
   - View attendance history
   - Check payment status

#### Phase 2: Admin Functions
4. **As an admin, I want to mark attendance**
   - Daily roll call interface
   - Filter students by today's classes
   - Mark: Present, Absent, Late, Excused
   - Record sign-in/sign-out times
   - Track pickup person

5. **As an admin, I want to track payments**
   - View all enrollments by payment status
   - Update payment status and amount paid
   - Generate payment reminder lists

#### Phase 3: Reporting
6. **As an admin, I want to see reports**
   - Enrollment numbers by class
   - Revenue by term/category
   - Attendance rates
   - Students with medical notes

### Technical Architecture Recommendations

**State Management:**
- Riverpod or Provider for state management
- Cache Airtable data locally, refresh periodically

**Airtable Integration:**
- Use `http` package for API calls
- Consider creating a `AirtableService` class
- Handle pagination (Airtable returns max 100 records per request)
- Implement rate limiting (5 requests/sec per base)

**Authentication:**
- Start simple: Email/password stored in Parents table
- Later: Proper auth (Firebase, Auth0, etc.)
- Or: Unique enrollment link sent via email (no login needed)

**Responsive Design:**
- Mobile-first (parents on phones)
- Desktop admin interface
- Material Design 3

**Offline Support:**
- Cache class list locally
- Queue enrollment submissions if offline
- Sync when connection restored

---

## 🚀 Next Steps for Flutter Developer

### Immediate Tasks

1. **Set Up Flutter Project**
   ```bash
   flutter create kaf_office_web
   cd kaf_office_web
   ```

2. **Move Documentation**
   ```bash
   mkdir docs
   cp ../KAF-Office/SCHEMA_V2.md docs/
   cp ../KAF-Office/VIEWS.md docs/
   cp -r ../KAF-Office/sample_data docs/
   # ... etc
   ```

3. **Configure Airtable API**
   - Create `.env` file (add to `.gitignore`)
   - Store `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID`
   - Use `flutter_dotenv` package

4. **Create Airtable Service**
   ```dart
   class AirtableService {
     static const baseId = 'appNuMdxaiSYdgxJS';

     Future<List<Class>> getClasses({String? status}) async {
       // GET /v0/{baseId}/Classes?filterByFormula=...
     }

     Future<void> createEnrollment(Enrollment enrollment) async {
       // POST /v0/{baseId}/Enrollments
     }
   }
   ```

5. **Build Core Models**
   ```dart
   class Parent { ... }
   class Student { ... }
   class SchoolClass { ... } // "Class" is reserved keyword
   class Enrollment { ... }
   class Attendance { ... }
   ```

6. **Implement MVP**
   - Simple class listing page
   - Basic enrollment form
   - Test with Airtable API

### Testing Strategy

1. **Use Sample Data**
   - Import `sample_data/*.csv` into Airtable
   - Test enrollment flow
   - Verify records created correctly

2. **Test Cases**
   - Enroll student in multiple classes
   - Create parent with multiple students (same household)
   - Test payment status updates
   - Mark attendance and track pickup

3. **Edge Cases**
   - Class at capacity (should prevent enrollment)
   - Missing emergency contacts (should warn)
   - Unauthorized pickup person (should flag)

---

## 📖 Key Documentation References

### Airtable Schema Details
- **Full spec:** `SCHEMA_V2.md` - Every field, every formula, every relationship
- **Views:** `VIEWS.md` - How to filter/sort/group data
- **Checklist:** `IMPLEMENTATION_CHECKLIST.md` - Track what's built

### Formula Examples (from SCHEMA_V2.md)

**Student ID:**
```
"STU-" & RIGHT("000" & {Student ID Number}, 3)
```

**Spots Remaining:**
```
{Capacity} - {Current Enrollment}
```

**Attendance Rate:**
```
IF({Sessions Included} > 0,
   ROUND({Sessions Attended} / {Sessions Included} * 100, 1) & "%",
   "N/A")
```

**Sessions Remaining:**
```
MAX(0, {Sessions Included} - {Sessions Attended})
```

### Common Workflows (from SCHEMA_V2.md)

**Enroll a Student:**
1. Find/create Parent → Household
2. Create Student → link to Parent, Household
3. Find target Class
4. Create Enrollment → link Student, Class, set emergency contacts, photo permission
5. Set payment status

**Daily Roll Call:**
1. Filter today's classes
2. For each enrolled student → create Attendance record
3. Mark status (Present/Absent/Late)
4. Record sign-in time
5. When picked up → link Pickup Person, record sign-out time

---

## ⚠️ Important Gotchas

### 1. Households Table Design
- **Not in original schema docs** but implemented in live base
- Parents/Students don't have direct address fields
- They lookup addresses from Households
- When creating a student, link to parent's Household

### 2. Single Select Field Values Must Match Exactly
Airtable API requires exact matches for dropdown values:

**Classes.Status:**
- ✅ "Active"
- ❌ "active" (won't work)

**Payment Status:**
- ✅ "Paid", "Pending", "Partial", "Overdue", "Refunded"

**Photo Permission:**
- ✅ "Yes - child & artwork"
- ✅ "Yes - artwork only"
- ✅ "No photos"

### 3. Linked Records Use Record IDs
When creating enrollment via API:
```json
{
  "fields": {
    "Student": ["recXXXXXXXXXXXXXX"],  // Array of record IDs
    "Class": ["recYYYYYYYYYYYYYY"]
  }
}
```

### 4. Airtable API Pagination
Max 100 records per request. Use `offset` parameter:
```
GET /v0/{baseId}/Classes?pageSize=100&offset=recXXX
```

### 5. Rate Limits
5 requests per second per base. Implement throttling in Flutter app.

### 6. Date Formats
- Airtable expects: `YYYY-MM-DD` for Date fields
- DateTime fields: ISO 8601 format `2025-01-21T14:30:00.000Z`

---

## 🔐 Security Considerations

### API Key Management
- ⚠️ **Never commit API key to git**
- Use environment variables
- Regenerate key if exposed

### Parent Data Access
- Parents should only see their own students' data
- Implement authentication to filter by parent
- Use Airtable's filtered views or API filterByFormula

### Payment Information
- Sensitive data (Amount Paid)
- Consider limiting exposure in parent-facing views
- Admin-only access for payment management

---

## 📞 Business Context

**Owner:** Sophia (art teacher, runs the school)
**Location:** Brisbane, Australia (Chapel Hill area)
**Scale:** Small business, ~20-50 students per term
**Classes:** After-school (3:30-5pm), weekends, holiday programs
**Venues:** Mix of rented school spaces + home studio

**Current Pain Points:**
1. Manual enrollment (phone/email)
2. Paper roll call
3. Payment tracking in spreadsheets
4. Parent communications scattered

**Goal:** Simple web app for parents to enroll, teachers to track attendance, admin to manage payments

---

## 🎯 Success Criteria

### MVP Definition
- [ ] Parents can browse classes and see spots available
- [ ] Parents can enroll a child with full information (emergency contacts, permissions)
- [ ] Admin can mark daily attendance
- [ ] Admin can update payment status
- [ ] All data syncs to/from Airtable

### Nice-to-Haves (Phase 2)
- [ ] Parent login to view their enrollments
- [ ] Automated email confirmations
- [ ] Photo gallery upload per class
- [ ] Attendance reports
- [ ] Payment reminder emails

---

## 📚 Additional Resources

**Airtable API Docs:**
- https://airtable.com/developers/web/api/introduction
- https://airtable.com/developers/web/api/authentication

**Flutter Packages:**
- `http` - API calls
- `flutter_dotenv` - Environment variables
- `provider` or `riverpod` - State management
- `intl` - Date formatting

**Sample Data:**
- Located in `docs/sample_data/`
- Import to Airtable for testing
- Includes realistic Australian names, schools, addresses

---

## 📝 Change Log

**2025-11-05:**
- Initial project analysis
- Airtable base inspection (appNuMdxaiSYdgxJS)
- Compared live base vs SCHEMA_V2.md (90% match)
- Archived obsolete files (20 files to `archive_2025-11-05/`)
- Identified 5 missing fields (non-critical)
- Created handover documentation
- Ready for Flutter web development

**Next:** Create Flutter project, move files, begin development

---

## 🤝 Questions for New Developer

When starting, please verify:

1. Can you access the Airtable base? (appNuMdxaiSYdgxJS)
2. Do you have a valid API key with correct scopes?
3. Have you run `python3 scripts/inspect_actual.py` to confirm current schema?
4. Is the base still empty (no real enrollment data yet)?
5. Should we add the 5 missing fields now, or work around them?

**Contact:** Anthony Lee (original project owner)

---

**Good luck with the Flutter build! All the schema work is done, database is ready, just needs a beautiful web interface. 🎨**
