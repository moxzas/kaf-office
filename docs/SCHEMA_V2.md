# Airtable Schema V2: Art & Craft School CRM

## Overview
This schema supports a small art/craft school running term-based and holiday classes for primary school children. It tracks students, enrollments, attendance, parent communications, and venue/teacher logistics.

**Version 2 Updates:**
- Incorporates best features from existing base (app1MhJmZGREczxSx)
- Adds Student ID, Emergency Contacts, Photo Permission, Marketing tracking
- Maintains normalized structure for data integrity

---

## Tables & Fields

### 1. Parents

**Purpose:** Contact information for parents/guardians, including interest tracking and authorization for student pickup.

| Field Name | Type | Description | Notes |
|------------|------|-------------|-------|
| Name | Single line text | Parent/guardian full name | Primary field |
| Email | Email | Primary email address | |
| Phone | Phone number | Home/work phone | |
| Mobile | Phone number | Mobile phone | |
| Address | Single line text | Street address | |
| Suburb | Single line text | Suburb/city | |
| Postcode | Single line text | Postcode | |
| Students | Link to Students | Children linked to this parent | Multiple links allowed |
| Authorized for Pickup | Checkbox | Can this person pick up students? | Default: checked |
| Interest Categories | Multiple select | Structured interests | Options: Pottery, Painting, Drawing, Sculpture, Mixed Media, Holiday Programs, After School Programs |
| Interest Notes | Long text | Freeform notes from calls/emails/SMS | Track conversations about interests |
| Communication Log | Long text | History of interactions | Timestamped notes |
| Created Date | Created time | When record was added | Auto-populated |

**Key Formulas:**
- `Student Count`: `COUNTA({Students})`
- `Student Names`: `ARRAYJOIN({Students}, ", ")`

---

### 2. Students

**Purpose:** Individual student records with medical/dietary info and enrollment history.

| Field Name | Type | Description | Notes |
|------------|------|-------------|-------|
| Student ID Number | Auto number | Unique sequential number | Hidden field for formula |
| Student ID | Formula | Custom student identifier | `"STU-" & RIGHT("000" & {Student ID Number}, 3)` → STU-001, STU-002... |
| Name | Single line text | Student full name | Primary field |
| Date of Birth | Date | Student DOB | Format: DD/MM/YYYY |
| Age | Formula | Current age in years | `DATETIME_DIFF(TODAY(), {Date of Birth}, 'years')` |
| Primary Parent | Link to Parents | Main contact parent | Single link, required |
| Parents | Link to Parents | All parent/guardian contacts | Multiple links allowed |
| Address | Lookup | Student's home address | From Primary Parent → Address |
| Suburb | Lookup | Suburb | From Primary Parent → Suburb |
| Postcode | Lookup | Postcode | From Primary Parent → Postcode |
| School | Single select | School/kindergarten name | Options: Chapel Hill Art Studio, Ironside State School, St Lucia Kindergarten, Yeronga State School, Good News Lutheran, Other |
| Year/Class | Single line text | Year level or class name | E.g., "Year 3", "Magpie 2" |
| Medical Notes | Long text | Allergies, conditions, medications | Important for teacher visibility |
| Dietary Notes | Long text | Food allergies, restrictions | For classes involving snacks |
| Special Needs | Long text | Learning support requirements | E.g., ADHD, autism, movement breaks |
| Student Photo | Attachment | Photo for identification | Uploaded during enrollment |
| Notes | Long text | General notes | |
| Enrollments | Link to Enrollments | All class enrollments | Automatically populated |
| Active Enrollments | Rollup | Count of active enrollments | `COUNTA(values)` where Enrollments → Class → Status = "Active" |
| Total Classes Attended | Rollup | All-time attendance count | `COUNTA(values)` from Enrollments → Attendance Records where Status = "Present" |

**Key Formulas:**
- `Student ID`: `"STU-" & RIGHT("000" & {Student ID Number}, 3)`
- `Age`: `DATETIME_DIFF(TODAY(), {Date of Birth}, 'years')`
- `Has Medical Notes`: `IF(OR({Medical Notes}, {Dietary Notes}, {Special Needs}), "⚠️ Medical", "")`
- `Primary Contact`: `ARRAYJOIN({Primary Parent}, "")`

