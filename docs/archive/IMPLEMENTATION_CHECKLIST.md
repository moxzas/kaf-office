# Implementation Checklist

Copy this checklist to track progress. Check off items as you complete them.

---

## ☑️ Pre-Build

- [ ] Reviewed SCHEMA_V2.md (know what tables/fields exist)
- [ ] Old base renamed to "🔴 OLD - Test Data"
- [ ] Created new base: "Art & Craft School CRM"

---

## ☑️ Build Tables

### Parents Table
- [ ] Create table "Parents"
- [ ] Add basic fields:
  - [ ] Name (Single line text) - Primary field
  - [ ] Email (Email)
  - [ ] Phone (Phone)
  - [ ] Mobile (Phone)
  - [ ] Address (Single line text)
  - [ ] Suburb (Single line text)
  - [ ] Postcode (Single line text)
  - [ ] Authorized for Pickup (Checkbox)
  - [ ] Interest Categories (Multiple select)
  - [ ] Interest Notes (Long text)
  - [ ] Communication Log (Long text)
  - [ ] Created Date (Created time)
- [ ] Add linked field:
  - [ ] Students (Link to Students, multiple)

### Students Table
- [ ] Create table "Students"
- [ ] Add basic fields:
  - [ ] Student ID Number (Auto number)
  - [ ] Name (Single line text) - Primary field
  - [ ] Date of Birth (Date)
  - [ ] School (Single select - add: Chapel Hill Art Studio, Ironside State School, etc.)
  - [ ] Year/Class (Single line text)
  - [ ] Medical Notes (Long text)
  - [ ] Dietary Notes (Long text)
  - [ ] Special Needs (Long text)
  - [ ] Student Photo (Attachment)
  - [ ] Notes (Long text)
- [ ] Add linked fields:
  - [ ] Primary Parent (Link to Parents, single)
  - [ ] Parents (Link to Parents, multiple)
  - [ ] Enrollments (Link to Enrollments, multiple)
- [ ] Add formulas/lookups:
  - [ ] Student ID (Formula: `"STU-" & RIGHT("000" & {Student ID Number}, 3)`)
  - [ ] Age (Formula: `DATETIME_DIFF(TODAY(), {Date of Birth}, 'years')`)
  - [ ] Address (Lookup from Primary Parent)
  - [ ] Suburb (Lookup from Primary Parent)
  - [ ] Postcode (Lookup from Primary Parent)
- [ ] Add rollups:
  - [ ] Active Enrollments (Rollup: COUNT from Enrollments where Class Status = Active)
  - [ ] Total Classes Attended (Rollup: COUNT from Enrollments → Attendance where Status = Present)

### Venues Table
- [ ] Create table "Venues"
- [ ] Add fields:
  - [ ] Name (Single line text) - Primary field
  - [ ] Type (Single select: School Rental, Home Studio)
  - [ ] Address (Long text)
  - [ ] Suburb (Single line text)
  - [ ] Capacity (Number)
  - [ ] Contact/Access Notes (Long text)
- [ ] Add linked field:
  - [ ] Classes (Link to Classes, multiple)
- [ ] Add rollup:
  - [ ] Active Classes Count (Rollup: COUNT from Classes where Status = Active)

### Teachers Table
- [ ] Create table "Teachers"
- [ ] Add fields:
  - [ ] Name (Single line text) - Primary field
  - [ ] Email (Email)
  - [ ] Phone (Phone)
  - [ ] Notes (Long text)
- [ ] Add linked field:
  - [ ] Classes (Link to Classes, multiple)
- [ ] Add rollup:
  - [ ] Active Classes Count (Rollup: COUNT from Classes where Status = Active)

### Classes Table
- [ ] Create table "Classes"
- [ ] Add basic fields:
  - [ ] Name (Single line text) - Primary field
  - [ ] Type (Single select: Term, Holiday)
  - [ ] Category (Single select: Pottery, Painting, Drawing, Sculpture, Mixed Media, General Craft)
  - [ ] Day of Week (Single select: Monday-Sunday)
  - [ ] Start Time (Single line text)
  - [ ] Duration (mins) (Number)
  - [ ] Term Start Date (Date)
  - [ ] Term End Date (Date)
  - [ ] Sessions in Term (Number)
  - [ ] Price (Currency)
  - [ ] Capacity (Number)
  - [ ] Status (Single select: Active, Inactive, Full, Cancelled)
- [ ] Add linked fields:
  - [ ] Venue (Link to Venues, single)
  - [ ] Teachers (Link to Teachers, multiple)
  - [ ] Enrollments (Link to Enrollments, multiple)
- [ ] Add rollup:
  - [ ] Current Enrollment (Rollup: COUNT from Enrollments)
- [ ] Add formulas:
  - [ ] Spots Remaining (Formula: `{Capacity} - {Current Enrollment}`)
  - [ ] Revenue (Projected) (Formula: `{Current Enrollment} * {Price}`)

