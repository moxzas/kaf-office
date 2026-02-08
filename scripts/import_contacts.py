#!/usr/bin/env python3
"""
Import Wix CSV data into Airtable Contacts table
==================================================

Reads contacts.csv and Booking list CSV, cleans/deduplicates/maps,
then creates records in the Contacts table via Airtable API.

Workflow:
  1. create-table  -- Create the Contacts table in Airtable (run once)
  2. dry-run       -- Parse CSVs, show stats, write preview JSON (no API calls)
  3. import        -- Push records to Airtable (includes synthetic parents)
  4. link-parents  -- Match contacts to existing Parent records by email
  5. create-views  -- Create filtered views for mailing list workflows

Usage:
    export AIRTABLE_API_KEY='pat...'
    python import_contacts.py create-table
    # Then in Airtable UI: add 'Parent Record' link field on Contacts -> Parents
    python import_contacts.py dry-run
    python import_contacts.py import
    python import_contacts.py link-parents
    python import_contacts.py create-views
"""

import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────

BASE_ID = "appNuMdxaiSYdgxJS"
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CONTACTS_CSV = str(PROJECT_DIR / "data" / "contacts.csv")
BOOKINGS_CSV = str(PROJECT_DIR / "data" / "bookings.csv")
AIRTABLE_API = "https://api.airtable.com/v0"
BATCH_SIZE = 10  # Airtable max per request
RATE_LIMIT_DELAY = 0.25  # seconds between API calls (5 req/sec limit)

# ──────────────────────────────────────────────────────────────────────
# Venue normalization: Company field value -> canonical venue name
# ──────────────────────────────────────────────────────────────────────

VENUE_MAP = {
    # Ironside variants
    "ironside ss": "Ironside SS",
    "ironside state school": "Ironside SS",
    "ironside": "Ironside SS",
    # Chapel Hill variants
    "chapel hill art studio": "Chapel Hill",
    "chapel hill ss": "Chapel Hill",
    "chapel hill": "Chapel Hill",
    # Good News Lutheran variants
    "good news lutheran school": "Good News Lutheran",
    "good news lutheran": "Good News Lutheran",
    "gnls": "Good News Lutheran",
    # Yeronga variants
    "yeronga ss": "Yeronga",
    "yeronga state school": "Yeronga",
    "yeronga": "Yeronga",
    # Holiday variants
    "holiday art class": "Holiday Program",
    "holiday art": "Holiday Program",
    "holiday class": "Holiday Program",
    "holiday": "Holiday Program",
    # Saturday
    "saturday art&craft": "Saturday Class",
    "saturday art class": "Saturday Class",
    # St Lucia
    "st lucia community hall": "St Lucia",
}

# Booking location -> venue
LOCATION_VENUE_MAP = {
    "kids art fun, nankoor street, chapel hill qld, australia": "Chapel Hill",
    "st lucia community hall": "St Lucia",
    "chapel hill art studio": "Chapel Hill",
    "online live class": "Online",
}

# ──────────────────────────────────────────────────────────────────────
# Class interest keyword detection
# ──────────────────────────────────────────────────────────────────────

INTEREST_KEYWORDS = {
    "Painting": ["painting", "paint", "watercolour", "watercolor", "acrylic"],
    "Drawing": ["drawing", "draw", "sketch"],
    "Pottery": ["pottery", "ceramic", "clay"],
    "Sculpture": ["sculpture", "sculpt", "figure", "model"],
    "Mixed Media": ["mixed media", "art&craft", "art & craft", "craft", "collage", "tie-dye", "tie dye"],
    "Holiday Workshops": ["holiday", "easter", "christmas", "winter", "spring", "summer"],
    "Term Classes": ["term "],
    "After School": ["after school", "afterschool"],
}

# ──────────────────────────────────────────────────────────────────────
# Source mapping: Wix Source -> Contacts table Source
# ──────────────────────────────────────────────────────────────────────

SOURCE_MAP = {
    "Form Submission": "Form Submission",
    "Service Booking": "Service Booking",
    "Contact Import": "Contact Import",
    "Site Members": "Site Member",
    "External App": "Contact Import",
    "Wix Stores": "Service Booking",
    "Manual Creation": "Manual",
    "Other": "Contact Import",
    "Chat Form Submission": "Form Submission",
}

# ──────────────────────────────────────────────────────────────────────
# Email status mapping
# ──────────────────────────────────────────────────────────────────────

EMAIL_STATUS_MAP = {
    "Subscribed": "Subscribed",
    "Unsubscribed": "Unsubscribed",
    "Never subscribed": "Never Subscribed",
    "Bounced": "Bounced",
    "": "Never Subscribed",
}

