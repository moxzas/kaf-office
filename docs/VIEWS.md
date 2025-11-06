# Airtable Views: Art & Craft School CRM

## Overview
This document defines the key views needed for each table to support daily operations. Views are saved filters, sorts, and groupings that make data easier to work with.

---

## 1. Parents Table Views

### All Parents (Default)
- **Filter:** None
- **Sort:** Name (A → Z)
- **Fields:** Name, Email, Mobile, Students, Authorized for Pickup, Interest Categories
- **Purpose:** Master list of all contacts

### Authorized Pickup Only
- **Filter:** Authorized for Pickup = checked
- **Sort:** Name (A → Z)
- **Fields:** Name, Mobile, Students, Interest Categories
- **Purpose:** Quick reference for who can pick up students

### Interested in Pottery
- **Filter:** Interest Categories contains "Pottery"
- **Sort:** Name (A → Z)
- **Fields:** Name, Email, Mobile, Interest Categories, Interest Notes, Communication Log
- **Purpose:** Marketing/outreach for pottery classes
- **Note:** Create similar views for each interest category

### No Active Enrollments
- **Filter:**
  - Students is not empty
  - Active Enrollments (rollup) = 0
- **Sort:** Last Modified (newest first)
- **Fields:** Name, Email, Mobile, Students, Interest Categories, Interest Notes
- **Purpose:** Re-engagement opportunities - parents who enrolled before but aren't currently active

### Pending Communications
- **Filter:** Communication Log contains "follow up" OR "call back"
- **Sort:** Last Modified (newest first)
- **Fields:** Name, Email, Mobile, Interest Notes, Communication Log
- **Purpose:** Action items for admin follow-up

---

## 2. Students Table Views

### All Students (Default)
- **Filter:** None
- **Sort:** Name (A → Z)
- **Fields:** Name, Age, Parents, Medical Notes, Dietary Notes, Active Enrollments
- **Group by:** Age
- **Purpose:** Master student list grouped by age

### Active Students
- **Filter:** Active Enrollments > 0
- **Sort:** Name (A → Z)
- **Fields:** Name, Age, Parents, Medical Notes, Active Enrollments
- **Purpose:** Currently enrolled students only

### Students with Medical Notes
- **Filter:** Medical Notes is not empty OR Dietary Notes is not empty
- **Sort:** Name (A → Z)
- **Fields:** Name, Age, Parents, Medical Notes, Dietary Notes, Active Enrollments
- **Purpose:** Important for teacher awareness and emergency situations
- **Color coding:** Consider highlighting rows in yellow/orange

### Inactive Students
- **Filter:** Active Enrollments = 0
- **Sort:** Last Modified (oldest first)
- **Fields:** Name, Age, Parents, Total Classes Attended (rollup)
- **Purpose:** Students who enrolled previously but aren't currently active

### By Age Group
- **Filter:** None
- **Sort:** Age (1 → 9)
- **Group by:** Age
- **Fields:** Name, Date of Birth, Parents, Active Enrollments
- **Purpose:** Planning age-appropriate classes

---

## 3. Venues Table Views

### All Venues (Default)
- **Filter:** None
- **Sort:** Name (A → Z)
- **Fields:** Name, Type, Suburb, Capacity, Active Classes Count, Contact/Access Notes
- **Purpose:** Master venue list

### School Rentals
- **Filter:** Type = "School Rental"
- **Sort:** Name (A → Z)
- **Fields:** Name, Suburb, Capacity, Contact/Access Notes, Active Classes Count
- **Purpose:** External venue management

### Home Studio
- **Filter:** Type = "Home Studio"
- **Sort:** Name (A → Z)
- **Fields:** Name, Capacity, Active Classes Count
- **Purpose:** Home studio classes

### By Suburb
- **Filter:** None
- **Sort:** Suburb (A → Z)
- **Group by:** Suburb
- **Fields:** Name, Type, Capacity, Active Classes Count
- **Purpose:** Geographic planning

---

## 4. Teachers Table Views

### All Teachers (Default)
- **Filter:** None
- **Sort:** Name (A → Z)
- **Fields:** Name, Email, Phone, Active Classes Count, Classes
- **Purpose:** Master teacher list

### Active Teachers
- **Filter:** Active Classes Count > 0
- **Sort:** Active Classes Count (9 → 1)
- **Fields:** Name, Email, Phone, Active Classes Count, Classes
- **Purpose:** Currently teaching instructors

### Available Teachers
- **Filter:** Active Classes Count < 3
- **Sort:** Active Classes Count (1 → 9)
- **Fields:** Name, Email, Phone, Active Classes Count, Notes
- **Purpose:** Finding teachers for new classes

---

## 5. Classes Table Views

### All Active Classes (Default)
- **Filter:** Status = "Active"
- **Sort:** Day of Week, then Start Time
- **Fields:** Name, Type, Category, Day of Week, Start Time, Venue, Teachers, Current Enrollment, Capacity, Spots Remaining
- **Group by:** Day of Week
- **Purpose:** Weekly schedule overview

