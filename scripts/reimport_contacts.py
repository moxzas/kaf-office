#!/usr/bin/env python3
"""
Reimport Contacts table from JSON dump
========================================

Restores the Contacts table from data/contacts_reimport.json.
Run this after recreating the Contacts table (use import_contacts.py create-table).

Usage:
    export AIRTABLE_API_KEY='pat...'
    python reimport_contacts.py              # dry-run (show count)
    python reimport_contacts.py --go         # import all records
    python reimport_contacts.py --link       # re-link Parent Record field
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

BASE_ID = "appNuMdxaiSYdgxJS"
AIRTABLE_API = "https://api.airtable.com/v0"
BATCH_SIZE = 10
RATE_LIMIT_DELAY = 0.25

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
REIMPORT_FILE = PROJECT_DIR / "data" / "contacts_reimport.json"


def get_api_key():
    key = os.getenv("AIRTABLE_API_KEY")
    if not key:
        print("Error: AIRTABLE_API_KEY not set.")
        sys.exit(1)
    return key


def airtable_request(method, url, api_key, data=None):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if method == "GET" and data:
        url = url + "?" + urlencode(data)
        body = None
    else:
        body = json.dumps(data).encode("utf-8") if data else None

    for attempt in range(3):
        req = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                time.sleep(RATE_LIMIT_DELAY)
                return result
        except HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", 30))
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  API error {e.code}: {e.read().decode()[:300]}")
                raise
    raise Exception("Failed after retries")


def cmd_import(api_key):
    records = json.loads(REIMPORT_FILE.read_text())
    total = len(records)
    url = f"{AIRTABLE_API}/{BASE_ID}/Contacts"
    created = 0

    print(f"Importing {total} records in batches of {BATCH_SIZE}...")
    for i in range(0, total, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        resp = airtable_request("POST", url, api_key, {"records": batch})
        n = len(resp.get("records", []))
        created += n
        print(f"  Batch {batch_num}/{total_batches}: +{n} ({created}/{total})")

    print(f"\nDone: {created} records imported.")


def cmd_link(api_key):
    """Re-link contacts to Parent records by email."""
    # Fetch parents
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

    parent_by_email = {}
    for p in parents:
        email = p.get("fields", {}).get("Email", "").strip().lower()
        if email:
            parent_by_email[email] = p["id"]
    print(f"Found {len(parent_by_email)} parents with emails")

    # Fetch contacts
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

    # Match
    updates = []
    for c in contacts:
        email = c.get("fields", {}).get("Email", "").strip().lower()
        if email in parent_by_email:
            updates.append({
                "id": c["id"],
                "fields": {"Parent Record": [parent_by_email[email]]}
            })

    print(f"Matched {len(updates)} contacts to parents")
    for i in range(0, len(updates), BATCH_SIZE):
        batch = updates[i:i + BATCH_SIZE]
        airtable_request("PATCH", contacts_url, api_key, {"records": batch})
        print(f"  Linked batch {(i // BATCH_SIZE) + 1}")

    print("Done.")


def main():
    if not REIMPORT_FILE.exists():
        print(f"Error: {REIMPORT_FILE} not found. Run the dump first.")
        sys.exit(1)

    records = json.loads(REIMPORT_FILE.read_text())

    if len(sys.argv) < 2 or sys.argv[1] not in ("--go", "--link"):
        print(f"Contacts reimport: {len(records)} records ready in {REIMPORT_FILE}")
        print(f"  Est. time: ~{len(records) // BATCH_SIZE * 0.25:.0f}s")
        print()
        print("Steps to restore:")
        print("  1. python import_contacts.py create-table")
        print("  2. Add 'Parent Record' link field in Airtable UI (Contacts -> Parents)")
        print("  3. python reimport_contacts.py --go")
        print("  4. python reimport_contacts.py --link")
        return

    api_key = get_api_key()

    if sys.argv[1] == "--go":
        cmd_import(api_key)
    elif sys.argv[1] == "--link":
        cmd_link(api_key)


if __name__ == "__main__":
    main()