# Email status priority for dedup (worst wins = highest number)
EMAIL_STATUS_PRIORITY = {
    "Subscribed": 0,
    "Never Subscribed": 1,
    "Unsubscribed": 2,
    "Bounced": 3,
}


# ──────────────────────────────────────────────────────────────────────
# Helper: Airtable API
# ──────────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.getenv("AIRTABLE_API_KEY")
    if not key:
        print("Error: AIRTABLE_API_KEY environment variable not set.")
        print("Get a token at https://airtable.com/create/tokens")
        print("Required scopes: data.records:read, data.records:write, schema.bases:write")
        sys.exit(1)
    return key


def airtable_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def airtable_request(method: str, url: str, api_key: str, data: dict = None,
                      retries: int = 3) -> dict:
    """Make an Airtable API request with retry on rate limit (stdlib only)."""
    headers = airtable_headers(api_key)

    for attempt in range(retries):
        if method == "GET" and data:
            # Append query params to URL
            from urllib.parse import urlencode
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
# Name cleaning
# ──────────────────────────────────────────────────────────────────────

def clean_name(first: str, last: str) -> Tuple[str, Optional[str]]:
    """
    Parse name fields, handling the child(parent) pattern.

    Returns (contact_name, child_note_or_none).

    Patterns detected:
      - "Heidi Huynh" / "(Eva Zhang)"   -> name="Eva Zhang", note="Child: Heidi Huynh"
      - "Heidi" / "Huynh (Eva Zhang)"   -> name="Eva Zhang", note="Child: Heidi Huynh"
      - "Sarah" / "Johnson"             -> name="Sarah Johnson", note=None
      - "Sarah" / ""                    -> name="Sarah", note=None
    """
    first = first.strip()
    last = last.strip()

    # Check for parenthetical pattern in last name
    paren_match = re.search(r'\(([^)]+)\)', last)
    if paren_match:
        parent_name = paren_match.group(1).strip()
        # The part before parens is child's last name
        child_last = re.sub(r'\s*\([^)]+\)\s*', '', last).strip()
        child_name = f"{first} {child_last}".strip() if child_last else first
        return _title_case(parent_name), f"Child: {_title_case(child_name)}"

    # Check for parenthetical pattern in first name (less common)
    paren_match = re.search(r'\(([^)]+)\)', first)
    if paren_match:
        parent_name = paren_match.group(1).strip()
        child_first = re.sub(r'\s*\([^)]+\)\s*', '', first).strip()
        child_name = f"{child_first} {last}".strip()
        return _title_case(parent_name), f"Child: {_title_case(child_name)}"

    # Standard name
    full = f"{first} {last}".strip()
    if not full:
        return "", None
    return _title_case(full), None


def _title_case(name: str) -> str:
    """Smart title case that handles McX, O'X patterns."""
    if not name:
        return name
    # If already mixed case (not all upper or all lower), leave it
    if name != name.upper() and name != name.lower():
        return name
    return name.title()


# ──────────────────────────────────────────────────────────────────────
# Label parsing -> structured fields
# ──────────────────────────────────────────────────────────────────────

def parse_labels(labels_str: str) -> Tuple[Set[str], Set[str], List[str]]:
    """
    Parse semicolon-separated labels into structured categories.

    Returns (contact_types, class_interests, overflow_labels).
    """
    contact_types: Set[str] = set()
    class_interests: Set[str] = set()
    overflow: List[str] = []

    if not labels_str.strip():
        return contact_types, class_interests, overflow

    for label in labels_str.split(";"):
        label = label.strip()
        if not label:
            continue

        label_lower = label.lower()

        # Contact type labels
        if label in ("Customers", "Students", "Organizations", "Family"):
            if label == "Customers":
                contact_types.add("Past Student Family")
            elif label == "Students":
                contact_types.add("Past Student Family")
            elif label == "Organizations":
                contact_types.add("Inquiry")
            elif label == "Family":
                contact_types.add("Current Family")
            continue

        # Gmail/email campaign labels -> Email Subscriber
        if label_lower.startswith("gmail"):
            contact_types.add("Email Subscriber")
            continue

        # "Contacted Me" label
        if label_lower == "contacted me":
            contact_types.add("Inquiry")
            continue

        # Try to match interest keywords
        matched_interest = False
        for interest, keywords in INTEREST_KEYWORDS.items():
            if any(kw in label_lower for kw in keywords):
                class_interests.add(interest)
                matched_interest = True
                break

        if not matched_interest:
            # Check if it looks like a class/term label
            if re.match(r"term \d", label_lower) or "class" in label_lower:
                class_interests.add("Term Classes")
            else:
                overflow.append(label)

    return contact_types, class_interests, overflow


