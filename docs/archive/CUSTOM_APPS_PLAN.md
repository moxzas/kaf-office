# Custom Apps Plan: Kids Art Fun CRM

## Architecture

```
┌─────────────────────────────────────────────┐
│  Flutter Apps                               │
│  ├─ Enrollment (Web - parents)              │
│  ├─ Attendance (Mobile - Sophia)            │
│  ├─ Parent Portal (Web - parents, future)   │
│  └─ Admin Dashboard (Web - Sophia, maybe)   │
└─────────────────────────────────────────────┘
                    ↓ HTTP/REST
┌─────────────────────────────────────────────┐
│  Dart Backend (Optional middleware)         │
│  ├─ /api/enroll (validation, Airtable)      │
│  ├─ /api/attendance (sync)                  │
│  └─ /api/students (search)                  │
└─────────────────────────────────────────────┘
                    ↓ Airtable REST API
┌─────────────────────────────────────────────┐
│  Airtable (Database + Admin UI)             │
│  ├─ 8 tables (~100 fields)                  │
│  ├─ Views for Sophia                        │
│  └─ Base ID: appNuMdxaiSYdgxJS              │
└─────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (Next Session)

### 1.1 Dart Airtable Client (~2 hours)

**File:** `packages/airtable_client/`

```dart
class AirtableClient {
  final String apiKey;
  final String baseId;

  Future<AirtableRecord> create(String table, Map<String, dynamic> fields);
  Future<AirtableRecord> get(String table, String recordId);
  Future<List<AirtableRecord>> list(String table, {String? filterFormula});
  Future<AirtableRecord> update(String table, String recordId, Map<String, dynamic> fields);
}
```

**Features:**
- Type-safe API calls
- Error handling
- Rate limiting (5 req/sec)
- Retry logic

---

### 1.2 Domain Models (~1 hour)

**File:** `packages/kaf_models/`

Generate from SCHEMA_V2.md:

```dart
class Household {
  final String? id;
  final String address;
  final String suburb;
  final String postcode;
  final List<String>? parentIds;
  final List<String>? studentIds;

  Map<String, dynamic> toAirtable() {
    return {
      'Address': address,
      'Suburb': suburb,
      'Postcode': postcode,
    };
  }

  factory Household.fromAirtable(AirtableRecord record) {
    // ...
  }
}

class Parent { /* ... */ }
class Student { /* ... */ }
class Enrollment { /* ... */ }
```

---

### 1.3 Validation Layer (~1 hour)

**File:** `packages/kaf_models/validation.dart`

```dart
class EnrollmentValidator {
  static ValidationResult validate(EnrollmentRequest req) {
    final errors = <String, String>{};

    // Parent
    if (req.parentEmail.isEmpty) errors['parentEmail'] = 'Required';
    if (!isValidEmail(req.parentEmail)) errors['parentEmail'] = 'Invalid email';

    // Student
    if (req.studentDOB.isAfter(DateTime.now())) {
      errors['studentDOB'] = 'Cannot be in future';
    }

    // Address
    if (req.postcode.length != 4) {
      errors['postcode'] = 'Must be 4 digits';
    }

    return ValidationResult(errors);
  }
}
```

---

## Phase 2: Enrollment App (Week 1)

### 2.1 Flutter Web Form (~6 hours)

**File:** `apps/enrollment_web/`

**Screens:**
1. **Parent Info**
   - Name, email, phone, mobile
   - Add second parent (optional)

2. **Address**
   - Street, suburb, postcode
   - Split custody? (checkbox → show second address)

3. **Student Info**
   - Name, DOB, school (dropdown), year/class
   - Medical notes, dietary, special needs
   - Photo upload
   - Add sibling (optional)

4. **Class Selection**
   - Show available classes (filtered by spots remaining)
   - Display: Schedule, price, capacity, location

5. **Additional Details**
   - Emergency contacts (2)
   - Photo permission
   - Marketing source
   - Special requests

6. **Review & Submit**
   - Show summary
   - Terms & conditions
   - Submit button

**Tech:**
- Form validation (use EnrollmentValidator)
- Progress indicator
- Mobile-responsive
- Loading states

---

### 2.2 Backend Endpoint (~4 hours)

**File:** `apps/enrollment_api/bin/server.dart`

```dart
@Route.post('/api/enroll')
Future<Response> enroll(Request request) async {
  // 1. Parse request
  final json = await request.readAsString();
  final data = EnrollmentRequest.fromJson(jsonDecode(json));

  // 2. Validate
  final validation = EnrollmentValidator.validate(data);
  if (!validation.isValid) {
    return Response.badRequest(body: jsonEncode(validation.errors));
  }

  // 3. Create records in Airtable
  final client = AirtableClient(apiKey, baseId);

  // 3a. Create Household(s)
  final household = await client.create('Households', {
    'Address': data.address,
    'Suburb': data.suburb,
    'Postcode': data.postcode,
  });

  // 3b. Create Parent(s)
  final parent1 = await client.create('Parents', {
    'Name': data.parent1Name,
    'Email': data.parent1Email,
    'Phone': data.parent1Phone,
    'Household': [household.id],
  });

  // 3c. Create Student
  final student = await client.create('Students', {
    'Name': data.studentName,
    'Date of Birth': data.studentDOB.toIso8601String(),
    'Parents': [parent1.id],
    'School': data.school,
    'Medical Notes': data.medicalNotes,
  });

  // 3d. Create Enrollment
  final enrollment = await client.create('Enrollments', {
    'Student': [student.id],
    'Class': [data.classId],
    'Payment Status': 'Pending',
    'Emergency Contact 1 Name': data.emergencyContact1Name,
    'Photo Permission': data.photoPermission,
    'Marketing Source': data.marketingSource,
  });

  // 4. Return success
  return Response.ok(jsonEncode({
    'success': true,
    'studentId': student.fields['Student ID'],
    'enrollmentId': enrollment.id,
  }));
}
```

**Deployment:**
- Cloud Run / Cloud Functions
- OR Vercel / Netlify Functions
- Environment vars: `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`

---

## Phase 3: Attendance App (Week 2)

### 3.1 Flutter Mobile App (~8 hours)

**File:** `apps/attendance_mobile/`

**Features:**

**Home Screen:**
```dart
ListView of today's classes:
┌──────────────────────────────────────┐
│ Monday Drawing (3:30-5:00 PM)        │
│ Ironside SS                          │
│ 12 enrolled • 0 marked today         │
└──────────────────────────────────────┘
```

**Class Detail Screen:**
```dart
Students enrolled:
☐ Emma Chen (STU-001)
☑ Rocky Lee (STU-002) - Present
    Signed in: 3:32 PM
    Picked up by: Sarah Chen (3:45 PM)
