# TODO: Complete Base Setup

**Current Status:** ~85% complete
- ✅ 8 tables created (including Households)
- ✅ ~75 fields created automatically
- ⚠️ ~15 fields need manual addition (link fields, lookups, formulas)

**Time to complete:** 15-20 minutes

---

## Critical Path (Do in This Order)

### 1. Households Table (5 minutes)

**Add link fields:**

- [ ] **Residents (Parents)**
  - Type: Link to another record
  - Link to: Parents
  - Allow multiple: YES

- [ ] **Students**
  - Type: Link to another record
  - Link to: Students
  - Allow multiple: YES

---

### 2. Parents Table (3 minutes)

**Delete old address fields:**
- [ ] Delete "Address" (currently text field)
- [ ] Delete "Suburb" (currently text field)
- [ ] Delete "Postcode" (currently text field)

**Add new fields:**

- [ ] **Household**
  - Type: Link to another record
  - Link to: Households
  - Allow multiple: NO
  - When prompted: Click "Skip" for lookup

- [ ] **Address** (Lookup)
  - Type: Lookup
  - Get data from: Household
  - Field: Address

- [ ] **Suburb** (Lookup)
  - Type: Lookup
  - Get data from: Household
  - Field: Suburb

- [ ] **Postcode** (Lookup)
  - Type: Lookup
  - Get data from: Household
  - Field: Postcode

---

### 3. Students Table (3 minutes)

**Delete old address fields (if any exist):**
- [ ] Delete any existing "Address" lookup fields
- [ ] Delete any existing "Suburb" lookup fields
- [ ] Delete any existing "Postcode" lookup fields
- [ ] Delete "Primary Contact" text field (if exists)

**Add new fields:**

- [ ] **Household** (Lookup)
  - Type: Lookup
  - Get data from: Parents
  - Field: Household

- [ ] **Address** (Lookup)
  - Type: Lookup
  - Get data from: Parents
  - Field: Address

- [ ] **Suburb** (Lookup)
  - Type: Lookup
  - Get data from: Parents
  - Field: Suburb

- [ ] **Postcode** (Lookup)
  - Type: Lookup
  - Get data from: Parents
  - Field: Postcode

---

### 4. Classes Table (2 minutes)

- [ ] **Venue**
  - Type: Link to another record
  - Link to: Venues
  - Allow multiple: NO (single venue)

**Note:** "Current Enrollment" rollup already exists (shows as "count" in API - this is correct)

---

### 5. Enrollments Table (3 minutes)

**Fix primary field:**
- [ ] Delete "Enrollment ID" (currently text)
- [ ] Add new "Enrollment ID"
  - Type: Auto number

**Add missing fields:**

- [ ] **OSHC Collection**
  - Type: Checkbox

- [ ] **Sessions Remaining**
  - Type: Formula
  - Formula: `MAX(0, {Sessions Included} - {Sessions Attended})`

**Reconfigure existing link fields:**
- [ ] Click on "Student" field → Customize → Turn off "Allow multiple" → Rename to "Student" (singular)
- [ ] Click on "Class" field → Customize → Turn off "Allow multiple" → Rename to "Class" (singular)

---

### 6. Attendance Table (2 minutes)

- [ ] **Attendance ID**
  - Type: Auto number

- [ ] **Pickup Person**
  - Type: Link to another record
  - Link to: Parents
  - Allow multiple: NO (single person)

**Reconfigure existing link field:**
- [ ] Click on "Enrollment" field → Customize → Turn off "Allow multiple" → Rename to "Enrollment" (singular)

---

## Verification Checklist

After completing all items above:

- [ ] Run verification script:
  ```bash
  python3 verify_base.py
  ```

- [ ] All tables should show "✅ All expected fields present"

---

## Test Workflow

Create a test enrollment to verify everything works:

- [ ] **Step 1:** Create Household
  - Address: "123 Test St"
  - Suburb: "Brisbane"
  - Postcode: "4000"

- [ ] **Step 2:** Create Parent
  - Name: "Test Parent"
  - Email: "test@test.com"
  - Link to Household (123 Test St)
  - Verify: Address auto-populates via lookup

- [ ] **Step 3:** Create Student
  - Name: "Test Student"
  - Link to Parent (Test Parent)
  - Verify: Address auto-populates via lookup

- [ ] **Step 4:** Create Class (or use existing)
  - Link to Venue

- [ ] **Step 5:** Create Enrollment
  - Link Student (Test Student)
  - Link Class
  - Set Payment Status: Paid
  - Verify: Enrollment Name formula shows "Test Student → Class Name"

- [ ] **Step 6:** Create Attendance
  - Link Enrollment
  - Set Date: Today
  - Set Status: Present
  - Link Pickup Person (Test Parent)
  - Verify: Student and Class auto-populate via lookup

- [ ] **Step 7:** Verify Rollups
  - Classes → Current Enrollment shows "1"
  - Enrollments → Sessions Attended shows "1"

---

## Quick Reference: Field Types

**Link fields:**
- Create relationships between tables
- Can be one-to-many or many-to-many
- Auto-creates reverse link in target table

**Lookup fields:**
- Pull data from linked records
- Read-only
- Useful for displaying related data

**Formula fields:**
- Calculated values
- Examples: Student ID, Age, Sessions Remaining

**Rollup fields:**
- Aggregate data from linked records
- Examples: Current Enrollment (count), Sessions Attended (count)

---

## Summary

**Must add manually:**
- 6 link fields (relationships)
- 8 lookup fields (address chain)
- 2 auto number fields
- 1 formula field (Sessions Remaining)
- Fix 3 existing link fields (make singular)

**Total:** ~20 field additions/modifications

**Time:** 15-20 minutes

---

**Next:** Start with section 1 (Households), work through in order.

