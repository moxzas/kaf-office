#!/usr/bin/env python3
"""
Import parsed enrolment forms into Airtable Parents + Students tables.
=====================================================================

Reads data/parsed_enrolments.json (output of form parsing), deduplicates
against existing Airtable records, and creates new Parent/Student records.

Usage:
    export AIRTABLE_API_KEY='pat...'
    python scripts/import_enrolments.py dry-run     # Preview what would be created
    python scripts/import_enrolments.py import       # Create records in Airtable
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

BASE_ID = "appNuMdxaiSYdgxJS"
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}"
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "parsed_enrolments.json")

# Valid Venue values in Airtable Students table
VENUE_MAP = {
    "good news lutheran": "Good News Lutheran School",
    "good news": "Good News Lutheran School",
    "gnls": "Good News Lutheran School",
    "ironside": "Ironside State School",
    "ironside state school": "Ironside State School",
    "ironside ss": "Ironside State School",
    "chapel hill art studio": "Chapel Hill Art Studio",
    "chapel hill": "Chapel Hill Art Studio",
    "st lucia kindergarten": "St Lucia Kindergarten",
    "yeronga": "Yeronga State School",
    "yeronga state school": "Yeronga State School",
}


def get_api_key():
    key = os.getenv("AIRTABLE_API_KEY")
    if not key:
        print("Error: AIRTABLE_API_KEY environment variable not set.")
        print("  export AIRTABLE_API_KEY='pat...'")
        sys.exit(1)
    return key


def airtable_get(url, api_key):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def airtable_post(url, api_key, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_all_records(table_name, api_key, fields=None):
    """Fetch all records from a table, handling pagination."""
    records = []
    params = f"pageSize=100"
    if fields:
        for f in fields:
            params += f"&fields%5B%5D={urllib.request.quote(f)}"
    url = f"{BASE_URL}/{urllib.request.quote(table_name)}?{params}"

    while url:
        time.sleep(0.25)
        data = airtable_get(url, api_key)
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if offset:
            url = f"{BASE_URL}/{urllib.request.quote(table_name)}?{params}&offset={offset}"
        else:
            url = None
    return records


def normalize_email(email):
    if not email:
        return None
    return email.strip().lower()


def normalize_phone(phone):
    if not phone:
        return None
    # Strip spaces, dashes, dots, parens
    p = re.sub(r'[\s\-\.\(\)]', '', phone)
    # Fix +61 prefix
    if p.startswith('+61'):
        p = '0' + p[3:]
    # Ensure 10 digits for Aus mobile
    if len(p) == 10 and p.startswith('0'):
        return p
    return p  # return as-is if non-standard


def map_venue(venue_str):
    """Map free-text venue to valid Airtable single-select value."""
    if not venue_str:
        return "Other"
    key = venue_str.strip().lower()
    # Check for substring matches
    for pattern, value in VENUE_MAP.items():
        if pattern in key:
            return value
    return "Other"


def build_parent_record(form):
    """Build Airtable Parent fields from form data. Uses mother as primary parent."""
    mother = form.get("mother", {})
    father = form.get("father", {})

    # Pick primary parent: prefer mother, fall back to father
    primary = mother if mother.get("name") else father
    secondary = father if mother.get("name") else mother

    if not primary.get("name"):
        return None

    fields = {
        "Name": primary["name"],
        "Mobile": normalize_phone(primary.get("mobile")),
        "Email": normalize_email(primary.get("email")),
    }

    # Add address
    if form.get("address"):
        fields["Address"] = form["address"]
    if form.get("suburb"):
        fields["Suburb"] = form["suburb"]
    if form.get("postcode"):
        fields["Postcode"] = form["postcode"]

    # Store secondary parent + emergency info in Interest Notes for now
    notes_parts = []
    if secondary.get("name"):
        sec_info = f"Other parent: {secondary['name']}"
        if secondary.get("mobile"):
            sec_info += f", {normalize_phone(secondary['mobile'])}"
        if secondary.get("email"):
            sec_info += f", {secondary['email']}"
        notes_parts.append(sec_info)

    emergency = form.get("emergency_contacts", [])
    if emergency:
        ec_lines = []
        for ec in emergency:
            if ec.get("name") or ec.get("phone"):
                parts = [ec.get("name", "?"), ec.get("phone", "")]
                ec_lines.append(" ".join(p for p in parts if p))
        if ec_lines:
            notes_parts.append("Emergency contacts: " + "; ".join(ec_lines))

    if form.get("pickup_notes"):
        notes_parts.append(f"Pickup: {form['pickup_notes']}")

    if notes_parts:
        fields["Interest Notes"] = "\n".join(notes_parts)

    # Remove None values
    return {k: v for k, v in fields.items() if v is not None}


def build_student_record(student, form, parent_record_id):
    """Build Airtable Student fields from parsed student data."""
    fields = {
        "Name": student["name"],
        "Parents": [parent_record_id],
    }

    if student.get("dob"):
        fields["Date of Birth"] = student["dob"]

    # Map venue from form-level venue
    venue = map_venue(form.get("venue"))
    fields["Venue"] = venue

    if student.get("school"):
        fields["School Attended"] = student["school"]

    if student.get("year_class"):
        # Clean up year_class - remove class-specific info
        yc = student["year_class"]
        # Normalize common patterns
        yc = re.sub(r'^(Year|Grade|Y)\s*', 'Year ', yc, flags=re.IGNORECASE)
        yc = re.sub(r'\s+in\s+\d{4}$', '', yc)  # remove "in 2026"
        fields["Year/Class"] = yc

    medical = student.get("medical_notes")
    if medical and medical.lower() not in ("none", "no", "nil", "n/a", "na"):
        fields["Medical Notes"] = medical

    return fields


def load_forms():
    with open(DATA_FILE) as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("dry-run", "import"):
        print("Usage: python import_enrolments.py [dry-run|import]")
        sys.exit(1)

    mode = sys.argv[1]
    api_key = get_api_key()
    forms = load_forms()

    print(f"Loaded {len(forms)} enrolment forms")

    # Fetch existing parents and students
    print("Fetching existing Parents...")
    existing_parents = fetch_all_records("Parents", api_key, ["Name", "Email", "Mobile"])
    print(f"  Found {len(existing_parents)} existing parents")

    print("Fetching existing Students...")
    existing_students = fetch_all_records("Students", api_key, ["Name", "Date of Birth", "Parents"])
    print(f"  Found {len(existing_students)} existing students")

    # Build lookup indexes
    parent_by_email = {}
    parent_by_name = {}
    for rec in existing_parents:
        f = rec.get("fields", {})
        email = normalize_email(f.get("Email"))
        if email:
            parent_by_email[email] = rec["id"]
        name = f.get("Name", "").strip().lower()
        if name:
            parent_by_name[name] = rec["id"]

    student_names = set()
    for rec in existing_students:
        f = rec.get("fields", {})
        name = f.get("Name", "").strip().lower()
        dob = f.get("Date of Birth", "")
        student_names.add((name, dob))

    # Process forms
    new_parents = []
    new_students = []
    skipped_parents = []
    skipped_students = []

    for form in forms:
        parent_fields = build_parent_record(form)
        if not parent_fields:
            print(f"  SKIP (no parent data): {form['source_file']}")
            continue

        email = parent_fields.get("Email")
        name = parent_fields.get("Name", "").strip().lower()

        # Check if parent already exists
        existing_id = None
        if email and email in parent_by_email:
            existing_id = parent_by_email[email]
            skipped_parents.append((parent_fields["Name"], email, "email match"))
        elif name in parent_by_name:
            existing_id = parent_by_name[name]
            skipped_parents.append((parent_fields["Name"], email, "name match"))

        if existing_id:
            parent_id = existing_id
        else:
            new_parents.append((parent_fields, form))
            parent_id = f"__NEW_{len(new_parents)}__"
            # Add to index so siblings don't create duplicate parents
            if email:
                parent_by_email[email] = parent_id
            if name:
                parent_by_name[name] = parent_id

        # Process students
        for student in form.get("students", []):
            if not student.get("name"):
                continue
            sname = student["name"].strip().lower()
            sdob = student.get("dob", "")
            if (sname, sdob) in student_names:
                skipped_students.append((student["name"], sdob, "already exists"))
                continue
            student_names.add((sname, sdob))
            new_students.append((student, form, parent_id))

    # Report
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total forms parsed:    {len(forms)}")
    print(f"Existing parents:      {len(existing_parents)}")
    print(f"Existing students:     {len(existing_students)}")
    print(f"")
    print(f"Parents to CREATE:     {len(new_parents)}")
    print(f"Parents SKIPPED:       {len(skipped_parents)}")
    print(f"Students to CREATE:    {len(new_students)}")
    print(f"Students SKIPPED:      {len(skipped_students)}")

    if skipped_parents:
        print(f"\nSkipped parents (already in DB):")
        for name, email, reason in skipped_parents:
            print(f"  - {name} ({email}) [{reason}]")

    if skipped_students:
        print(f"\nSkipped students (already in DB):")
        for name, dob, reason in skipped_students:
            print(f"  - {name} (DOB: {dob}) [{reason}]")

    if new_parents:
        print(f"\nNew parents to create:")
        for fields, form in new_parents:
            print(f"  + {fields['Name']} ({fields.get('Email', 'no email')}) - {form['source_file']}")

    if new_students:
        print(f"\nNew students to create:")
        for student, form, pid in new_students:
            venue = map_venue(form.get("venue"))
            print(f"  + {student['name']} (DOB: {student.get('dob', '?')}) @ {venue}")

    if mode == "dry-run":
        print(f"\n[DRY RUN] No records created. Run with 'import' to create.")
        return

    # === IMPORT MODE ===
    print(f"\n{'='*60}")
    print(f"CREATING RECORDS")
    print(f"{'='*60}")

    # Create parents in batches of 10
    parent_id_map = {}  # __NEW_n__ -> actual record ID
    for i in range(0, len(new_parents), 10):
        batch = new_parents[i:i+10]
        records = [{"fields": fields} for fields, _ in batch]
        print(f"Creating parents batch {i//10 + 1} ({len(batch)} records)...")
        try:
            result = airtable_post(f"{BASE_URL}/Parents", api_key, {"records": records})
            for j, rec in enumerate(result.get("records", [])):
                placeholder = f"__NEW_{i+j+1}__"
                parent_id_map[placeholder] = rec["id"]
                real_name = batch[j][0]["Name"]
                print(f"  Created: {real_name} -> {rec['id']}")
                # Update indexes
                email = normalize_email(batch[j][0].get("Email"))
                if email:
                    parent_by_email[email] = rec["id"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  ERROR: {e.code} - {body}")
            continue
        time.sleep(0.25)

    # Create students in batches of 10
    for i in range(0, len(new_students), 10):
        batch = new_students[i:i+10]
        records = []
        for student, form, parent_id in batch:
            # Resolve placeholder parent IDs
            if parent_id.startswith("__NEW_"):
                actual_id = parent_id_map.get(parent_id)
                if not actual_id:
                    print(f"  SKIP student {student['name']}: parent not created")
                    continue
                parent_id = actual_id
            fields = build_student_record(student, form, parent_id)
            records.append({"fields": fields})

        if not records:
            continue

        print(f"Creating students batch {i//10 + 1} ({len(records)} records)...")
        try:
            result = airtable_post(f"{BASE_URL}/Students", api_key, {"records": records})
            for rec in result.get("records", []):
                print(f"  Created: {rec['fields'].get('Name', '?')} -> {rec['id']}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  ERROR: {e.code} - {body}")
            continue
        time.sleep(0.25)

    print(f"\nDone!")


if __name__ == "__main__":
    main()