### Today's Classes
- **Filter:**
  - Status = "Active"
  - Day of Week = [Today's day]
- **Sort:** Start Time
- **Fields:** Name, Venue, Teachers, Start Time, Duration, Current Enrollment, Capacity
- **Purpose:** Daily teaching schedule
- **Note:** This view will need to be manually filtered or use a formula field for "Is Today"

### Classes by Venue
- **Filter:** Status = "Active"
- **Sort:** Venue (A → Z), then Day of Week
- **Group by:** Venue
- **Fields:** Name, Day of Week, Start Time, Teachers, Current Enrollment, Capacity
- **Purpose:** Venue coordination and planning

### Classes by Teacher
- **Filter:** Status = "Active"
- **Sort:** Teachers (A → Z)
- **Group by:** Teachers
- **Fields:** Name, Day of Week, Start Time, Venue, Current Enrollment, Capacity
- **Purpose:** Teacher workload and scheduling

### Term vs Holiday
- **Filter:** Status = "Active"
- **Sort:** Type, then Term Start Date
- **Group by:** Type
- **Fields:** Name, Category, Term Start Date, Term End Date, Sessions in Term, Price, Current Enrollment, Revenue (Projected)
- **Purpose:** Program type comparison

### Nearly Full Classes
- **Filter:**
  - Status = "Active"
  - Spots Remaining ≤ 3
- **Sort:** Spots Remaining (1 → 9)
- **Fields:** Name, Current Enrollment, Capacity, Spots Remaining, Day of Week, Start Time
- **Color coding:** Highlight in orange/red
- **Purpose:** Classes approaching capacity

### Full Classes
- **Filter:**
  - Status = "Active" OR Status = "Full"
  - Current Enrollment ≥ Capacity
- **Sort:** Name (A → Z)
- **Fields:** Name, Current Enrollment, Capacity, Type, Category
- **Purpose:** Waitlist management

### Pottery Classes
- **Filter:**
  - Status = "Active"
  - Category = "Pottery"
- **Sort:** Day of Week, Start Time
- **Fields:** Name, Venue, Teachers, Day of Week, Start Time, Current Enrollment, Capacity
- **Purpose:** Category-specific view (create similar for each category)

### Revenue Report
- **Filter:** Status = "Active"
- **Sort:** Revenue (Projected) (9 → 1)
- **Group by:** Type
- **Fields:** Name, Current Enrollment, Price, Revenue (Projected), Category, Term Start Date
- **Summary:** Sum Revenue (Projected)
- **Purpose:** Financial overview

---

## 6. Enrollments Table Views

### All Active Enrollments (Default)
- **Filter:** Class → Status = "Active"
- **Sort:** Student (A → Z)
- **Group by:** Student
- **Fields:** Enrollment Name, Student, Class, Payment Status, Sessions Remaining, Attendance Rate
- **Purpose:** Master enrollment list

### By Student
- **Filter:** Class → Status = "Active"
- **Sort:** Student (A → Z)
- **Group by:** Student
- **Fields:** Student, Class, Payment Status, Amount Paid, Sessions Remaining, Attendance Rate
- **Purpose:** Parent conversations about enrollments

### By Class
- **Filter:** Class → Status = "Active"
- **Sort:** Class (A → Z)
- **Group by:** Class
- **Fields:** Student, Enrollment Date, Payment Status, Sessions Remaining, Special Requests
- **Purpose:** Class roster and planning

### Payment Pending
- **Filter:**
  - Payment Status = "Pending" OR Payment Status = "Overdue"
  - Class → Status = "Active"
- **Sort:** Enrollment Date (oldest first)
- **Fields:** Student, Class, Enrollment Date, Payment Status, Amount Paid, Price (from Class), Student → Parents
- **Color coding:** Red for Overdue, Orange for Pending
- **Purpose:** Payment follow-up

### Payment Partially Paid
- **Filter:**
  - Payment Status = "Partial"
  - Class → Status = "Active"
- **Sort:** Student (A → Z)
- **Fields:** Student, Class, Amount Paid, Price (from Class), Payment Status, Student → Parents
- **Purpose:** Payment plan tracking

### All Paid
- **Filter:**
  - Payment Status = "Paid"
  - Class → Status = "Active"
- **Sort:** Student (A → Z)
- **Group by:** Class
- **Fields:** Student, Class, Amount Paid, Enrollment Date
- **Purpose:** Confirmed enrollments

### Low Attendance
- **Filter:**
  - Sessions Attended ≥ 3
  - Attendance Rate < 70%
- **Sort:** Attendance Rate (1 → 9)
- **Fields:** Student, Class, Sessions Attended, Sessions Included, Attendance Rate, Student → Parents
- **Purpose:** Student welfare check-ins

### Sessions Running Out
- **Filter:**
  - Class → Type = "Term"
  - Sessions Remaining ≤ 2
  - Sessions Remaining > 0
- **Sort:** Sessions Remaining (1 → 9)
- **Fields:** Student, Class, Sessions Remaining, Attendance Rate, Student → Parents
- **Purpose:** Re-enrollment outreach

### Special Requests
- **Filter:** Special Requests is not empty
- **Sort:** Class (A → Z)
- **Group by:** Class
- **Fields:** Student, Class, Special Requests, Student → Medical Notes
- **Purpose:** Teacher preparation

---

## 7. Attendance Table Views

### All Attendance (Default)
- **Filter:** None
- **Sort:** Date (newest first)
- **Group by:** Class
- **Fields:** Date, Student, Class, Status, Pickup Person, Sign-in Time, Notes
- **Purpose:** Complete attendance record

### Today's Roll Call
- **Filter:** Date = [Today]
- **Sort:** Class, then Student
- **Group by:** Class
- **Fields:** Student, Class, Status, Sign-in Time, Sign-out Time, Pickup Person, Notes
- **Purpose:** Daily attendance tracking
- **Note:** Update filter daily or use formula

### This Week
- **Filter:** Date is within [Last 7 days]
- **Sort:** Date (newest first), then Class
- **Group by:** Date
- **Fields:** Date, Student, Class, Status, Pickup Person
- **Purpose:** Weekly overview

### Present Today
- **Filter:**
  - Date = [Today]
  - Status = "Present" OR Status = "Late"
- **Sort:** Class, then Student
- **Group by:** Class
- **Fields:** Student, Class, Sign-in Time, Pickup Person, Sign-out Time
- **Purpose:** Current students in class

### Not Yet Picked Up
- **Filter:**
  - Date = [Today]
  - Status = "Present"
  - Sign-out Time is empty
- **Sort:** Sign-in Time (oldest first)
- **Fields:** Student, Class, Sign-in Time, Pickup Person, Student → Parents (phone)
- **Color coding:** Highlight in red after class end time
- **Purpose:** Student safety - tracking pickups

### Absences This Week
- **Filter:**
  - Date is within [Last 7 days]
  - Status = "Absent" OR Status = "Excused"
- **Sort:** Date (newest first)
- **Group by:** Student
- **Fields:** Date, Student, Class, Status, Notes
- **Purpose:** Following up on absences

### By Student
- **Filter:** None
- **Sort:** Date (newest first)
- **Group by:** Student
- **Fields:** Date, Class, Status, Pickup Person, Notes
- **Purpose:** Individual student history

### By Class
- **Filter:** None
- **Sort:** Date (newest first)
- **Group by:** Class
- **Fields:** Date, Student, Status, Pickup Person, Notes
- **Purpose:** Class-specific attendance patterns

### Pickup Concerns
- **Filter:**
  - Pickup Person is not empty
  - Pickup Person → Authorized for Pickup = false
- **Sort:** Date (newest first)
- **Fields:** Date, Student, Class, Pickup Person, Notes
- **Color coding:** Red highlight
- **Purpose:** Safety audit - unauthorized pickups

### Late Arrivals
- **Filter:** Status = "Late"
- **Sort:** Date (newest first)
- **Group by:** Student
- **Fields:** Date, Student, Class, Sign-in Time, Notes
- **Purpose:** Pattern identification

---

## Interface Views (for Parent Portal - Future Phase)

### Parent-Facing Views
Consider creating Airtable Interfaces for parent access:

1. **My Children**
   - Shows Students linked to logged-in parent
   - Active enrollments
   - Upcoming classes

2. **My Enrollments**
   - Active classes
   - Payment status
   - Sessions remaining

3. **Attendance History**
   - Past attendance records
   - Attendance rate per class

---

## View Naming Conventions

- **All [Table]**: Default view with no filters
- **Active**: Currently relevant records only
- **By [Field]**: Grouped by that field
- **[Specific Filter]**: Describes the filter condition clearly

---

## Tips for View Management

1. **Pin frequently used views** to the top
2. **Hide fields** that aren't needed in specific views to reduce clutter
3. **Use conditional coloring** for important flags:
   - Red: Urgent (overdue payments, unauthorized pickup)
   - Orange: Warning (low attendance, nearly full)
   - Green: Good (paid, present)
   - Yellow: Medical notes

4. **Create personal views** for each admin user if needed
5. **Share views** with teachers via Airtable interface for read-only access
6. **Date filters** may need manual updating unless using automation/formulas

---

## Automation Ideas (Future Enhancement)

1. **Daily Roll Call Reminder**: Send email to teachers with Today's Classes view
2. **Payment Reminders**: Weekly email for Payment Pending enrollments
3. **Low Attendance Alert**: Trigger when attendance rate drops below 60%
4. **Re-enrollment Nudge**: When Sessions Remaining ≤ 2, email parent
5. **Pickup Notification**: SMS parent when student signed in

---

*Views Version: 1.0*
*Last Updated: 2025-01-21*