def map_company_to_venue(company: str) -> Optional[str]:
    """Map Company field value to canonical venue name."""
    if not company.strip():
        return None
    key = company.strip().lower()
    return VENUE_MAP.get(key)


def map_location_to_venue(location: str) -> Optional[str]:
    """Map booking location to canonical venue name."""
    if not location.strip():
        return None
    key = location.strip().lower()
    return LOCATION_VENUE_MAP.get(key)


def detect_interests_from_service(service_name: str) -> Set[str]:
    """Detect class interest keywords from booking service name."""
    interests = set()
    if not service_name:
        return interests
    sn_lower = service_name.lower()
    for interest, keywords in INTEREST_KEYWORDS.items():
        if any(kw in sn_lower for kw in keywords):
            interests.add(interest)
    return interests


def map_email_status(raw_status: str) -> str:
    """Map Wix email subscriber status to Contacts table value."""
    return EMAIL_STATUS_MAP.get(raw_status.strip(), "Never Subscribed")


def map_source(raw_source: str) -> str:
    """Map Wix source to Contacts table source."""
    return SOURCE_MAP.get(raw_source.strip(), "Contact Import")


def derive_contact_type(source: str, has_bookings: bool) -> Set[str]:
    """Derive contact type from source and booking presence."""
    types: Set[str] = set()
    if has_bookings:
        types.add("Past Student Family")
    if source == "Form Submission":
        types.add("Inquiry")
    if source == "Site Member":
        types.add("Site Member")
    if source == "Contact Import":
        types.add("Imported List")
    return types


# ──────────────────────────────────────────────────────────────────────
# CSV Loading
# ──────────────────────────────────────────────────────────────────────

def load_contacts(path: str) -> List[Dict[str, str]]:
    """Load contacts.csv with BOM handling."""
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_bookings(path: str) -> List[Dict[str, Any]]:
    """Load bookings CSV and flatten form fields into a clean dict."""
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    cleaned = []
    for row in rows:
        rec = {
            "email": row.get("Email", "").strip().lower(),
            "first_name": row.get("First Name", "").strip(),
            "last_name": row.get("Last Name", "").strip(),
            "phone": row.get("Phone", "").strip(),
            "service_name": row.get("Service Name", "").strip(),
            "service_type": row.get("Service Type", "").strip(),
            "location": row.get("Location Address", "").strip(),
            "order_total": row.get("Order Total", "").strip(),
            "booking_date": row.get("Booking Start Time", "").strip(),
            "registration_date": row.get("Registration Date", "").strip(),
        }
        # Flatten form fields
        forms = {}
        for i in range(40):
            fn = row.get(f"Form Field {i}", "").strip()
            fv = row.get(f"Form Response {i}", "").strip()
            if fn and fv:
                forms[fn] = fv
        rec["form_fields"] = forms
        cleaned.append(rec)
    return cleaned


# ──────────────────────────────────────────────────────────────────────
# Build enriched booking data indexed by email
# ──────────────────────────────────────────────────────────────────────

def index_bookings(bookings: List[Dict]) -> Dict[str, Dict]:
    """
    Group bookings by email and aggregate:
      - venues (set)
      - interests (set)
      - booking_count (int)
      - total_spend (float)
      - latest_booking (str date)
    """
    by_email: Dict[str, Dict] = {}

    for b in bookings:
        email = b["email"]
        if not email:
            continue

        if email not in by_email:
            by_email[email] = {
                "venues": set(),
                "interests": set(),
                "booking_count": 0,
                "total_spend": 0.0,
                "latest_booking": "",
                "parent_name": "",
                "child_info": "",
            }

        rec = by_email[email]
        rec["booking_count"] += 1

        # Parse order total
        total_str = b["order_total"].replace("AU$", "").replace(",", "").strip()
        try:
            rec["total_spend"] += float(total_str)
        except ValueError:
            pass

        # Venue from location
        venue = map_location_to_venue(b["location"])
        if venue:
            rec["venues"].add(venue)

        # Interests from service name
        rec["interests"].update(detect_interests_from_service(b["service_name"]))

        # Latest booking date
        if b["booking_date"] and b["booking_date"] > rec["latest_booking"]:
            rec["latest_booking"] = b["booking_date"]

        # Form fields
        forms = b["form_fields"]
        if forms.get("Parent's Name"):
            rec["parent_name"] = forms["Parent's Name"]
        if forms.get("Child's Age and Class"):
            rec["child_info"] = forms["Child's Age and Class"]

    return by_email


