# Airtable Schema: KAF Art & Craft School CRM

**Base ID:** `appNuMdxaiSYdgxJS`
**Last Updated:** 2025-11-07
**Status:** Production (Live enrollment system)

---

## Overview

This is the **authoritative schema documentation** for the KAF enrollment system. It reflects the actual current Airtable structure as of November 7, 2025.

**What This System Does:**
- Online enrollment form for parents (SurveyJS at app.sonzai.com/kaf/enrollment.html)
- Student records with medical/dietary notes
- Audit trail of all enrollments and changes
- Email notifications to school owner and parents

**Database Architecture:**
- 8 tables in Airtable
- Direct API access from enrollment form (browser → Airtable)
- Audit logging via backend server (ezeo_otg)
- No complex build process, minimal dependencies

---

## Table Summary

| Table | Fields | Purpose |
|-------|--------|---------|
| **Parents** | 13 | Contact information, authorization |
| **Students** | 17 | Child details, medical notes, auto-generated IDs |
| **Audit Log** | 5 | Complete history of enrollments (JSON blobs) |
| **Venues** | 7 | Class locations (not used by enrollment form yet) |
| **Teachers** | 8 | Instructors (not used by enrollment form yet) |
| **Classes** | 17 | Class schedules (not used by enrollment form yet) |
| **Enrollments** | 24 | Student-class junction (not used by enrollment form yet) |
| **Attendance** | 10 | Session tracking (not used by enrollment form yet) |

**Note:** Only Parents, Students, and Audit Log are actively used by the current enrollment form. The other tables are legacy/planned for future features.

---

## 1. Parents Table

**Purpose:** Parent/guardian contact information and enrollment authorization.

**Used by:** Enrollment form (create/update), email notifications

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| **Name** | Single line text | ✅ | Parent/guardian full name (Primary field) |
| **Email** | Email | ✅ | Primary email address |
| **Mobile** | Phone number | ✅ | Mobile phone (accepts +61 format) |
| **Phone** | Phone number | | Home/work phone |
| **Address** | Single line text | ✅ | Street address (e.g., "123 Main St") |
| **Suburb** | Single line text | ✅ | Suburb/city (e.g., "Chapel Hill") |
| **Postcode** | Single line text | ✅ | Australian postcode (e.g., "4069") |
| **Authorized for Pickup** | Checkbox | | Can this person pick up students? |
| **Interest Categories** | Multiple select | | Interests: Pottery, Painting, Drawing, Sculpture, Mixed Media, Holiday Programs, After School Programs |
| **Interest Notes** | Long text | | Freeform notes about interests |
| **Communication Log** | Long text | | History of interactions |
| **Students** | Link to Students | | Children linked to this parent (auto-populated) |
| **Attendance** | Link to Attendance | | Attendance records where this parent was pickup person (auto-populated) |

**Key Relationships:**
- Parents (1) → (many) Students
- Parents can be linked as pickup person in Attendance records

**Form Behavior:**
- Create mode: POST new parent record on final submit
- Edit mode: PATCH existing parent record on final submit
- URL: `?parent={RECORD_ID}` to pre-fill form for editing

---

## 2. Students Table

**Purpose:** Individual student records with auto-generated IDs and medical information.

