# Airtable Manual Cleanup - Remove Households Table

**Goal:** Simplify schema by removing Households table and storing address directly on Parents.

---

## What Claude Can Do Via API ❌

Unfortunately, **nothing**. The Airtable API cannot:
- Delete tables
- Delete fields
- Add new fields
- Modify field types

The API can only:
- Create/read/update/delete **records** (data)
- Read schema (what fields exist)

So this is **100% manual work** in the Airtable UI.

---

## Manual Steps (You Do These)

### Step 1: Add Address Fields to Parents Table

Open **Parents** table, add these fields:

| Field Name | Field Type | Notes |
|------------|------------|-------|
| Address | Single line text | Street address |
| Suburb | Single line text | Suburb/city |
| Postcode | Single line text | 4-digit postcode |

**After adding, the old lookup fields will still exist (Address, Suburb, Postcode from Households). Don't delete them yet.**

### Step 2: Copy Data (If Any Real Data Exists)

If you have real parent records (not just test data):

1. Open each Parent record
2. Look at the **lookup fields** (Address, Suburb, Postcode from Households)
3. Copy those values
4. Paste into the **new direct fields** you just created
5. Repeat for each parent

**If no real data exists:** Skip this step, we'll start fresh.

### Step 3: Remove Household Links from Parents

1. In **Parents** table, find these fields:
   - `Household` (Link to Households)
   - `Address` (Lookup from Households) - OLD
   - `Suburb` (Lookup from Households) - OLD
   - `Postcode` (Lookup from Households) - OLD

2. **Delete these 4 fields** (click field name → delete field)

### Step 4: Remove Household Links from Students

1. In **Students** table, find these fields:
   - `Households` (Link to Households)
   - `Address` (Lookup from Households)
   - `Suburb` (Lookup from Households)
   - `Postcode` (Lookup from Households)

2. **Delete these 4 fields**

3. **Add new lookup fields** that point to Parents instead:
   - Field name: `Address`
   - Field type: Lookup
   - Look up field from: `Parents` → `Address`
   - Repeat for `Suburb` and `Postcode`

### Step 5: Delete Households Table

1. Click on **Households** table tab
2. Click the dropdown arrow next to table name
3. Select "Delete table"
4. Confirm deletion

### Step 6: Verify Schema

After cleanup, your tables should look like:

**Parents:**
- Name (text)
- Email (email)
- Phone (phone)
- Mobile (phone)
- **Address (text)** ← NEW direct field
- **Suburb (text)** ← NEW direct field
- **Postcode (text)** ← NEW direct field
- Authorized for Pickup (checkbox)
- Interest Categories (multiple select)
- Interest Notes (long text)
- Communication Log (long text)
- Students (link to Students)
- Attendance (link to Attendance)

**Students:**
- Name (text)
- Student ID Number (auto number)
- Student ID (formula)
- School (single select)
- Year/Class (text)
- Medical Notes (long text)
- Dietary Notes (long text)
- Special Needs (long text)
- Student Photo (attachment)
- General Notes (long text)
- Date of Birth (date)
- Age (formula)
- Parents (link to Parents)
- Enrollments (link to Enrollments)
- **Address (lookup from Parents)** ← Updated to point to Parents
- **Suburb (lookup from Parents)** ← Updated
- **Postcode (lookup from Parents)** ← Updated

---

## Verification Checklist

After completing the steps above:

- [ ] Parents table has direct Address, Suburb, Postcode fields (not lookups)
- [ ] Students table has Address, Suburb, Postcode as **lookups from Parents** (not Households)
- [ ] No references to Households table anywhere
- [ ] Households table is deleted
- [ ] Test: Create a new Parent record, add address directly
- [ ] Test: Link a Student to that Parent, verify address populates via lookup

---

## After Manual Cleanup

Once you've done the above, tell Claude:

**"Airtable cleanup done, check the new schema"**

Then I'll:
1. Inspect the updated schema via API
2. Verify everything is correct
3. Update the documentation (SCHEMA_V2.md)
4. Build the enrollment form based on the new schema

---

## Regarding Fees

You mentioned classes will have fees. The **Classes** table already has a `Price` field (currency type).

For now:
- Keep the Price field
- Enrollment form will just show class details (no prices yet)
- Later we can add price display + total calculation

**We'll walk before we run!** 🚶‍♂️

---

## Questions?

If anything is unclear, ask before making changes. The good news is you can't really break anything - Airtable has revision history and you can undo.

---

**Take your time with this. Let me know when it's done and I'll verify!**