# ──────────────────────────────────────────────────────────────────────
# Build contact records
# ──────────────────────────────────────────────────────────────────────

def build_contact_records(contacts: List[Dict], booking_index: Dict[str, Dict]) -> List[Dict]:
    """
    Transform raw CSV rows into Airtable-ready contact records.
    Handles deduplication by email.
    """
    # Group contacts by normalized email
    by_email: Dict[str, List[Dict]] = defaultdict(list)
    no_email = []
    for c in contacts:
        email = c.get("Email 1", "").strip().lower()
        if email:
            by_email[email].append(c)
        else:
            no_email.append(c)

    records = []

    for email, dupes in by_email.items():
        record = _merge_contact_dupes(email, dupes, booking_index)
        if record:
            records.append(record)

    # Skip contacts with no email (can't dedup or link them usefully)
    # But log count for transparency
    print(f"  Skipped {len(no_email)} contacts with no email")

    return records


def _merge_contact_dupes(email: str, dupes: List[Dict],
                         booking_index: Dict[str, Dict]) -> Optional[Dict]:
    """Merge duplicate contact rows for the same email into one record."""

    # Start with the most recently active row
    dupes.sort(key=lambda x: x.get("Last Activity Date (UTC+0)", ""), reverse=True)
    primary = dupes[0]

    # Name: use first non-empty from most recent
    first_name = ""
    last_name = ""
    for d in dupes:
        fn = d.get("First Name", "").strip()
        ln = d.get("Last Name", "").strip()
        if fn or ln:
            first_name = fn
            last_name = ln
            break

    name, child_note = clean_name(first_name, last_name)

    # If name is still empty, try to get from bookings
    if not name:
        bdata = booking_index.get(email, {})
        if bdata.get("parent_name"):
            name = _title_case(bdata["parent_name"])

    # Phone: first non-empty
    phone = ""
    for d in dupes:
        p = d.get("Phone 1", "").strip()
        if p:
            phone = p
            break

    # Suburb: from address fields
    suburb = ""
    for d in dupes:
        city = d.get("Address 1 - City", "").strip()
        if city:
            suburb = city
            break

    # Email status: worst status wins (most restrictive)
    worst_status = "Subscribed"
    worst_priority = 0
    for d in dupes:
        status = map_email_status(d.get("Email subscriber status", ""))
        priority = EMAIL_STATUS_PRIORITY.get(status, 1)
        if priority > worst_priority:
            worst_priority = priority
            worst_status = status

    # Source: from primary (most recent)
    source = map_source(primary.get("Source", ""))

    # Created date: earliest
    created_dates = [d.get("Created At (UTC+0)", "") for d in dupes if d.get("Created At (UTC+0)")]
    created = min(created_dates) if created_dates else ""

    # Last activity: latest
    activity_dates = [d.get("Last Activity Date (UTC+0)", "") for d in dupes
                      if d.get("Last Activity Date (UTC+0)")]
    last_activity = max(activity_dates) if activity_dates else ""

    # Aggregate labels from all dupes
    all_contact_types: Set[str] = set()
    all_interests: Set[str] = set()
    all_overflow: List[str] = []
    all_venues: Set[str] = set()

    for d in dupes:
        labels_str = d.get("Labels", "")
        ct, ci, overflow = parse_labels(labels_str)
        all_contact_types.update(ct)
        all_interests.update(ci)
        all_overflow.extend(overflow)

        # Venue from Company
        venue = map_company_to_venue(d.get("Company", ""))
        if venue:
            all_venues.add(venue)

    # Derive additional contact types from source
    has_bookings = email in booking_index
    all_contact_types.update(derive_contact_type(source, has_bookings))

    # Enrich from bookings
    if has_bookings:
        bdata = booking_index[email]
        all_venues.update(bdata["venues"])
        all_interests.update(bdata["interests"])

    # Build notes
    notes_parts = []
    if child_note:
        notes_parts.append(child_note)
    if all_overflow:
        # Deduplicate overflow
        unique_overflow = list(dict.fromkeys(all_overflow))
        if len(unique_overflow) > 10:
            notes_parts.append(f"Wix labels: {'; '.join(unique_overflow[:10])}... (+{len(unique_overflow)-10} more)")
        else:
            notes_parts.append(f"Wix labels: {'; '.join(unique_overflow)}")
    if has_bookings:
        bdata = booking_index[email]
        notes_parts.append(f"Bookings: {bdata['booking_count']}, Total: AU${bdata['total_spend']:.0f}")
        if bdata.get("child_info"):
            if not child_note:
                notes_parts.append(f"Child info: {bdata['child_info']}")

    notes = "\n".join(notes_parts) if notes_parts else ""

    # Wix Contact ID (from primary row -- Wix doesn't export this in the CSV
    # we have, so we skip it)

    # Parse dates to ISO format
    created_iso = _parse_wix_date(created)
    last_activity_iso = _parse_wix_date(last_activity)

    # Build Airtable record
    fields: Dict[str, Any] = {}

    if name:
        fields["Name"] = name
    fields["Email"] = email
    if phone:
        fields["Phone"] = phone
    if suburb:
        fields["Suburb"] = suburb
    if worst_status:
        fields["Email Status"] = worst_status
    if all_contact_types:
        fields["Contact Type"] = sorted(all_contact_types)
    if all_interests:
        fields["Class Interests"] = sorted(all_interests)
    if all_venues:
        fields["Venues"] = sorted(all_venues)
    if source:
        fields["Source"] = source
    if last_activity_iso:
        fields["Last Activity"] = last_activity_iso
    if created_iso:
        fields["Created"] = created_iso
    if notes:
        fields["Notes"] = notes

    return {"fields": fields}