☐ Aanya Patel (STU-003)
```

**Mark Attendance:**
- Swipe right = Present (shows sign-in time)
- Swipe left = Absent
- Tap for menu (Late, Excused)
- Select pickup person (dropdown of parents)

**Offline Mode:**
- Cache today's classes on app open
- Queue attendance marks locally
- Sync to Airtable when online
- Show sync status indicator

**Tech:**
- Local DB: sqflite or hive
- State management: Riverpod or Bloc
- Sync logic: Queue pattern

---

## Phase 4: Optional Enhancements

### 4.1 Payment Integration
- Stripe checkout on enrollment
- Auto-update Payment Status when paid

### 4.2 Notifications
- SMS reminders (class tomorrow)
- Email receipts
- Push notifications (attendance app)

### 4.3 Waitlist
- When class is full, add to waitlist
- Auto-notify when spot opens

### 4.4 Re-enrollment
- Email to parents: "Term 2 starting, re-enroll?"
- Pre-filled form (just select new class)

---

## Development Timeline

### Week 1: Foundation + Enrollment
- [x] Airtable base complete
- [ ] Dart Airtable client (Day 1)
- [ ] Domain models (Day 1)
- [ ] Enrollment form UI (Day 2)
- [ ] Backend API (Day 3)
- [ ] Deploy + test (Day 3)

### Week 2: Attendance App
- [ ] Mobile UI (Day 4-5)
- [ ] Offline sync logic (Day 5)
- [ ] Testing (Day 6)
- [ ] Deploy to App Store / TestFlight (Day 6)

### Week 3: Polish + Handoff
- [ ] Documentation for Sophia
- [ ] Training session
- [ ] Monitor first real enrollments
- [ ] Fix issues

**Total: 3 weeks part-time or 1.5 weeks full-time**

---

## Tech Stack

**Frontend:**
- Flutter (Web + Mobile)
- State management: Riverpod
- Forms: flutter_form_builder
- HTTP: dio

**Backend:**
- Dart shelf (REST API)
- Hosted: Cloud Run or Vercel
- OR: Direct Airtable from Flutter (no backend)

**Database:**
- Airtable (REST API)
- Offline cache: sqflite (mobile)

**Deployment:**
- Web: Vercel / Netlify
- Mobile: TestFlight → App Store
- Backend: Cloud Run

**Auth (future):**
- Firebase Auth or Supabase
- Magic link email login

---

## Airtable API Details

**Base URL:** `https://api.airtable.com/v0/appNuMdxaiSYdgxJS`

**Headers:**
```
Authorization: Bearer patYJhlgK2q6sAnyZ...
Content-Type: application/json
```

**Rate Limits:**
- 5 requests/second
- 100k records/base
- 50k API calls/month (free tier)

**Key Endpoints:**
```
GET    /Households
POST   /Households
GET    /Students/{recordId}
PATCH  /Students/{recordId}
GET    /Classes?filterByFormula={Status}='Active'
```

---

## Next Steps

**This Session:**
1. ✅ Airtable base complete
2. ✅ Schema finalized

**Next Session:**
1. Generate Dart models from schema
2. Build Airtable client
3. Start enrollment form

**After That:**
- Build backend API
- Deploy enrollment app
- Build attendance app

---

## Questions to Decide

1. **Backend middleware or direct Airtable calls from Flutter?**
   - Middleware: More control, validation, hide API key
   - Direct: Simpler, fewer moving parts

2. **Monorepo or separate repos?**
   - Monorepo: Shared models/client
   - Separate: Simpler deploys

3. **Payment now or later?**
   - Now: Stripe integration from day 1
   - Later: Manual payment tracking first

4. **Mobile app priority?**
   - High: Build attendance app week 2
   - Low: Sophia uses Airtable UI for now

---

*Ready to build. Let me know when you want to start on the Dart/Flutter side.*