**Used by:** Enrollment form (create/update), email summaries

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| **Name** | Single line text | ✅ | Student full name (Primary field) |
| **Date of Birth** | Date | ✅ | Student DOB (format: YYYY-MM-DD for API) |
| **School** | Single select | ✅ | School/kindergarten name |
| **Year/Class** | Single line text | | Year level or class (e.g., "Year 3") |
| **Medical Notes** | Long text | | Allergies, conditions, medications |
| **Dietary Notes** | Long text | | Food allergies, restrictions |
| **Special Needs** | Long text | | Learning support requirements |
| **Student ID Number** | Auto number | | Sequential number (hidden) |
| **Student ID** | Formula | | Formatted ID: `"STU-" & RIGHT("000" & {Student ID Number}, 3)` → STU-001, STU-002... |
| **Age** | Formula | | Current age: `DATETIME_DIFF(TODAY(), {Date of Birth}, 'years')` |
| **Student Photo** | Attachment | | Photo for identification (not used by form yet) |
| **General Notes** | Long text | | Additional notes |
| **Parents** | Link to Parents | ✅ | Parent/guardian links (created by form) |
| **Enrollments** | Link to Enrollments | | Class enrollments (auto-populated, not used yet) |
| **Address** | Lookup | | From Parents → Address |
| **Suburb** | Lookup | | From Parents → Suburb |
| **Postcode** | Lookup | | From Parents → Postcode |

**School Options (Single Select):**
- Chapel Hill Art Studio
- Ironside State School
- St Lucia Kindergarten
- Yeronga State School
- Good News Lutheran School
- Other

**⚠️ Critical:** School field must use exact values from dropdown. Form uses dropdown to prevent validation errors.

**Key Formulas:**
- `Student ID`: `"STU-" & RIGHT("000" & {Student ID Number}, 3)`
- `Age`: `DATETIME_DIFF(TODAY(), {Date of Birth}, 'years')`

**Form Behavior:**
- Create mode: POST new student records on final submit
- Edit mode: PATCH existing students, POST new ones, DELETE removed ones
- Students are dynamically added via form panels

---

## 3. Audit Log Table

**Purpose:** Complete immutable history of all enrollment submissions and changes.

**Used by:** ezeo_otg server (`POST /api/kaf/audit`), troubleshooting, compliance

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| **Record ID** | Single line text | ✅ | Parent record ID, or "Incomplete" for page 1 only |
| **Record Type** | Single select | ✅ | Type of record (currently only "KAF Enrollment") |
| **Action** | Single select | ✅ | Created, Updated, Deleted, Incomplete |
| **Email** | Email | ✅ | Parent email address |
| **Data** | Long text | ✅ | Complete JSON blob with timestamp, before/after states |

**Action Options:**
- **Created** - New enrollment submitted
- **Updated** - Existing enrollment edited
- **Deleted** - Enrollment removed (not implemented yet)
- **Incomplete** - Page 1 filled but form not completed (for follow-up)

**⚠️ Manual Setup Required:** Add "Incomplete" option to Action field in Airtable UI.

**JSON Data Structure:**
```json
{
  "timestamp": "2025-11-07T00:53:48.191112",
  "recordType": "KAF Enrollment",
  "recordId": "recXXXXXXXXXXXXX",
  "action": "Created",
  "parentEmail": "parent@example.com",
  "parentName": "Parent Name",
  "before": null,
  "after": {
    "parent": {
      "Name": "...",
      "Email": "...",
      "Mobile": "...",
      "Address": "...",
      "Suburb": "...",
      "Postcode": "..."
    },
    "students": [
      {
        "Name": "...",
        "Date of Birth": "...",
        "School": "...",
        "Medical Notes": "..."
      }
    ],
    "authorizedPickup": [
      {
        "pickupName": "...",
        "pickupPhone": "...",
        "isEmergencyContact": true
      }
    ],
    "photoPermission": "Yes - child & artwork",
    "oshcCollection": true,
    "specialRequests": ""
  }
}
```

**Why JSON Blobs?**
- Future-proof: Works for any form, not just enrollment
- Complete history: Full snapshot of data at submission time
- No schema changes: Add new form fields without altering database
- Delta calculation: Can diff before/after states in code

**Querying:**
- Filter by Email to see all submissions from a parent
- Filter by Action to see only completed enrollments
- Parse JSON in code to extract specific fields

---

## 4. Venues Table

**Purpose:** Locations where classes are held (not currently used by enrollment form).