def _parse_wix_date(date_str: str) -> str:
    """Parse Wix date format '2019-01-21 11:52' to ISO date 'YYYY-MM-DD'."""
    if not date_str or not date_str.strip():
        return ""
    try:
        # Format: "2019-01-21 11:52"
        dt = datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return ""


# ──────────────────────────────────────────────────────────────────────
# Create Contacts table in Airtable
# ──────────────────────────────────────────────────────────────────────

def create_contacts_table(api_key: str):
    """Create the Contacts table via Airtable Meta API."""
    url = f"{AIRTABLE_API}/meta/bases/{BASE_ID}/tables"

    table_schema = {
        "name": "Contacts",
        "description": "CRM/mailing list contacts imported from Wix and other sources",
        "fields": [
            {
                "name": "Name",
                "type": "singleLineText",
                "description": "Contact name (parent/guardian name)"
            },
            {
                "name": "Email",
                "type": "email",
                "description": "Primary email address"
            },
            {
                "name": "Phone",
                "type": "phoneNumber",
                "description": "Primary phone number"
            },
            {
                "name": "Suburb",
                "type": "singleLineText",
                "description": "Suburb/city from address or company field"
            },
            {
                "name": "Email Status",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Subscribed", "color": "greenLight2"},
                        {"name": "Unsubscribed", "color": "redLight2"},
                        {"name": "Bounced", "color": "orangeLight2"},
                        {"name": "Never Subscribed", "color": "grayLight2"},
                    ]
                }
            },
            {
                "name": "Contact Type",
                "type": "multipleSelects",
                "options": {
                    "choices": [
                        {"name": "Email Subscriber", "color": "blueLight2"},
                        {"name": "Past Student Family", "color": "cyanLight2"},
                        {"name": "Inquiry", "color": "tealLight2"},
                        {"name": "Current Family", "color": "greenLight2"},
                        {"name": "Imported List", "color": "grayLight2"},
                        {"name": "Site Member", "color": "purpleLight2"},
                    ]
                }
            },
            {
                "name": "Class Interests",
                "type": "multipleSelects",
                "options": {
                    "choices": [
                        {"name": "Painting", "color": "blueLight2"},
                        {"name": "Drawing", "color": "cyanLight2"},
                        {"name": "Pottery", "color": "tealLight2"},
                        {"name": "Sculpture", "color": "greenLight2"},
                        {"name": "Mixed Media", "color": "yellowLight2"},
                        {"name": "Holiday Workshops", "color": "orangeLight2"},
                        {"name": "Term Classes", "color": "redLight2"},
                        {"name": "After School", "color": "pinkLight2"},
                    ]
                }
            },
            {
                "name": "Venues",
                "type": "multipleSelects",
                "options": {
                    "choices": [
                        {"name": "Ironside SS", "color": "blueLight2"},
                        {"name": "Chapel Hill", "color": "cyanLight2"},
                        {"name": "Good News Lutheran", "color": "tealLight2"},
                        {"name": "Yeronga", "color": "greenLight2"},
                        {"name": "Holiday Program", "color": "orangeLight2"},
                        {"name": "Saturday Class", "color": "yellowLight2"},
                        {"name": "St Lucia", "color": "purpleLight2"},
                        {"name": "Online", "color": "grayLight2"},
                    ]
                }
            },
            {
                "name": "Source",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Form Submission", "color": "blueLight2"},
                        {"name": "Service Booking", "color": "cyanLight2"},
                        {"name": "Contact Import", "color": "grayLight2"},
                        {"name": "Site Member", "color": "purpleLight2"},
                        {"name": "Enrollment Form", "color": "greenLight2"},
                        {"name": "Manual", "color": "yellowLight2"},
                    ]
                }
            },
            {
                "name": "Last Activity",
                "type": "date",
                "options": {
                    "dateFormat": {"name": "iso"}
                }
            },
            {
                "name": "Created",
                "type": "date",
                "options": {
                    "dateFormat": {"name": "iso"}
                }
            },
            {
                "name": "Notes",
                "type": "multilineText",
                "description": "Overflow labels, child info, booking summary"
            },
        ]
    }

    print("Creating Contacts table...")
    resp = airtable_request("POST", url, api_key, table_schema)
    table_id = resp.get("id", "unknown")
    print(f"  Created table: {resp.get('name')} (ID: {table_id})")
    print(f"  Fields created: {len(resp.get('fields', []))}")
    return table_id


