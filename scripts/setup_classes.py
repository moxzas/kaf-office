#!/usr/bin/env python3
"""
Setup Classes & Enrollments tables in Airtable
================================================

Verifies/creates the schema needed for class registration:
- Classes table (17 fields)
- Enrollments table (5 fields, lean junction table)
- Venues table seed data (5 known venues)

Workflow:
  1. verify        -- Check which tables exist, report missing fields
  2. create-tables -- Create missing tables/fields via Meta API
  3. seed-venues   -- Populate Venues with known locations (idempotent)

Usage:
    export AIRTABLE_API_KEY='pat...'
    python setup_classes.py verify
    python setup_classes.py create-tables
    python setup_classes.py seed-venues
"""

import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────

BASE_ID = "appNuMdxaiSYdgxJS"
AIRTABLE_API = "https://api.airtable.com/v0"
META_API = "https://api.airtable.com/v0/meta/bases"
BATCH_SIZE = 10
RATE_LIMIT_DELAY = 0.25

# ──────────────────────────────────────────────────────────────────────
# Known venues to seed
# ──────────────────────────────────────────────────────────────────────

VENUES = [
    {
        "Name": "Chapel Hill Art Studio",
        "Type": "Home Studio",
        "Suburb": "Chapel Hill",
    },
    {
        "Name": "Ironside State School",
        "Type": "School Rental",
        "Suburb": "St Lucia",
    },
    {
        "Name": "St Lucia Kindergarten",
        "Type": "School Rental",
        "Suburb": "St Lucia",
    },
    {
        "Name": "Yeronga State School",
        "Type": "School Rental",
        "Suburb": "Yeronga",
    },
    {
        "Name": "Good News Lutheran School",
        "Type": "School Rental",
        "Suburb": "Kenmore",
    },
]

# ──────────────────────────────────────────────────────────────────────
# Expected schemas
# ──────────────────────────────────────────────────────────────────────

CLASSES_FIELDS = [
    {"name": "Name", "type": "singleLineText", "description": "Class name, e.g. 'After School Art - Term 1 2026'"},
    {"name": "Type", "type": "singleSelect", "options": {"choices": [
        {"name": "Term", "color": "blueLight2"},
        {"name": "Holiday Program", "color": "orangeLight2"},
    ]}},
    {"name": "Category", "type": "singleSelect", "options": {"choices": [
        {"name": "Pottery", "color": "cyanLight2"},
        {"name": "Painting", "color": "blueLight2"},
        {"name": "Drawing", "color": "tealLight2"},
        {"name": "Sculpture", "color": "greenLight2"},
        {"name": "Mixed Media", "color": "yellowLight2"},
    ]}},
    {"name": "Day of Week", "type": "singleSelect", "options": {"choices": [
        {"name": "Monday", "color": "blueLight2"},
        {"name": "Tuesday", "color": "cyanLight2"},
        {"name": "Wednesday", "color": "tealLight2"},
        {"name": "Thursday", "color": "greenLight2"},
        {"name": "Friday", "color": "yellowLight2"},
        {"name": "Saturday", "color": "orangeLight2"},
        {"name": "Sunday", "color": "redLight2"},
    ]}},
    {"name": "Start Time", "type": "singleLineText", "description": "e.g. 3:30 PM"},
    {"name": "Duration (mins)", "type": "number", "options": {"precision": 0}},
    {"name": "Sessions in Term", "type": "number", "options": {"precision": 0}},
    {"name": "Price", "type": "currency", "options": {"precision": 2, "symbol": "$"}},
    {"name": "Capacity", "type": "number", "options": {"precision": 0}},
    {"name": "Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Active", "color": "greenLight2"},
        {"name": "Completed", "color": "grayLight2"},
        {"name": "Cancelled", "color": "redLight2"},
    ]}},
    {"name": "Term Start Date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Term End Date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
]