---

### 3. Venues

**Purpose:** Locations where classes are held (school rentals and home studio).

| Field Name | Type | Description | Notes |
|------------|------|-------------|-------|
| Name | Single line text | Venue name | Primary field |
| Type | Single select | Venue type | Options: School Rental, Home Studio |
| Address | Long text | Full street address | |
| Suburb | Single line text | Suburb/city | For grouping |
| Capacity | Number | Max students | |
| Contact/Access Notes | Long text | Keycode, contact person, parking, etc. | For teacher reference |
| Classes | Link to Classes | Classes held here | Automatically populated |
| Active Classes Count | Rollup | Number of active classes | `COUNTA(values)` where Classes → Status = "Active" |

---

### 4. Teachers

**Purpose:** Instructors who teach classes.

| Field Name | Type | Description | Notes |
|------------|------|-------------|-------|
| Name | Single line text | Teacher full name | Primary field |
| Email | Email | Contact email | |
| Phone | Phone number | Contact phone | |
| Classes | Link to Classes | Classes taught | Automatically populated |
| Active Classes Count | Rollup | Current active classes | `COUNTA(values)` where Classes → Status = "Active" |
| Notes | Long text | Qualifications, preferences | |

---

### 5. Classes

**Purpose:** Individual class offerings (term-based or holiday programs).

| Field Name | Type | Description | Notes |
|------------|------|-------------|-------|
| Name | Single line text | Class name | Primary field. E.g., "Pottery Term 1 2025" |
| Type | Single select | Class type | Options: Term, Holiday |
| Category | Single select | Art/craft category | Options: Pottery, Painting, Drawing, Sculpture, Mixed Media, General Craft |
| Venue | Link to Venues | Location | Single link |
| Teachers | Link to Teachers | Instructor(s) | 1-2 teachers typically |
| Day of Week | Single select | Class day | Options: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday |
| Start Time | Single line text | Class start time | Format: "3:30 PM" |
| Duration (mins) | Number | Class length in minutes | Typically 60-90 |
| Term Start Date | Date | First class date | |
| Term End Date | Date | Last class date | |
| Sessions in Term | Number | Total sessions | For term classes only |
| Price | Currency | Enrollment cost | Per term or per session |
| Capacity | Number | Max students | |
| Status | Single select | Current status | Options: Active, Inactive, Full, Cancelled |
| Enrollments | Link to Enrollments | Student enrollments | Automatically populated |
| Current Enrollment | Rollup | Number enrolled | `COUNTA(values)` from Enrollments |
| Spots Remaining | Formula | Available spots | `{Capacity} - {Current Enrollment}` |
| Revenue (Projected) | Formula | Total potential revenue | `{Current Enrollment} * {Price}` |

**Key Formulas:**
- `Spots Remaining`: `{Capacity} - {Current Enrollment}`
- `Status Indicator`: `IF({Current Enrollment} >= {Capacity}, "🔴 Full", IF({Current Enrollment} > {Capacity} * 0.8, "🟡 Almost Full", "🟢 Available"))`
- `Schedule`: `{Day of Week} & " " & {Start Time} & " (" & {Duration (mins)} & " mins)"`

---

### 6. Enrollments

**Purpose:** Junction table linking students to classes, tracking payment, permissions, and emergency contacts.