# ──────────────────────────────────────────────────────────────────────
# Import records to Airtable
# ──────────────────────────────────────────────────────────────────────

def import_records(api_key: str, records: List[Dict]):
    """Batch import records to Contacts table."""
    url = f"{AIRTABLE_API}/{BASE_ID}/Contacts"
    total = len(records)
    created = 0
    errors = 0

    print(f"\nImporting {total} records in batches of {BATCH_SIZE}...")

    for i in range(0, total, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        try:
            resp = airtable_request("POST", url, api_key, {"records": batch})
            batch_created = len(resp.get("records", []))
            created += batch_created
            print(f"  Batch {batch_num}/{total_batches}: {batch_created} records created ({created}/{total})")
        except Exception as e:
            errors += len(batch)
            print(f"  Batch {batch_num}/{total_batches}: ERROR - {e}")
            # Log the failed batch for retry
            error_file = f"/tmp/kaf_import_errors_batch_{batch_num}.json"
            with open(error_file, "w") as f:
                json.dump(batch, f, indent=2)
            print(f"    Failed batch saved to {error_file}")

    print(f"\nImport complete: {created} created, {errors} errors out of {total} total")
    return created, errors


# ──────────────────────────────────────────────────────────────────────
# Link contacts to existing Parents records
# ──────────────────────────────────────────────────────────────────────

def link_parents(api_key: str):
    """
    Match contacts to existing Parent records by email.
    This requires the Contacts table to have a 'Parent Record' link field
    which must be created manually in Airtable (link fields require both
    tables to exist first).
    """
    print("\nFetching Parents records...")
    parents_url = f"{AIRTABLE_API}/{BASE_ID}/Parents"
    parents = []
    offset = None

    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        resp = airtable_request("GET", parents_url, api_key, params)
        parents.extend(resp.get("records", []))
        offset = resp.get("offset")
        if not offset:
            break

    print(f"  Found {len(parents)} parent records")

    # Index parents by email (lowercase)
    parent_by_email = {}
    for p in parents:
        email = p.get("fields", {}).get("Email", "").strip().lower()
        if email:
            parent_by_email[email] = p["id"]

    print(f"  {len(parent_by_email)} parents with email addresses")

    # Fetch contacts
    print("\nFetching Contacts records...")
    contacts_url = f"{AIRTABLE_API}/{BASE_ID}/Contacts"
    contacts = []
    offset = None

    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        resp = airtable_request("GET", contacts_url, api_key, params)
        contacts.extend(resp.get("records", []))
        offset = resp.get("offset")
        if not offset:
            break

    print(f"  Found {len(contacts)} contact records")

    # Match and update
    updates = []
    for c in contacts:
        email = c.get("fields", {}).get("Email", "").strip().lower()
        if email in parent_by_email:
            updates.append({
                "id": c["id"],
                "fields": {
                    "Parent Record": [parent_by_email[email]]
                }
            })

    print(f"\n  Matched {len(updates)} contacts to parent records")

    if not updates:
        print("  No matches found. Nothing to update.")
        return

    # Batch update
    for i in range(0, len(updates), BATCH_SIZE):
        batch = updates[i:i + BATCH_SIZE]
        resp = airtable_request("PATCH", contacts_url, api_key, {"records": batch})
        print(f"  Updated batch {(i // BATCH_SIZE) + 1}: {len(resp.get('records', []))} records")

    print(f"  Parent linking complete: {len(updates)} contacts linked")


# ──────────────────────────────────────────────────────────────────────
# Synthetic contacts for enrolled parents not in Wix
# ──────────────────────────────────────────────────────────────────────

def add_synthetic_parents(api_key: str, existing_emails: Set[str]):
    """
    For enrolled parents whose emails are NOT already in the import set,
    create synthetic contact records from the Parents table.
    """
    print("\nChecking for enrolled parents not in Wix export...")
    parents_url = f"{AIRTABLE_API}/{BASE_ID}/Parents"
    parents = []
    offset = None

    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        resp = airtable_request("GET", parents_url, api_key, params)
        parents.extend(resp.get("records", []))
        offset = resp.get("offset")
        if not offset:
            break

    synthetic = []
    for p in parents:
        fields = p.get("fields", {})
        email = fields.get("Email", "").strip().lower()
        if not email or email in existing_emails:
            continue

        rec = {"fields": {
            "Name": fields.get("Name", ""),
            "Email": email,
            "Email Status": "Subscribed",
            "Contact Type": ["Current Family"],
            "Source": "Enrollment Form",
        }}
        if fields.get("Mobile"):
            rec["fields"]["Phone"] = fields["Mobile"]
        if fields.get("Suburb"):
            rec["fields"]["Suburb"] = fields["Suburb"]
        rec["fields"]["Notes"] = "Added from enrollment form (not in Wix export)"
        rec["fields"]["Created"] = datetime.now().strftime("%Y-%m-%d")
        synthetic.append(rec)

    print(f"  Found {len(parents)} enrolled parents, {len(synthetic)} not in Wix export")
    return synthetic


# ──────────────────────────────────────────────────────────────────────
# Create Airtable views
# ──────────────────────────────────────────────────────────────────────

def print_view_instructions():
    """Print instructions for creating views in Airtable UI.

    Note: The Airtable API does not support creating views programmatically.
    Views must be created manually in the Airtable interface.
    """
    print("\n" + "=" * 70)
    print("CREATE THESE VIEWS IN AIRTABLE UI")
    print("=" * 70)
    print("\nOpen the Contacts table, click '+' next to the view tabs,")
    print("choose 'Grid view', name it, then set the filter.\n")

    views = [
        ("All Active Subscribers",
         "Email Status = Subscribed",
         "General newsletter"),
        ("Holiday Workshop List",
         "Email Status = Subscribed AND (Class Interests contains 'Holiday Workshops' OR Venues contains 'Holiday Program')",
         "Holiday announcements"),
        ("Ironside SS Families",
         "Email Status = Subscribed AND Venues contains 'Ironside SS'",
         "Term reminders"),
        ("Chapel Hill Families",
         "Email Status = Subscribed AND Venues contains 'Chapel Hill'",
         "Term reminders"),
        ("Good News Lutheran",
         "Email Status = Subscribed AND Venues contains 'Good News Lutheran'",
         "Term reminders"),
        ("Yeronga Families",
         "Email Status = Subscribed AND Venues contains 'Yeronga'",
         "Term reminders"),
        ("Current Families",
         "Contact Type contains 'Current Family'",
         "Enrolled families"),
        ("Do Not Email",
         "Email Status = Unsubscribed",
         "Reference only"),
    ]

    for name, filter_desc, use_case in views:
        print(f"  {name}")
        print(f"    Filter: {filter_desc}")
        print(f"    Use: {use_case}")
        print()


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    # Load and process CSVs (needed for dry-run and import)
    if command in ("dry-run", "import"):
        print("=" * 70)
        print("KAF Contacts Import")
        print("=" * 70)

        print(f"\nLoading {CONTACTS_CSV}...")
        contacts_raw = load_contacts(CONTACTS_CSV)
        print(f"  {len(contacts_raw)} rows")

        print(f"\nLoading {BOOKINGS_CSV}...")
        bookings_raw = load_bookings(BOOKINGS_CSV)
        print(f"  {len(bookings_raw)} rows")

        print("\nIndexing bookings by email...")
        booking_index = index_bookings(bookings_raw)
        print(f"  {len(booking_index)} unique booking customers")

        print("\nBuilding contact records...")
        records = build_contact_records(contacts_raw, booking_index)
        print(f"  {len(records)} deduplicated contact records")

        # Statistics
        print("\n" + "-" * 40)
        print("STATISTICS")
        print("-" * 40)

        with_name = sum(1 for r in records if r["fields"].get("Name"))
        with_phone = sum(1 for r in records if r["fields"].get("Phone"))
        with_suburb = sum(1 for r in records if r["fields"].get("Suburb"))
        with_interests = sum(1 for r in records if r["fields"].get("Class Interests"))
        with_venues = sum(1 for r in records if r["fields"].get("Venues"))
        with_notes = sum(1 for r in records if r["fields"].get("Notes"))

        print(f"  Total records: {len(records)}")
        print(f"  With name: {with_name} ({100*with_name/len(records):.1f}%)")
        print(f"  With phone: {with_phone} ({100*with_phone/len(records):.1f}%)")
        print(f"  With suburb: {with_suburb} ({100*with_suburb/len(records):.1f}%)")
        print(f"  With interests: {with_interests} ({100*with_interests/len(records):.1f}%)")
        print(f"  With venues: {with_venues} ({100*with_venues/len(records):.1f}%)")
        print(f"  With notes: {with_notes} ({100*with_notes/len(records):.1f}%)")

        # Email status breakdown
        status_counts = Counter()
        for r in records:
            status_counts[r["fields"].get("Email Status", "")] += 1
        print(f"\n  Email status:")
        for k, v in status_counts.most_common():
            print(f"    {k}: {v}")

        # Source breakdown
        source_counts = Counter()
        for r in records:
            source_counts[r["fields"].get("Source", "")] += 1
        print(f"\n  Source:")
        for k, v in source_counts.most_common():
            print(f"    {k}: {v}")

        # Contact type breakdown
        type_counts = Counter()
        for r in records:
            for t in r["fields"].get("Contact Type", []):
                type_counts[t] += 1
        print(f"\n  Contact types:")
        for k, v in type_counts.most_common():
            print(f"    {k}: {v}")

        # Venue breakdown
        venue_counts = Counter()
        for r in records:
            for v_name in r["fields"].get("Venues", []):
                venue_counts[v_name] += 1
        print(f"\n  Venues:")
        for k, v in venue_counts.most_common():
            print(f"    {k}: {v}")

        # Interest breakdown
        interest_counts = Counter()
        for r in records:
            for i_name in r["fields"].get("Class Interests", []):
                interest_counts[i_name] += 1
        print(f"\n  Class interests:")
        for k, v in interest_counts.most_common():
            print(f"    {k}: {v}")

        if command == "dry-run":
            # Write preview
            preview_file = "/tmp/kaf_contacts_preview.json"
            with open(preview_file, "w") as f:
                json.dump(records[:20], f, indent=2)
            print(f"\n  Preview (first 20) saved to: {preview_file}")

            full_file = "/tmp/kaf_contacts_all.json"
            with open(full_file, "w") as f:
                json.dump(records, f, indent=2)
            print(f"  Full export saved to: {full_file}")
            print(f"\n  API calls needed: ~{(len(records) + BATCH_SIZE - 1) // BATCH_SIZE}")
            print(f"\n  Note: Synthetic parents from enrollment form will be added")
            print(f"  during 'import' (requires API call to fetch Parents table).")

        elif command == "import":
            api_key = get_api_key()

            # Add synthetic contacts for enrolled parents not in Wix
            existing_emails = {r["fields"]["Email"] for r in records}
            synthetic = add_synthetic_parents(api_key, existing_emails)
            if synthetic:
                records.extend(synthetic)
                print(f"  Total records after adding synthetic parents: {len(records)}")

            print("\n" + "=" * 40)
            print("IMPORTING TO AIRTABLE")
            print("=" * 40)
            confirm = input(f"\nImport {len(records)} records to Contacts table? [y/N] ")
            if confirm.lower() != "y":
                print("Aborted.")
                return
            import_records(api_key, records)

    elif command == "create-table":
        api_key = get_api_key()
        table_id = create_contacts_table(api_key)
        print(f"\nNext steps:")
        print(f"  1. In Airtable, add a 'Parent Record' Link field in Contacts -> Parents")
        print(f"  2. Run: python import_contacts.py dry-run")
        print(f"  3. Run: python import_contacts.py import")
        print(f"  4. Run: python import_contacts.py link-parents")
        print(f"  5. Run: python import_contacts.py create-views")

    elif command == "link-parents":
        api_key = get_api_key()
        link_parents(api_key)

    elif command == "create-views":
        print_view_instructions()

    else:
        print(f"Unknown command: {command}")
        print("Commands: create-table, dry-run, import, link-parents, create-views")


if __name__ == "__main__":
    main()