# Link fields and computed fields are added separately after table creation
CLASSES_LINK_FIELDS = [
    {"name": "Venue", "type": "multipleRecordLinks", "options": {"linkedTableId": None}},  # -> Venues
    {"name": "Teachers", "type": "multipleRecordLinks", "options": {"linkedTableId": None}},  # -> Teachers
]

ENROLLMENTS_FIELDS = [
    {"name": "Enrollment Date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
    {"name": "Payment Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Pending", "color": "yellowLight2"},
        {"name": "Paid", "color": "greenLight2"},
        {"name": "Cancelled", "color": "grayLight2"},
        {"name": "Refunded", "color": "redLight2"},
    ]}},
    {"name": "Notes", "type": "multilineText"},
]

ENROLLMENTS_LINK_FIELDS = [
    {"name": "Student", "type": "multipleRecordLinks", "options": {"linkedTableId": None}},  # -> Students
    {"name": "Class", "type": "multipleRecordLinks", "options": {"linkedTableId": None}},  # -> Classes
]


# ──────────────────────────────────────────────────────────────────────
# Helper: Airtable API (same pattern as import_contacts.py)
# ──────────────────────────────────────────────────────────────────────

def get_api_key():
    key = os.getenv("AIRTABLE_API_KEY")
    if not key:
        print("Error: AIRTABLE_API_KEY environment variable not set.")
        print("Get a token at https://airtable.com/create/tokens")
        print("Required scopes: data.records:read, data.records:write, schema.bases:read, schema.bases:write")
        sys.exit(1)
    return key