| Field Name | Type | Description |
|------------|------|-------------|
| **Name** | Single line text | Venue name (Primary field) |
| **Type** | Single select | School Rental, Home Studio |
| **Address** | Long text | Full street address |
| **Suburb** | Single line text | Suburb/city |
| **Capacity** | Number | Max students |
| **Contact/Access Notes** | Long text | Keycode, contact person, parking info |
| **Classes** | Link to Classes | Classes held at this venue (auto-populated) |

**Status:** Legacy/planned feature. Not integrated with enrollment form.

---

## 5. Teachers Table

**Purpose:** Instructor records (not currently used by enrollment form).

| Field Name | Type | Description |
|------------|------|-------------|
| **Name** | Single line text | Teacher full name (Primary field) |
| **Email** | Email | Contact email |
| **Phone** | Phone number | Contact phone |
| **Address** | Single line text | Home address |
| **Suburb** | Single line text | Suburb |
| **Postcode** | Single line text | Postcode |
| **Notes** | Long text | General notes |
| **Classes** | Link to Classes | Classes taught (auto-populated) |

**Status:** Legacy/planned feature. Not integrated with enrollment form.

---

## 6. Classes Table

**Purpose:** Class schedules and details (not currently used by enrollment form).

| Field Name | Type | Description |
|------------|------|-------------|
| **Name** | Single line text | Class name (Primary field) |
| **Type** | Single select | Term, Holiday Program |
| **Category** | Single select | Pottery, Painting, Drawing, Sculpture, Mixed Media |
| **Day of Week** | Single select | Monday - Sunday |
| **Start Time** | Single line text | e.g., "3:30 PM" |
| **Duration (mins)** | Number | Class length in minutes |
| **Sessions in Term** | Number | Total sessions (e.g., 10 for term) |
| **Price** | Currency | Class fee |
| **Capacity** | Number | Max students |
| **Status** | Single select | Active, Completed, Cancelled |
| **Term Start Date** | Date | First session date |
| **Term End Date** | Date | Last session date |
| **Venue** | Link to Venues | Class location |
| **Teachers** | Link to Teachers | Instructors (1-2 teachers) |
| **Enrollments** | Link to Enrollments | Student enrollments (auto-populated) |
| **Current Enrollment** | Count | Number of enrolled students |
| **Spots Remaining** | Formula | `{Capacity} - {Current Enrollment}` |

**Status:** Legacy/planned feature. Future: integrate class selection into enrollment form.

---

## 7. Enrollments Table

**Purpose:** Junction table linking students to classes (not currently used by enrollment form).

| Field Name | Type | Description |
|------------|------|-------------|
| **Enrollment Name** | Formula | Auto-generated name |
| **Enrollment ID** | Auto number | Sequential ID |
| **Student** | Link to Students | Which student |
| **Class** | Link to Classes | Which class |
| **Payment Status** | Single select | Paid, Pending, Partial, Overdue, Refunded |
| **Amount Paid** | Currency | Payment received |
| **Sessions Included** | Number | Number of sessions paid for |
| **Enrollment Date** | Date | When enrolled |
| **Emergency Contact 1 Name** | Single line text | Primary emergency contact |
| **Emergency Contact 1 Relationship** | Single line text | Relationship to student |
| **Emergency Contact 1 Phone** | Phone number | Emergency phone |
| **Emergency Contact 2 Name** | Single line text | Secondary emergency contact |
| **Emergency Contact 2 Relationship** | Single line text | Relationship |
| **Emergency Contact 2 Phone** | Phone number | Emergency phone |
| **Photo Permission** | Single select | Yes - child & artwork, Yes - artwork only, No photos |
| **Approved Pickup People** | Long text | Who can collect the student |
| **OSHC Collection** | Checkbox | Collect from after-school care? (Ironside SS only) |
| **Marketing Source** | Single select | How they found us |
| **Special Requests** | Long text | Parent requests/notes |
| **Additional Notes** | Long text | Internal notes |
| **Attendance Records** | Link to Attendance | Session attendance (auto-populated) |
| **Sessions Attended** | Rollup | Count of attended sessions |
| **Sessions Remaining** | Formula | `MAX(0, {Sessions Included} - {Sessions Attended})` |
| **Attendance Rate** | Formula | Percentage attendance |

