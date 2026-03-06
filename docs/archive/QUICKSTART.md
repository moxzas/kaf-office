# Quickstart: Build the CRM from Scratch

**TL;DR:** The old base has test data. Start fresh with SCHEMA_V2.md. Ignore migration docs.

---

## 🎯 What to Do

### 1. Rename Old Base (2 mins)
- Go to old base: https://airtable.com/app1MhJmZGREczxSx
- Rename to: "🔴 OLD - Test Data (Do Not Use)"
- Keep it for reference, never delete

### 2. Create New Base (10 mins)
1. Go to Airtable workspace
2. Create new base: "Art & Craft School CRM"
3. Create 7 tables:
   - Parents
   - Students
   - Venues
   - Teachers
   - Classes
   - Enrollments
   - Attendance

### 3. Add Fields (30 mins)
For each table, copy fields from **SCHEMA_V2.md** (Section: Tables & Fields)

**Order matters for linked fields:**
1. ✅ Add basic fields first (text, numbers, dates, selects)
2. ✅ Then add Link fields
3. ✅ Then add Formulas, Rollups, Lookups (reference link fields)

**Quick reference:**
- Parents: 13 fields (Name, Email, Phone, Mobile, Address, Suburb, Postcode, etc.)
- Students: 20 fields (Student ID, Name, DOB, School, Medical, Photo, etc.)
- Venues: 7 fields
- Teachers: 5 fields
- Classes: 17 fields
- Enrollments: 26 fields (includes emergency contacts, permissions)
- Attendance: 8 fields

### 4. Create Sample Records (15 mins)
Import CSVs from `sample_data/`:
1. Venues (4 records)
2. Teachers (3 records)
3. Parents (7 records)
4. Students (10 records) - link to Parents
5. Classes (6 records) - link to Venues, Teachers

**Skip:** Enrollments and Attendance (create these when real students enroll)

### 5. Set Up Views (30 mins)
Follow **VIEWS.md** to create key views:

**Must-have views:**
- Classes: "All Active Classes", "Today's Classes"
- Students: "Active Students", "Students with Medical Notes"
- Enrollments: "Payment Pending", "By Student"
- Attendance: "Today's Roll Call", "Not Yet Picked Up"
- Parents: "Authorized Pickup Only"

### 6. Build Enrollment Interface (Optional, 1-2 hours)
Use Airtable Interface Builder to create enrollment form that:
- Searches/creates Parent
- Creates/links Student
- Creates Enrollment
- All in one flow

**Or:** Just use Airtable forms for now, manually link records

---

## 📋 Field Priority (If Short on Time)

### Phase 1 - Core Fields Only:
**Parents:** Name, Email, Mobile, Address, Suburb, Postcode, Authorized for Pickup
**Students:** Student ID, Name, DOB, School, Medical Notes, Primary Parent (link)
**Classes:** Name, Day, Time, Venue (link), Type, Category, Capacity, Status
**Enrollments:** Student (link), Class (link), Payment Status, Sessions Included

### Phase 2 - Add Later:
- Emergency contacts in Enrollments
- Photo permissions
- Marketing source
- Student photos
- Attendance table

---

## 🚀 First Real Enrollment Workflow

1. **Parent calls/emails:**
   - Create Parent record (Name, Email, Mobile, Address)
   - Set Authorized for Pickup = ✓

2. **Add student:**
   - Create Student record
   - Link to Parent (Primary Parent field)
   - Fill: Name, DOB, School, Medical Notes
   - Upload photo if available

3. **Enroll in class:**
   - Find Class (or create if new term)
   - Create Enrollment record:
     - Link Student
     - Link Class
     - Set Payment Status
     - Add Emergency Contacts
     - Set Photo Permission

4. **Mark attendance:**
   - Create Attendance record
   - Link to Enrollment
   - Set Date, Status = Present
   - Link Pickup Person when collected

---

## 🎨 Australian Schools Dropdown

For Students.School field, use these options:
- Chapel Hill Art Studio
- Ironside State School
- Yeronga State School
- Good News Lutheran School
- St Lucia Kindergarten
- Other

Add more as needed.

---

## ⚡ Advanced: Custom Student ID

**Auto-generate STU-001, STU-002, etc:**

1. Add to Students table:
   - `Student ID Number` (Auto number field)
   - `Student ID` (Formula field)

2. Formula:
   ```
   "STU-" & RIGHT("000" & {Student ID Number}, 3)
   ```

3. Result: STU-001, STU-002, STU-003...

---

## 📊 Quick Reporting

**How many active students?**
- Students table → "Active Students" view (Active Enrollments > 0)

**Payment status?**
- Enrollments table → "Payment Pending" view

**Who's here today?**
- Attendance table → "Today's Roll Call" view (Date = today)

**Revenue?**
- Classes table → "Revenue Report" view
- Sum of Current Enrollment × Price

---

## 🆘 If You Get Stuck

1. Check **SCHEMA_V2.md** for field definitions
2. Check **VIEWS.md** for view configurations
3. Look at `sample_data/` CSVs for examples
4. Old base still there for reference (don't use, just look)

---

## ✅ Done Checklist

- [ ] Old base renamed
- [ ] New base created with 7 tables
- [ ] All fields added (at minimum: Phase 1 core fields)
- [ ] Sample data imported
- [ ] 3-5 key views created
- [ ] Test workflow: Create parent → student → enrollment
- [ ] Ready for real enrollments

---

## 🎯 What NOT to Do

- ❌ Don't migrate old data (it's test data, not worth it)
- ❌ Don't try to preserve old base structure
- ❌ Don't overthink it - just build from SCHEMA_V2.md
- ❌ Don't add fancy features yet - get basics working first

---

**Time to complete:** 2-3 hours for full setup, 1 hour for minimal viable

**Next step:** Open SCHEMA_V2.md and start building tables.

---

*Quickstart Version: 1.0*
*Last Updated: 2025-01-21*
