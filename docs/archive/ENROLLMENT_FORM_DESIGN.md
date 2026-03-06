# Enrollment Form Design - Simplified Passwordless Flow

**Goal:** Make it easy for parents to enroll kids while capturing complete information.

---

## Two-Phase Approach

### **Phase 1: Quick Start (Funnel Top)**
Get parent in the door, send them a link to complete later.

### **Phase 2: Full Enrollment**
Complete student details, class selection, permissions when they're ready.

---

## Phase 1: Email Capture Form

**URL:** `kaf.sonzai.com` or `app.sonzai.com/kaf`

### Page Design (Single Page)

```
┌──────────────────────────────────────────────────────┐
│                                                       │
│     🎨 KAF Art & Craft School                       │
│                                                       │
│     Get Started - Enter Your Details                 │
│                                                       │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Email Address *                                     │
│  [____________________]                              │
│                                                       │
│  Your Name *                                         │
│  [____________________]                              │
│                                                       │
│  Mobile Number *                                     │
│  [____________________]                              │
│                                                       │
│  [ Send Me My Enrollment Link ]                     │
│                                                       │
│  We'll email you a personalized link to:            │
│  • Add your children's details                      │
│  • Browse and select classes                        │
│  • Complete enrollment anytime                      │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### What Happens

1. User fills out 3 fields (email, name, mobile)
2. Form submits to Shelf server endpoint: `POST /api/request-link`
3. Server:
   - Checks if email exists in Airtable
   - **If exists:** Send link to existing record
   - **If new:** Create new Parent record, send link
4. User sees: "Check your email! We've sent you a link to continue."
5. Email contains: `kaf.sonzai.com/enrol/{parent_record_id}`

### Fields Created in Airtable (Parents table)

```json
{
  "Name": "Sarah Johnson",
  "Email": "sarah@example.com",
  "Mobile": "0444 444 444",
  "Authorized for Pickup": true  // Default
}
```

---

## Phase 2: Full Enrollment Form

**URL:** `kaf.sonzai.com/enrol/rec2TKvLhWqVio1qO`

### Multi-Page SurveyJS Form

#### **Page 1: Your Details** (Pre-filled from Phase 1)

```
┌──────────────────────────────────────────────────────┐
│  Welcome back, Sarah!                                 │
│                                                       │
│  Contact Information                                 │
│                                                       │
│  Name: [Sarah Johnson________] (pre-filled)         │
│  Email: [sarah@example.com___] (pre-filled)         │
│  Mobile: [0444 444 444_______] (pre-filled)         │
│  Phone: [__________________] (optional)              │
│                                                       │
│  Address                                             │
│  Street: [_______________________]                   │
│  Suburb: [_______________________]                   │
│  Postcode: [____]                                    │
│                                                       │
│  ☑ I am authorized to pick up my children           │
│                                                       │
│  [Continue →]                                        │
└──────────────────────────────────────────────────────┘
```

Updates Parent record with address info.

---

#### **Page 2: Your Children** (Repeatable)

```
┌──────────────────────────────────────────────────────┐
│  Add Your Children                                    │
│                                                       │
│  ┌────────────────────────────────────────────────┐ │
│  │ Student 1                                      │ │
│  │                                                │ │
│  │ Name: [__________________________]            │ │
│  │ Date of Birth: [__/__/____]                   │ │
│  │ School: [Dropdown ▼]                          │ │
│  │   • Ironside State School                     │ │
│  │   • St Lucia Kindergarten                     │ │
│  │   • Yeronga State School                      │ │
│  │   • Other                                     │ │
│  │ Year/Class: [________]                        │ │
│  │                                                │ │
│  │ Medical Notes: [__________________]           │ │
│  │ Dietary Notes: [__________________]           │ │
│  │ Special Needs: [__________________]           │ │
│  │                                                │ │
│  └────────────────────────────────────────────────┘ │
│                                                       │
│  [+ Add Another Child]                               │
│                                                       │
│  [Continue →]                                        │
└──────────────────────────────────────────────────────┘
```

**SurveyJS Feature:** Dynamic Panel - allows adding multiple students.

Creates Student records linked to Parent.

---

#### **Page 3: Select Classes**

```
┌──────────────────────────────────────────────────────┐
│  Select Classes                                       │
│                                                       │
│  For: [Dropdown: Select Student ▼]                  │
│                                                       │
│  Available Classes:                                  │
│                                                       │
│  ☐ Pottery - Term 1 2025                            │
│     Mondays 3:30 PM - Ironside SS                   │
│     6/10 spots remaining                             │
│                                                       │
│  ☐ Painting - Term 1 2025                           │
│     Wednesdays 4:00 PM - Chapel Hill Studio         │
│     2/8 spots remaining                              │
│                                                       │
│  ☐ Holiday Program - January 2025                   │
│     Mon-Fri 9:00 AM - Chapel Hill Studio            │
│     8/12 spots remaining                             │
│                                                       │
│  [Continue →]                                        │
└──────────────────────────────────────────────────────┘
```

**Logic:**
- Dropdown lists all students added in Page 2
- Select student → Show classes
- Repeat for each student
- Classes loaded dynamically from Airtable Classes table

**Later enhancement:** Filter by age, category, day of week.

---

#### **Page 4: Enrollment Details** (Per Student/Class Combo)

```
┌──────────────────────────────────────────────────────┐
│  Enrollment Details                                   │
│                                                       │
│  For: Emma Johnson → Pottery Term 1 2025            │
│                                                       │
│  Authorized Pickup People                            │
│  1. ✓ Sarah Johnson (you) - 0444 444 444           │
│  2. Name: [______________] Relation: [_____]        │
│     Phone: [______________]                          │
│  3. Name: [______________] Relation: [_____]        │
│     Phone: [______________]                          │
│                                                       │
│  Emergency Contacts (if different from above)        │
│  1. Name: [______________] Relation: [_____]        │
│     Phone: [______________]                          │
│  2. Name: [______________] Relation: [_____]        │
│     Phone: [______________]                          │
│                                                       │
│  Photo Permission                                    │
│  ○ Yes - child & artwork                            │
│  ○ Yes - artwork only                               │
│  ○ No photos                                        │
│                                                       │
│  ☐ Pick up from OSHC (Ironside SS only)             │
│                                                       │
│  Special Requests                                    │
│  [_________________________________]                 │
│                                                       │
│  [Continue →]                                        │
└──────────────────────────────────────────────────────┘
```

**Logic:**
- This page repeats for EACH student/class combination
- If Emma enrolled in 2 classes → 2 pages
- If Emma + Noah enrolled in 3 classes total → 3 pages

Creates Enrollment records in Airtable.

---

#### **Page 5: Summary & Submit**

```
┌──────────────────────────────────────────────────────┐
│  Review Your Enrollments                              │
│                                                       │
│  Emma Johnson                                        │
│    • Pottery - Term 1 2025 (Mondays 3:30 PM)        │
│    • Holiday Program (Mon-Fri 9:00 AM)              │
│                                                       │
│  Noah Johnson                                        │
│    • Painting - Term 1 2025 (Wednesdays 4:00 PM)    │
│                                                       │
│  ──────────────────────────────────────────────────  │
│                                                       │
│  Next Steps:                                         │
│  • We'll send payment details via email             │
│  • Class starts: [Date]                             │
│  • Location: [Venue]                                │
│                                                       │
│  [Submit Enrollment]                                 │
└──────────────────────────────────────────────────────┘
```

After submit:
- Show thank you message
- Send confirmation email
- Sophia gets notification

---

## Data Flow Summary

### Phase 1: Email Capture
```
User → Shelf Server → Airtable Parents table
                   ↓
                Email with link