**Status:** Legacy/planned feature. Currently, enrollment form captures emergency contacts and photo permissions but doesn't create Enrollment records yet. This is stored in Audit Log JSON blobs for now.

---

## 8. Attendance Table

**Purpose:** Individual session attendance tracking (not currently used by enrollment form).

| Field Name | Type | Description |
|------------|------|-------------|
| **Attendance ID** | Auto number | Sequential ID |
| **Enrollment** | Link to Enrollments | Which enrollment |
| **Date** | Date | Session date |
| **Status** | Single select | Present, Absent, Late, Excused |
| **Sign-in Time** | Date/time | When student arrived |
| **Sign-out Time** | Date/time | When student left |
| **Pickup Person** | Link to Parents | Who collected the student |
| **Notes** | Long text | Session notes |
| **Student** | Lookup | From Enrollment → Student |
| **Class** | Lookup | From Enrollment → Class |

**Status:** Legacy/planned feature. Future: teacher interface for marking attendance.

---

## Relationships Diagram

```
Parents (1) ←──→ (many) Students
                     │
                     └─→ Audit Log (logs all changes)

[Legacy/Planned:]
Students (many) ←──→ (many) Enrollments ←──→ (many) Classes
                               │                    │
                               │                    ├─→ Venues (1)
                               │                    └─→ Teachers (1-2)
                               │
                               └─→ (many) Attendance
                                        │
                                        └─→ Parents (pickup person)
```

**Active Relationships (Currently Used):**
- Parents → Students (one parent can have multiple children)
- Students → Parents (one child can have multiple guardians)
- Audit Log tracks all enrollment submissions (not linked via Airtable relationships)

**Inactive Relationships (For Future Features):**
- Everything involving Venues, Teachers, Classes, Enrollments, Attendance

---

## Key Design Decisions

### 1. No Households Table
**Previous plan:** Central Households table with address, Parents/Students lookup addresses.
**Current:** Address fields directly in Parents table.
**Why:** Simpler for enrollment form, fewer API calls, easier to understand.

### 2. JSON Blobs in Audit Log
**Alternative:** Structured fields for each enrollment detail.
**Current:** Complete snapshots as JSON in single "Data" field.
**Why:**
- Works for any future form (not enrollment-specific)
- No schema changes when adding form fields
- Complete immutable history
- Easy to compare before/after states

### 3. Direct Airtable API Calls from Browser
**Alternative:** Proxy all requests through backend server.
**Current:** Form calls Airtable directly for CRUD, server only for audit/email.
**Why:**
- Fast form submission (no proxy latency)
- Backend only for side effects (logging, emails)
- Airtable handles rate limiting and validation

### 4. School Field as Dropdown
**Previous:** Free text input.
**Current:** Dropdown with exact Airtable values.
**Why:** Airtable rejects invalid single-select values with 422 error. Dropdown prevents user error.

### 5. Save Only on Final Submit
**Previous:** Progressive saving after each page.
**Current:** All records created on final submit only.
**Why:**
- No orphan records if user abandons form
- Cleaner audit trail
- Matches user expectation ("Submit" means submit)
- Page 1 completion still tracked via Audit Log for follow-up

---

## API Usage Examples

### Create Parent
```bash
POST https://api.airtable.com/v0/appNuMdxaiSYdgxJS/Parents
{
  "records": [{
    "fields": {
      "Name": "Sarah Johnson",
      "Email": "sarah@example.com",
      "Mobile": "+61444555666",
      "Address": "123 Main St",
      "Suburb": "Chapel Hill",
      "Postcode": "4069",
      "Interest Categories": ["Painting", "After School Programs"]
    }
  }]
}
```

