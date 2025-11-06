#!/usr/bin/env python3
"""
Verify the base is complete and correct.
"""

import requests
import json

API_KEY = 'patYJhlgK2q6sAnyZ.8c3945853082593f6ec6cc6d12a0cd863a13a912a067dfd99c75a0ff95ae4e06'
BASE_ID = 'appNuMdxaiSYdgxJS'

def get_schema():
    """Fetch current schema."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
    response = requests.get(url, headers=headers)
    return response.json()

def verify_table(table, expected_fields):
    """Check if table has expected fields."""
    actual_fields = {f['name']: f['type'] for f in table['fields']}

    missing = []
    incorrect_type = []

    for field_name, expected_type in expected_fields.items():
        if field_name not in actual_fields:
            missing.append(field_name)
        elif expected_type and actual_fields[field_name] != expected_type:
            incorrect_type.append(f"{field_name} (expected: {expected_type}, got: {actual_fields[field_name]})")

    return missing, incorrect_type, actual_fields

# Expected fields per table
EXPECTED = {
    'Households': {
        'Address': 'singleLineText',
        'Suburb': 'singleLineText',
        'Postcode': 'singleLineText',
        'Primary Contact': 'singleLineText',
        'Parents': 'multipleRecordLinks',
        'Students': 'multipleRecordLinks',
        'Notes': 'multilineText',
    },
    'Students': {
        'Name': 'singleLineText',
        'Student ID Number': 'autoNumber',
        'Student ID': 'formula',
        'Date of Birth': 'date',
        'Age': 'formula',
        'Parents': 'multipleRecordLinks',
        'Households': 'multipleRecordLinks',
        'Address': 'multipleLookupValues',
        'Suburb': 'multipleLookupValues',
        'Postcode': 'multipleLookupValues',
        'School': 'singleSelect',
        'Year/Class': 'singleLineText',
        'Medical Notes': 'multilineText',
        'Dietary Notes': 'multilineText',
        'Special Needs': 'multilineText',
        'Student Photo': 'multipleAttachments',
        'General Notes': 'multilineText',
        'Enrollments': 'multipleRecordLinks',
    },
    'Parents': {
        'Name': 'singleLineText',
        'Email': 'email',
        'Phone': 'phoneNumber',
        'Mobile': 'phoneNumber',
        'Household': 'multipleRecordLinks',
        'Address': 'multipleLookupValues',
        'Suburb': 'multipleLookupValues',
        'Postcode': 'multipleLookupValues',
        'Authorized for Pickup': 'checkbox',
        'Interest Categories': 'multipleSelects',
        'Interest Notes': 'multilineText',
        'Communication Log': 'multilineText',
        'Students': 'multipleRecordLinks',
    },
    'Venues': {
        'Name': 'singleLineText',
        'Type': 'singleSelect',
        'Address': 'multilineText',
        'Suburb': 'singleLineText',
        'Capacity': 'number',
        'Contact/Access Notes': 'multilineText',
        'Classes': 'multipleRecordLinks',
    },
    'Teachers': {
        'Name': 'singleLineText',
        'Email': 'email',
        'Phone': 'phoneNumber',
        'Address': 'singleLineText',
        'Suburb': 'singleLineText',
        'Postcode': 'singleLineText',
        'Notes': 'multilineText',
        'Classes': 'multipleRecordLinks',
    },
    'Classes': {
        'Name': 'singleLineText',
        'Type': 'singleSelect',
        'Category': 'singleSelect',
        'Day of Week': 'singleSelect',
        'Start Time': 'singleLineText',
        'Duration (mins)': 'number',
        'Term Start Date': 'date',
        'Term End Date': 'date',
        'Sessions in Term': 'number',
        'Price': 'currency',
        'Capacity': 'number',
        'Status': 'singleSelect',
        'Venue': 'multipleRecordLinks',
        'Teachers': 'multipleRecordLinks',
        'Enrollments': 'multipleRecordLinks',
        'Current Enrollment': 'count',
        'Spots Remaining': 'formula',
    },
    'Enrollments': {
        'Enrollment ID': 'autoNumber',
        'Student': 'multipleRecordLinks',
        'Class': 'multipleRecordLinks',
        'Enrollment Date': 'date',
        'Payment Status': 'singleSelect',
        'Amount Paid': 'currency',
        'Sessions Included': 'number',
        'Emergency Contact 1 Name': 'singleLineText',
        'Emergency Contact 1 Relationship': 'singleLineText',
        'Emergency Contact 1 Phone': 'phoneNumber',
        'Emergency Contact 2 Name': 'singleLineText',
        'Emergency Contact 2 Relationship': 'singleLineText',
        'Emergency Contact 2 Phone': 'phoneNumber',
        'Photo Permission': 'singleSelect',
        'OSHC Collection': 'checkbox',
        'Approved Pickup People': 'multilineText',
        'Marketing Source': 'singleSelect',
        'Special Requests': 'multilineText',
        'Additional Notes': 'multilineText',
        'Attendance Records': 'multipleRecordLinks',
        'Enrollment Name': 'formula',
        'Sessions Attended': 'rollup',
        'Sessions Remaining': 'formula',
        'Attendance Rate': 'formula',
    },
    'Attendance': {
        'Attendance ID': 'autoNumber',
        'Date': 'date',
        'Status': 'singleSelect',
        'Sign-in Time': 'dateTime',
        'Sign-out Time': 'dateTime',
        'Notes': 'multilineText',
        'Enrollment': 'multipleRecordLinks',
        'Pickup Person': 'multipleRecordLinks',
        'Student': 'multipleLookupValues',
        'Class': 'multipleLookupValues',
    },
}

def main():
    """Run verification."""
    print("="*80)
    print("VERIFYING BASE STRUCTURE")
    print("="*80 + "\n")

    schema = get_schema()
    tables = {t['name']: t for t in schema['tables']}

    all_good = True

    for table_name, expected_fields in EXPECTED.items():
        if table_name not in tables:
            print(f"❌ TABLE MISSING: {table_name}\n")
            all_good = False
            continue

        table = tables[table_name]
        missing, incorrect, actual = verify_table(table, expected_fields)

        print(f"📋 {table_name}")
        print(f"   Fields: {len(actual)}/{len(expected_fields)} expected")

        if missing:
            print(f"   ❌ Missing fields ({len(missing)}):")
            for f in missing:
                print(f"      - {f}")
            all_good = False

        if incorrect:
            print(f"   ⚠️  Incorrect types:")
            for f in incorrect:
                print(f"      - {f}")

        if not missing and not incorrect:
            print(f"   ✅ All expected fields present")

        print()

    print("="*80)
    if all_good:
        print("✅ BASE IS COMPLETE!")
        print("="*80)
        print("\nNext steps:")
        print("1. Import sample data (optional)")
        print("2. Create views from VIEWS.md")
        print("3. Test creating: Parent → Student → Enrollment → Attendance")
    else:
        print("⚠️  SOME FIELDS MISSING")
        print("="*80)
        print("\nReview MANUAL_FIXUP.md and add missing fields.")

if __name__ == '__main__':
    main()
