# Audit Log Table - Airtable Schema

**Table Name:** `Audit Log`

---

## Purpose

Track all enrollment form submissions and changes for:
- Legal audit trail
- Debugging issues
- Understanding user behavior
- Email notification content

---

## Fields

| Field Name | Type | Description |
|------------|------|-------------|
| **Timestamp** | Date & Time | When the submission occurred (automatic) |
| **Action** | Single Select | `Created` or `Updated` |
| **Parent Record** | Link to Parents | Link to parent record |
| **Parent Email** | Email | Parent's email address (for easy searching) |
| **Parent Name** | Single Line Text | Parent's name at time of submission |
| **Before State** | Long Text | JSON snapshot of data before changes |
| **After State** | Long Text | JSON snapshot of data after changes |
| **Delta Summary** | Long Text | Human-readable summary of what changed |
| **Student Count** | Number | How many students in this submission |
| **IP Address** | Single Line Text | Client IP (optional, for security) |
| **User Agent** | Long Text | Browser/device info (optional) |
| **Processing Status** | Single Select | `Pending`, `Email Sent`, `Failed` |
| **Email Sent At** | Date & Time | When notification email was sent |
| **Error Message** | Long Text | Any errors that occurred |

---

## Sample Records

### Create Action
```json
{
  "Timestamp": "2025-11-06 15:30:00",
  "Action": "Created",
  "Parent Record": ["recABC123"],
  "Parent Email": "sarah@example.com",
  "Parent Name": "Sarah Johnson",
  "Before State": null,
  "After State": {
    "parent": {
      "Name": "Sarah Johnson",
      "Email": "sarah@example.com",
      "Mobile": "0444 444 444",
      "Address": "123 Main St",
      "Suburb": "Chapel Hill",
      "Postcode": "4069"
    },
    "students": [
      {
        "Name": "Emma Johnson",
        "DOB": "2015-03-15",
        "School": "Ironside State School"
      }
    ]
  },
  "Delta Summary": "New enrollment created\n• Parent: Sarah Johnson\n• Students: Emma Johnson (1 student)",
  "Student Count": 1,
  "Processing Status": "Email Sent",
  "Email Sent At": "2025-11-06 15:30:05"
}
```

### Update Action
```json
{
  "Timestamp": "2025-11-07 10:15:00",
  "Action": "Updated",
  "Parent Record": ["recABC123"],
  "Parent Email": "sarah@example.com",
  "Parent Name": "Sarah Johnson",
  "Before State": {
    "parent": {
      "Mobile": "0444 444 444",
      "Address": "123 Main St"
    },
    "students": [
      {"Name": "Emma Johnson"}
    ]
  },
  "After State": {
    "parent": {
      "Mobile": "0411 555 666",
      "Address": "456 New St"
    },
    "students": [
      {"Name": "Emma Johnson"},
      {"Name": "Noah Johnson"}
    ]
  },
  "Delta Summary": "Enrollment updated\n• Mobile changed: 0444 444 444 → 0411 555 666\n• Address changed: 123 Main St → 456 New St\n• Student added: Noah Johnson\n• Total students: 2",
  "Student Count": 2,
  "Processing Status": "Email Sent",
  "Email Sent At": "2025-11-07 10:15:03"
}
```

---

## Manual Setup Steps

1. **Create table in Airtable:**
   - Go to KAF base
   - Add new table: "Audit Log"

2. **Add fields** (in order):
   - Timestamp (Created time)
   - Action (Single select: Created, Updated)
   - Parent Record (Link to Parents)
   - Parent Email (Email)
   - Parent Name (Single line text)
   - Before State (Long text)
   - After State (Long text)
   - Delta Summary (Long text)
   - Student Count (Number)
   - IP Address (Single line text)
   - User Agent (Long text)
   - Processing Status (Single select: Pending, Email Sent, Failed)
   - Email Sent At (Date & time)
   - Error Message (Long text)

3. **Configure views:**
   - **All Logs** (default): Show all records, sorted by Timestamp descending
   - **Recent Changes** (last 7 days): Filter Timestamp > 7 days ago
   - **Failed Emails**: Filter Processing Status = Failed
   - **By Parent**: Group by Parent Record

---

## Programmatic Access

### Create Log Entry

```javascript
POST https://api.airtable.com/v0/{BASE_ID}/Audit%20Log

{
  "fields": {
    "Action": "Created",
    "Parent Record": ["recABC123"],
    "Parent Email": "sarah@example.com",
    "Parent Name": "Sarah Johnson",
    "After State": "{...JSON...}",
    "Delta Summary": "New enrollment created...",
    "Student Count": 1,
    "Processing Status": "Pending"
  }
}
```

### Update Processing Status

```javascript
PATCH https://api.airtable.com/v0/{BASE_ID}/Audit%20Log/{record_id}

{
  "fields": {
    "Processing Status": "Email Sent",
    "Email Sent At": "2025-11-06T15:30:05.000Z"
  }
}
```

---

## Delta Calculation Logic

Compare before/after state to generate human-readable summary:

```javascript
function calculateDelta(before, after) {
  const changes = [];

  // Parent changes
  if (before?.parent?.Mobile !== after.parent.Mobile) {
    changes.push(`Mobile changed: ${before.parent.Mobile} → ${after.parent.Mobile}`);
  }

  // Student changes
  const studentsBefore = before?.students?.length || 0;
  const studentsAfter = after.students.length;

  if (studentsAfter > studentsBefore) {
    const newStudents = after.students.slice(studentsBefore);
    newStudents.forEach(s => changes.push(`Student added: ${s.Name}`));
  }

  if (studentsBefore > studentsAfter) {
    changes.push(`Student removed (${studentsBefore - studentsAfter})`);
  }

  return changes.join('\n• ');
}
```

---

## Privacy & Retention

**Data Storage:**
- Audit logs contain full enrollment details
- Stored indefinitely for legal compliance
- Access restricted to Sophia (base owner)

**Compliance:**
- Parents consent to data storage via enrollment form
- Audit logs demonstrate proper record-keeping
- Can be exported if requested by parent

---

## Next Steps

1. ✅ Document schema (this file)
2. ⏳ Manually create table in Airtable
3. ⏳ Build server endpoint: POST /api/kaf/audit
4. ⏳ Integrate Resend for email sending
5. ⏳ Update enrollment form to call audit endpoint