```

### Phase 2: Full Enrollment
```
Page 1: Update Parent (address)
Page 2: Create Students (repeatable)
Page 3: Select Classes (per student)
Page 4: Create Enrollments (per student/class)
Page 5: Submit all
```

### Airtable Records Created

For 1 parent with 2 kids in 3 classes total:

```
Parents: 1 record (updated)
Students: 2 records (created)
Enrollments: 3 records (created)
```

---

## Technical Implementation

### Phase 1 Tech Stack
- Static HTML + JS form
- Shelf server endpoint: `POST /api/request-link`
- Resend for email sending
- Airtable API for parent lookup/creation

### Phase 2 Tech Stack
- SurveyJS form (what we already built in POC)
- Shelf server serves form with pre-filled data
- SurveyJS dynamic panels for repeatable students
- Shelf API endpoints to proxy Airtable calls

---

## SurveyJS Features to Use

1. **Dynamic Panels** - Add multiple students
2. **Conditional Visibility** - OSHC checkbox only for Ironside SS
3. **Pre-filling** - Load parent data from Airtable
4. **Custom Widgets** - Class selection with details
5. **Progress Bar** - Show completion progress
6. **Validation** - Required fields, email format, date ranges

---

## Questions to Resolve

- [ ] Should we show class prices in the form? (You said no for now)
- [ ] Should we allow photo upload for students in the form? (Optional field)
- [ ] Should we auto-calculate total cost? (Later feature)
- [ ] Should we collect payment info? (No - handle separately)

---

## Next Steps

1. Build Phase 1: Email capture form (simple HTML)
2. Build Shelf endpoints for link generation
3. Set up Resend email integration
4. Build Phase 2: SurveyJS enrollment form
5. Test end-to-end flow

---

**Ready to start building?** 🚀