def airtable_request(method, url, api_key, data=None, retries=3):
    """Make an Airtable API request with retry on rate limit."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(retries):
        if method == "GET" and data:
            url_with_params = url + "?" + urlencode(data)
            body = None
        else:
            url_with_params = url
            body = json.dumps(data).encode("utf-8") if data else None

        req = Request(url_with_params, data=body, headers=headers, method=method)

        try:
            with urlopen(req) as resp:
                resp_body = resp.read().decode("utf-8")
                time.sleep(RATE_LIMIT_DELAY)
                return json.loads(resp_body)
        except HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", 30))
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                resp_body = e.read().decode("utf-8") if e.fp else ""
                print(f"  API error {e.code}: {resp_body[:500]}")
                raise

    raise Exception(f"Failed after {retries} retries")


# ──────────────────────────────────────────────────────────────────────
# Fetch base schema
# ──────────────────────────────────────────────────────────────────────

def fetch_schema(api_key):
    """Fetch all tables and fields from the Meta API."""
    url = f"{META_API}/{BASE_ID}/tables"
    resp = airtable_request("GET", url, api_key)
    tables = {}
    for t in resp.get("tables", []):
        fields = {f["name"]: f for f in t.get("fields", [])}
        tables[t["name"]] = {"id": t["id"], "fields": fields}
    return tables


# ──────────────────────────────────────────────────────────────────────
# Verify command
# ──────────────────────────────────────────────────────────────────────

def cmd_verify(api_key):
    """Check which tables/fields exist and report gaps."""
    print("=" * 60)
    print("Verifying Airtable schema for class registration")
    print("=" * 60)

    tables = fetch_schema(api_key)

    print(f"\nFound {len(tables)} tables: {', '.join(tables.keys())}\n")

    # Check required tables
    required = {
        "Classes": [f["name"] for f in CLASSES_FIELDS] + ["Venue", "Teachers", "Enrollments", "Current Enrollment", "Spots Remaining"],
        "Enrollments": ["Student", "Class"] + [f["name"] for f in ENROLLMENTS_FIELDS],
        "Venues": ["Name", "Type", "Address", "Suburb", "Capacity", "Contact/Access Notes", "Classes"],
        "Teachers": ["Name", "Email", "Phone", "Classes"],
        "Students": ["Name"],
        "Parents": ["Name", "Email"],
    }

    all_ok = True
    for table_name, expected_fields in required.items():
        if table_name not in tables:
            print(f"  MISSING TABLE: {table_name}")
            all_ok = False
        else:
            t = tables[table_name]
            print(f"  {table_name} (ID: {t['id']})")
            existing = set(t["fields"].keys())
            missing = [f for f in expected_fields if f not in existing]
            if missing:
                print(f"    Missing fields: {', '.join(missing)}")
                all_ok = False
            else:
                print(f"    All {len(expected_fields)} checked fields present")

    print()
    if all_ok:
        print("All tables and fields verified.")
    else:
        print("Some tables or fields are missing. Run 'create-tables' to fix.")

    return tables


# ──────────────────────────────────────────────────────────────────────
# Create tables command
# ──────────────────────────────────────────────────────────────────────

def cmd_create_tables(api_key):
    """Create missing tables and add missing fields."""
    print("=" * 60)
    print("Creating/updating tables for class registration")
    print("=" * 60)

    tables = fetch_schema(api_key)
    create_url = f"{META_API}/{BASE_ID}/tables"

    # ── Classes table ──
    if "Classes" not in tables:
        print("\nCreating Classes table...")
        schema = {
            "name": "Classes",
            "description": "Class schedules and details for registration",
            "fields": CLASSES_FIELDS,
        }
        resp = airtable_request("POST", create_url, api_key, schema)
        tables["Classes"] = {"id": resp["id"], "fields": {f["name"]: f for f in resp.get("fields", [])}}
        print(f"  Created Classes table (ID: {resp['id']})")
    else:
        print(f"\nClasses table exists (ID: {tables['Classes']['id']})")
        _add_missing_fields(api_key, tables["Classes"], CLASSES_FIELDS)

    # ── Enrollments table ──
    if "Enrollments" not in tables:
        print("\nCreating Enrollments table...")
        schema = {
            "name": "Enrollments",
            "description": "Student-class registration records",
            "fields": ENROLLMENTS_FIELDS,
        }
        resp = airtable_request("POST", create_url, api_key, schema)
        tables["Enrollments"] = {"id": resp["id"], "fields": {f["name"]: f for f in resp.get("fields", [])}}
        print(f"  Created Enrollments table (ID: {resp['id']})")
    else:
        print(f"\nEnrollments table exists (ID: {tables['Enrollments']['id']})")
        _add_missing_fields(api_key, tables["Enrollments"], ENROLLMENTS_FIELDS)

    # ── Venues table ──
    if "Venues" not in tables:
        print("\nVenues table missing! It should already exist from the original schema.")
        print("  Please create it manually in Airtable with fields: Name, Type, Address, Suburb, Capacity, Contact/Access Notes")
    else:
        print(f"\nVenues table exists (ID: {tables['Venues']['id']})")

    # ── Teachers table ──
    if "Teachers" not in tables:
        print("\nTeachers table missing! It should already exist from the original schema.")
        print("  Please create it manually in Airtable with fields: Name, Email, Phone")
    else:
        print(f"\nTeachers table exists (ID: {tables['Teachers']['id']})")

    # ── Add link fields ──
    # These need the target table IDs, so we do them after table creation
    print("\n--- Adding link fields ---")

    classes_id = tables["Classes"]["id"]
    enrollments_id = tables["Enrollments"]["id"]
    classes_fields = tables["Classes"]["fields"]
    enrollments_fields = tables["Enrollments"]["fields"]

    # Enrollments -> Students link
    if "Students" in tables and "Student" not in enrollments_fields:
        print("  Adding Student link to Enrollments...")
        _add_field(api_key, enrollments_id, {
            "name": "Student",
            "type": "multipleRecordLinks",
            "options": {"linkedTableId": tables["Students"]["id"]},
        })

    # Enrollments -> Classes link
    if "Class" not in enrollments_fields:
        print("  Adding Class link to Enrollments...")
        _add_field(api_key, enrollments_id, {
            "name": "Class",
            "type": "multipleRecordLinks",
            "options": {"linkedTableId": classes_id},
        })

    # Classes -> Venues link
    if "Venues" in tables and "Venue" not in classes_fields:
        print("  Adding Venue link to Classes...")
        _add_field(api_key, classes_id, {
            "name": "Venue",
            "type": "multipleRecordLinks",
            "options": {"linkedTableId": tables["Venues"]["id"]},
        })

    # Classes -> Teachers link
    if "Teachers" in tables and "Teachers" not in classes_fields:
        print("  Adding Teachers link to Classes...")
        _add_field(api_key, classes_id, {
            "name": "Teachers",
            "type": "multipleRecordLinks",
            "options": {"linkedTableId": tables["Teachers"]["id"]},
        })

    # ── Computed fields on Classes ──
    # Current Enrollment (count of Enrollments link)
    if "Enrollments" in classes_fields and "Current Enrollment" not in classes_fields:
        print("  Adding Current Enrollment count to Classes...")
        # Find the Enrollments field ID for the count
        enrollments_link_field = classes_fields.get("Enrollments")
        if enrollments_link_field:
            _add_field(api_key, classes_id, {
                "name": "Current Enrollment",
                "type": "count",
                "options": {"recordLinkFieldId": enrollments_link_field["id"]},
            })

    # Spots Remaining formula
    if "Spots Remaining" not in classes_fields and "Capacity" in classes_fields:
        print("  Adding Spots Remaining formula to Classes...")
        _add_field(api_key, classes_id, {
            "name": "Spots Remaining",
            "type": "formula",
            "options": {"formula": "IF({Capacity}, {Capacity} - {Current Enrollment}, '')"},
        })

    # Re-fetch to confirm
    print("\n--- Final verification ---")
    cmd_verify(api_key)


def _add_missing_fields(api_key, table_info, expected_fields):
    """Add any fields from expected_fields that are missing from the table."""
    existing = set(table_info["fields"].keys())
    table_id = table_info["id"]

    for field_def in expected_fields:
        if field_def["name"] not in existing:
            print(f"  Adding field: {field_def['name']}")
            _add_field(api_key, table_id, field_def)


def _add_field(api_key, table_id, field_def):
    """Add a single field to a table via Meta API."""
    url = f"{META_API}/{BASE_ID}/tables/{table_id}/fields"
    try:
        resp = airtable_request("POST", url, api_key, field_def)
        print(f"    Added: {resp.get('name', '?')} ({resp.get('type', '?')})")
        return resp
    except Exception as e:
        print(f"    Failed to add {field_def['name']}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────
# Seed venues command
# ──────────────────────────────────────────────────────────────────────

def cmd_seed_venues(api_key):
    """Populate Venues table with known locations (idempotent)."""
    print("=" * 60)
    print("Seeding Venues table")
    print("=" * 60)

    # Fetch existing venues
    url = f"{AIRTABLE_API}/{BASE_ID}/Venues"
    existing = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        resp = airtable_request("GET", url, api_key, params)
        existing.extend(resp.get("records", []))
        offset = resp.get("offset")
        if not offset:
            break

    existing_names = {r["fields"].get("Name", "") for r in existing}
    print(f"  Existing venues: {len(existing)} ({', '.join(sorted(existing_names)) or 'none'})")

    # Create missing venues
    to_create = [v for v in VENUES if v["Name"] not in existing_names]

    if not to_create:
        print("  All venues already exist. Nothing to do.")
        return

    print(f"  Creating {len(to_create)} venues...")
    records = [{"fields": v} for v in to_create]

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        resp = airtable_request("POST", url, api_key, {"records": batch})
        for r in resp.get("records", []):
            print(f"    Created: {r['fields'].get('Name', '?')} (ID: {r['id']})")

    print(f"  Done. {len(to_create)} venues created.")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    api_key = get_api_key()

    if command == "verify":
        cmd_verify(api_key)
    elif command == "create-tables":
        cmd_create_tables(api_key)
    elif command == "seed-venues":
        cmd_seed_venues(api_key)
    else:
        print(f"Unknown command: {command}")
        print("Commands: verify, create-tables, seed-venues")


if __name__ == "__main__":
    main()