| Field Name | Type | Description | Notes |
|------------|------|-------------|-------|
| Enrollment ID | Auto number | Unique identifier | Primary field |
| Student | Link to Students | Enrolled student | Single link required |
| Class | Link to Classes | Class enrolled in | Single link required |
| Enrollment Name | Formula | Display name | `{Student} & " → " & {Class}` |
| Enrollment Date | Date | When enrolled | |
| **Payment & Sessions** | | | |
| Payment Status | Single select | Payment state | Options: Paid, Pending, Partial, Overdue, Refunded |
| Amount Paid | Currency | Money received | |
| Sessions Included | Number | Total sessions for this enrollment | For term classes, matches class sessions |
| **Emergency Contacts** | | | |
| Emergency Contact 1 Name | Single line text | Primary emergency contact | |
| Emergency Contact 1 Relationship | Single line text | Relationship to student | E.g., Aunt, Neighbour |
| Emergency Contact 1 Phone | Phone number | Contact phone | |
| Emergency Contact 2 Name | Single line text | Secondary emergency contact | |
| Emergency Contact 2 Relationship | Single line text | Relationship to student | |
| Emergency Contact 2 Phone | Phone number | Contact phone | |
| **Permissions & Preferences** | | | |
| Photo Permission | Single select | Photography consent | Options: "Yes - child & artwork", "Yes - artwork only", "No photos" |
| OSHC Collection | Checkbox | Collect from OSHC (Ironside SS only) | Australian-specific |
| Approved Pickup People | Long text | List of authorized pickup persons | In addition to linked Parents |
| **Marketing** | | | |
| Marketing Source | Single select | How did you hear about us? | Options: Facebook, Google, Instagram, Friend Referral, Flyer, School Newsletter, Kidsbook, Other |
| **Notes** | | | |
| Special Requests | Long text | Parent requests or student needs | |
| Additional Notes | Long text | Any other information | |
| **Tracking** | | | |
| Attendance Records | Link to Attendance | Individual attendance entries | Automatically populated |
| Sessions Attended | Rollup | Count of attended sessions | `COUNTALL(values)` from Attendance Records where Status = "Present" |
| Sessions Remaining | Formula | Sessions left | `{Sessions Included} - {Sessions Attended}` |
| Attendance Rate | Formula | Percentage attended | `IF({Sessions Attended} > 0, ROUND({Sessions Attended} / {Sessions Included} * 100, 0) & "%", "0%")` |

**Key Formulas:**
- `Enrollment Name`: `ARRAYJOIN({Student}, "") & " → " & ARRAYJOIN({Class}, "")`
- `Sessions Remaining`: `MAX(0, {Sessions Included} - {Sessions Attended})`
- `Attendance Rate`: `IF({Sessions Included} > 0, ROUND({Sessions Attended} / {Sessions Included} * 100, 1) & "%", "N/A")`
- `Payment Warning`: `IF({Payment Status} = "Overdue", "⚠️ OVERDUE", IF({Payment Status} = "Pending", "💰 Pending", ""))`
- `Has Emergency Contacts`: `IF(OR({Emergency Contact 1 Name}, {Emergency Contact 2 Name}), "✓", "⚠️ Missing")`

---

### 7. Attendance

**Purpose:** Individual attendance records for each class session.

| Field Name | Type | Description | Notes |
|------------|------|-------------|-------|
| Attendance ID | Auto number | Unique identifier | Primary field |
| Enrollment | Link to Enrollments | Which enrollment this is for | Single link required |
| Student | Lookup | Student name | From Enrollment → Student |
| Class | Lookup | Class name | From Enrollment → Class |
| Date | Date | Class date | |
| Status | Single select | Attendance status | Options: Present, Absent, Late, Excused |
| Pickup Person | Link to Parents | Who picked up the student | Single link |
| Sign-in Time | Date (with time) | When student signed in | |
| Sign-out Time | Date (with time) | When student was picked up | |
| Notes | Long text | Behavior, incidents, achievements | |

**Key Formulas:**
- `Record Name`: `ARRAYJOIN({Student}, "") & " - " & DATETIME_FORMAT({Date}, 'DD/MM/YYYY')`
- `Pickup Authorized`: `IF({Pickup Person}, IF(ARRAYJOIN({Pickup Person}, ""), "✓", "⚠️ Not recorded"), "")`

---

## Relationships Diagram

```
Parents (1) ←→ (many) Students
                    ↓
              (many) Enrollments (many) ← Classes (1) ← Venues
                    ↓                           ↑
              (many) Attendance              Teachers (1-2)
                    ↓
         Pickup Person (Parents)
```

**Key Relationships:**
1. **Parents ↔ Students**: One parent can have multiple students; one student can have multiple parents/guardians
2. **Students ↔ Enrollments ↔ Classes**: Many-to-many via Enrollments junction table
3. **Classes → Venue**: Many classes at one venue
4. **Classes → Teachers**: One class has 1-2 teachers (many-to-many)
5. **Enrollments → Attendance**: One enrollment has many attendance records
6. **Attendance → Parents (Pickup Person)**: Each attendance record links to who picked up

