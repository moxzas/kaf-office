# Schema Update V3 - Households Removed

**Date:** 2025-11-06
**Status:** ✅ Complete

---

## Changes from V2

### Removed
- ❌ **Households table** - Eliminated to simplify data model

### Modified

**Parents Table:**
- ✅ Address, Suburb, Postcode are now **direct fields** (singleLineText)
- ✅ No longer linked to Households

**Students Table:**
- ✅ Address, Suburb, Postcode are **lookups from Parents** (not Households)
- ✅ No longer linked to Households

---

## Current Schema (Verified 2025-11-06)

### 7 Tables

1. **Parents** - 13 fields
2. **Students** - 17 fields
3. **Venues** - 7 fields
4. **Teachers** - 8 fields
5. **Classes** - 17 fields
6. **Enrollments** - 24 fields
7. **Attendance** - 10 fields

---

## Parents Table (13 fields)

| Field Name | Type | Notes |
|------------|------|-------|
| Name | Single line text | Account holder name |
| Email | Email | Login identifier (passwordless) |
| Phone | Phone number | Optional |
| Mobile | Phone number | Required |
| **Address** | **Single line text** | Direct field (not lookup) |
| **Suburb** | **Single line text** | Direct field (not lookup) |
| **Postcode** | **Single line text** | Direct field (not lookup) |
| Authorized for Pickup | Checkbox | Default: true |
| Interest Categories | Multiple select | Marketing tracking |
| Interest Notes | Long text | Freeform notes |
| Communication Log | Long text | History |
| Students | Link to Students | Auto-populated |
| Attendance | Link to Attendance | Auto-populated |

**Note:** Students.Address/Suburb/Postcode lookup from Parents (one level, not through Households).

---

## Students Table (17 fields)

| Field Name | Type | Notes |
|------------|------|-------|
| Name | Single line text | Student name |
| Student ID Number | Auto number | Sequential |
| Student ID | Formula | STU-001, STU-002... |
| School | Single select | Ironside SS, St Lucia Kindy, etc. |
| Year/Class | Single line text | Year 3, Magpie 2, etc. |
| Medical Notes | Long text | Allergies, conditions |
| Dietary Notes | Long text | Food restrictions |
| Special Needs | Long text | Learning support |
| Student Photo | Attachment | Optional |
| General Notes | Long text | Miscellaneous |
| Date of Birth | Date | DD/MM/YYYY |
| Age | Formula | Calculated from DOB |
| Parents | Link to Parents | Multiple links allowed |
| Enrollments | Link to Enrollments | Auto-populated |
| **Address** | **Lookup from Parents** | Via Parents link |
| **Suburb** | **Lookup from Parents** | Via Parents link |
| **Postcode** | **Lookup from Parents** | Via Parents link |

**Note:** No "Households" link field. Address data comes directly from Parents.

---

## Rationale for Removing Households

**Problems with Households:**
- Over-complicated family situations (separated parents, multiple addresses)
- School doesn't need to track where kids live each week
- Added complexity for minimal benefit

**What we actually need:**
- One billing address (stored on Parents)
- List of authorized pickup people (stored per Enrollment)
- Emergency contacts (stored per Enrollment)

**Result:**
- Simpler data model
- Easier enrollment forms
- Focus on what school actually needs

---

## Impact on Enrollment Forms

**Simplified flow:**
1. Parent enters their address once
2. All students link to that parent
3. Students automatically inherit address via lookup
4. Per-enrollment: Add authorized pickups + emergency contacts

**No need to manage:**
- Multiple households per family
- Custody arrangements
- Where kids live this week

---

## Next Steps

- [x] Remove Households table
- [x] Verify schema cleanup
- [ ] Update enrollment form design
- [ ] Build Phase 1: Email capture
- [ ] Build Phase 2: Full enrollment

---

**Schema V3 is ready for enrollment form development!** 🎉