### Create Student
```bash
POST https://api.airtable.com/v0/appNuMdxaiSYdgxJS/Students
{
  "records": [{
    "fields": {
      "Name": "Emma Johnson",
      "Date of Birth": "2015-06-15",
      "School": "Ironside State School",
      "Year/Class": "Year 3",
      "Medical Notes": "Peanut allergy",
      "Parents": ["recPARENT_ID_HERE"]
    }
  }]
}
```

### Create Audit Log
```bash
POST https://api.airtable.com/v0/appNuMdxaiSYdgxJS/Audit%20Log
{
  "records": [{
    "fields": {
      "Record ID": "recPARENT_ID_HERE",
      "Record Type": "KAF Enrollment",
      "Action": "Created",
      "Email": "sarah@example.com",
      "Data": "{\"timestamp\":\"2025-11-07T10:30:00Z\",\"action\":\"Created\",...}"
    }
  }]
}
```

**Important:**
- Linked records use arrays: `"Parents": ["recXXXX"]`
- Single select values must match exactly (case-sensitive)
- Dates use ISO 8601 format: `YYYY-MM-DD`

---

## Migration Notes

**Changes from Original Schema Plan (Nov 5):**
1. ✅ Households table removed - addresses moved to Parents
2. ✅ Audit Log table added - not in original schema
3. ✅ School field confirmed as dropdown (was documented but form had bug)
4. ❌ Some rollup fields not implemented (Active Enrollments, Total Classes Attended)
5. ❌ Primary Parent field not implemented (not needed for current form)

**Breaking Changes:**
- None for current enrollment form
- Legacy tables (Classes, Enrollments, etc.) not actively used yet

---

## Validation Rules

### Parents Table
- Email must be valid email format
- At least one of Mobile or Phone should be provided (form requires Mobile)
- Address, Suburb, Postcode required by form

### Students Table
- Name required
- Date of Birth required (must be valid date)
- School must match dropdown options exactly
- Parents link required (at least one parent)

### Audit Log Table
- All fields required
- Data must be valid JSON string

---

## Usage Statistics (As of Nov 7, 2025)

**Active Tables:**
- Parents: 1 record (Test Test)
- Students: 1 record (Tom)
- Audit Log: 3 records (1 incomplete, 1 created, 1 test)

**Unused Tables:**
- Venues: 0 records
- Teachers: 0 records
- Classes: 0 records
- Enrollments: 0 records
- Attendance: 0 records

**Status:** Awaiting first real enrollments from Sophia's students.

---

## Future Enhancements

### Phase 4 (Planned)
1. **Class Selection** - Let parents choose which classes to enroll in
2. **Create Enrollment Records** - Link students to classes via Enrollments table
3. **Payment Integration** - Stripe or Square for online payment
4. **Parent Dashboard** - View enrollments, attendance, payments

### Phase 5 (Future)
1. **Teacher Interface** - Mark attendance, view class rosters
2. **Automated Emails** - Class reminders, payment reminders
3. **Photo Gallery** - Upload class photos to Airtable
4. **Reports** - Attendance rates, revenue by class, enrollment trends

---

## Support & Maintenance

**Live System:** https://app.sonzai.com/kaf/enrollment.html
**Airtable Base:** https://airtable.com/appNuMdxaiSYdgxJS
**Documentation:** `/docs/SESSION_HANDOVER_2025-11-07.md`

**Key Contacts:**
- School Owner: Sophia (kidsartfun@gmail.com)
- Developer: Anthony Lee (anthony.f.lee@gmail.com)

**Emergency Procedures:**
- Form down: Check GitHub Pages deployment status
- Server down: SSH to 209.38.86.222, restart ezeo-otg service
- Emails not sending: Check Resend dashboard, verify API key

---

**Last Updated:** 2025-11-07
**Schema Version:** 1.0 (Production)