---

## Sample Use Cases

### 1. Enroll a Student
1. Find/create Parent record
2. Find/create Student record, link to Parent
3. Find target Class
4. Create Enrollment record linking Student + Class
5. Set payment status, sessions included

### 2. Roll Call (Daily Attendance)
1. Filter Enrollments by Class + today's date range
2. For each enrolled student, create Attendance record
3. Mark Status as Present/Absent
4. Record Sign-in Time
5. When picked up, link Pickup Person and record Sign-out Time

### 3. Parent Lookup
1. Find Parent record
2. View linked Students
3. View each Student's Enrollments (filtered to Active)
4. View Attendance Records for each Enrollment

### 4. Interest Tracking
1. Parent calls about pottery classes
2. Find/create Parent record
3. Check "Pottery" in Interest Categories
4. Add note to Interest Notes: "2025-01-15: Called re pottery for 7yo daughter, wants Term 1"
5. When class opens, filter Parents by Interest Categories = "Pottery"

### 5. Revenue Reporting
- Group Classes by Type (Term/Holiday)
- Sum Revenue (Projected) or Enrollments → Amount Paid
- Filter by date range

---

## Recommended Views (see VIEWS.md for details)

### Classes Table
- **All Active Classes**: Status = "Active"
- **Today's Classes**: Status = "Active", Day of Week = TODAY()
- **Classes by Venue**: Grouped by Venue
- **Classes by Teacher**: Grouped by Teachers

### Enrollments Table
- **Active Enrollments**: Class → Status = "Active"
- **Payment Pending**: Payment Status = "Pending" OR "Overdue"
- **By Student**: Grouped by Student
- **Attendance Issues**: Attendance Rate < 70%

### Attendance Table
- **Today's Roll Call**: Date = TODAY()
- **Not Picked Up**: Status = "Present", Pickup Person is empty
- **By Class**: Grouped by Class
- **Absences This Week**: Status = "Absent", Date within last 7 days

### Parents Table
- **Interested in Pottery**: Interest Categories contains "Pottery"
- **Authorized Pickup**: Authorized for Pickup = checked
- **No Enrollments**: Student Count > 0, Active Enrollments = 0

### Students Table
- **Active Students**: Active Enrollments > 0
- **Medical Notes**: Medical Notes is not empty
- **By Age**: Grouped by Age

---

## Implementation Notes

### Field Type Choices
- **Single line text** for short names/labels
- **Long text** for notes, addresses, multi-line content
- **Email/Phone** for proper formatting and click-to-call/email
- **Currency** for all dollar amounts (auto-formats with $)
- **Date** vs **Date with time**: Use Date for class dates, Date with time for sign-in/sign-out
- **Formula** for calculated values (read-only)
- **Rollup** for aggregating linked record data
- **Lookup** for pulling single values from linked records

### Privacy & Access
- Consider Airtable's permissions/interfaces for parent-facing views
- Keep medical/dietary notes visible to teachers in class views
- Restrict payment info to admin views only

### Future Enhancements (Phase 2+)
- Waitlist table for full classes
- Lesson plans table linked to Classes
- Materials inventory
- Teacher checkout system
- SMS integration for reminders
- Automated payment reminders
- Photo galleries per class session

---

## Data Validation Rules

1. **Student must have at least one Parent** before enrollment
2. **Enrollment requires both Student and Class** to be set
3. **Attendance requires Enrollment** to be set first
4. **Pickup Person should be flagged** if Authorized for Pickup = false
5. **Class capacity** should warn when Current Enrollment > Capacity
6. **Payment Status = "Paid"** should match Amount Paid = Price

---

## Migration / Setup Process

1. Create base in Airtable
2. Create all 7 tables
3. Add fields to each table (start with simple fields, add links/formulas after)
4. Set up relationships (link fields)
5. Add formulas and rollups
6. Import sample data (CSVs)
7. Create views
8. Test workflows (enroll → attend → pickup)
9. Refine field names/formulas based on real use

---

*Schema Version: 1.0*
*Last Updated: 2025-01-21*