### Enrollments Table
- [ ] Create table "Enrollments"
- [ ] Add basic fields:
  - [ ] Enrollment ID (Auto number) - Primary field
  - [ ] Enrollment Date (Date)
  - [ ] Payment Status (Single select: Paid, Pending, Partial, Overdue, Refunded)
  - [ ] Amount Paid (Currency)
  - [ ] Sessions Included (Number)
  - [ ] Emergency Contact 1 Name (Single line text)
  - [ ] Emergency Contact 1 Relationship (Single line text)
  - [ ] Emergency Contact 1 Phone (Phone)
  - [ ] Emergency Contact 2 Name (Single line text)
  - [ ] Emergency Contact 2 Relationship (Single line text)
  - [ ] Emergency Contact 2 Phone (Phone)
  - [ ] Photo Permission (Single select: "Yes - child & artwork", "Yes - artwork only", "No photos")
  - [ ] OSHC Collection (Checkbox)
  - [ ] Approved Pickup People (Long text)
  - [ ] Marketing Source (Single select: Facebook, Google, Instagram, Friend Referral, Flyer, School Newsletter, Kidsbook, Other)
  - [ ] Special Requests (Long text)
  - [ ] Additional Notes (Long text)
- [ ] Add linked fields:
  - [ ] Student (Link to Students, single, required)
  - [ ] Class (Link to Classes, single, required)
  - [ ] Attendance Records (Link to Attendance, multiple)
- [ ] Add formulas:
  - [ ] Enrollment Name (Formula: `ARRAYJOIN({Student}, "") & " → " & ARRAYJOIN({Class}, "")`)
- [ ] Add rollups:
  - [ ] Sessions Attended (Rollup: COUNT from Attendance Records where Status = Present)
  - [ ] Sessions Remaining (Formula: `MAX(0, {Sessions Included} - {Sessions Attended})`)
  - [ ] Attendance Rate (Formula: `IF({Sessions Included} > 0, ROUND({Sessions Attended} / {Sessions Included} * 100, 1) & "%", "N/A")`)

### Attendance Table
- [ ] Create table "Attendance"
- [ ] Add basic fields:
  - [ ] Attendance ID (Auto number) - Primary field
  - [ ] Date (Date)
  - [ ] Status (Single select: Present, Absent, Late, Excused)
  - [ ] Sign-in Time (Date with time)
  - [ ] Sign-out Time (Date with time)
  - [ ] Notes (Long text)
- [ ] Add linked fields:
  - [ ] Enrollment (Link to Enrollments, single, required)
  - [ ] Pickup Person (Link to Parents, single)
- [ ] Add lookups:
  - [ ] Student (Lookup from Enrollment → Student)
  - [ ] Class (Lookup from Enrollment → Class)

---

## ☑️ Import Sample Data

- [ ] Import `sample_data/venues.csv` → Venues table
- [ ] Import `sample_data/teachers.csv` → Teachers table
- [ ] Import `sample_data/parents.csv` → Parents table
- [ ] Import `sample_data/students.csv` → Students table
  - [ ] Manually link Students to Parents (CSV import doesn't do links)
- [ ] Import `sample_data/classes.csv` → Classes table
  - [ ] Manually link Classes to Venues
  - [ ] Manually link Classes to Teachers

---

## ☑️ Create Views

### Classes Table
- [ ] "All Active Classes" (Filter: Status = Active, Group by: Day of Week)
- [ ] "Nearly Full Classes" (Filter: Spots Remaining ≤ 3)

### Students Table
- [ ] "Active Students" (Filter: Active Enrollments > 0)
- [ ] "Students with Medical Notes" (Filter: Medical Notes OR Dietary Notes OR Special Needs is not empty)

### Parents Table
- [ ] "Authorized Pickup Only" (Filter: Authorized for Pickup = checked)

### Enrollments Table
- [ ] "Payment Pending" (Filter: Payment Status = Pending OR Overdue)
- [ ] "By Student" (Group by: Student)

### Attendance Table
- [ ] "Today's Roll Call" (Filter: Date = today)
- [ ] "Not Yet Picked Up" (Filter: Date = today, Status = Present, Sign-out Time is empty)

---

## ☑️ Test Workflow

- [ ] Create a test parent record
- [ ] Create a test student record linked to parent
- [ ] Create/find a test class
- [ ] Create enrollment linking student + class
- [ ] Create attendance record for enrollment
- [ ] Mark attendance as Present
- [ ] Link pickup person
- [ ] Record sign-out time

**If all steps work → You're ready for production**

---

## ☑️ Go Live

- [ ] Archive old base (rename, hide from workspace)
- [ ] Share new base with Sophia
- [ ] Train on enrollment workflow
- [ ] Create first real enrollment
- [ ] Monitor for issues

---

## 📝 Notes / Issues

(Space for tracking problems, questions, or customizations)

---

**Estimated Time:**
- Tables + Fields: 1-1.5 hours
- Sample Data: 15 minutes
- Views: 30 minutes
- Testing: 15 minutes
- **Total: 2-2.5 hours**

---

*Use this checklist to stay focused and track progress systematically.*
