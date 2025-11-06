#!/usr/bin/env python3
"""
Inspect Existing Airtable Base Schema
======================================

This script reads the current base structure and generates a comparison report.

Usage:
    export AIRTABLE_API_KEY='your_token'
    python inspect_existing_base.py app1MhJmZGREczxSx
    python inspect_existing_base.py appj6RU7hVn11srUi
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any


def get_base_schema(api_key: str, base_id: str) -> Dict[str, Any]:
    """Fetch base schema using Airtable Meta API."""
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def format_field_type(field: Dict[str, Any]) -> str:
    """Format field type for readability."""
    field_type = field.get('type', 'unknown')

    # Add options for select fields
    if field_type in ['singleSelect', 'multipleSelects']:
        options = field.get('options', {}).get('choices', [])
        if options:
            choices = [opt['name'] for opt in options[:3]]
            if len(options) > 3:
                choices.append(f"...+{len(options)-3} more")
            return f"{field_type} ({', '.join(choices)})"

    # Add linked table info
    if field_type == 'multipleRecordLinks':
        linked_table = field.get('options', {}).get('linkedTableId', 'unknown')
        return f"Link to table {linked_table}"

    # Add formula preview
    if field_type == 'formula':
        formula = field.get('options', {}).get('formula', '')[:50]
        return f"formula: {formula}..."

    return field_type


def print_schema_report(base_id: str, schema: Dict[str, Any]):
    """Print formatted schema report."""
    print("\n" + "="*80)
    print(f"AIRTABLE BASE SCHEMA: {base_id}")
    print("="*80 + "\n")

    tables = schema.get('tables', [])

    print(f"Total Tables: {len(tables)}\n")

    for table in tables:
        table_name = table.get('name', 'Unknown')
        table_id = table.get('id', '')
        fields = table.get('fields', [])

        print(f"\n📋 {table_name} (ID: {table_id})")
        print("-" * 80)
        print(f"Fields: {len(fields)}\n")

        for field in fields:
            field_name = field.get('name', 'Unknown')
            field_type = format_field_type(field)
            field_id = field.get('id', '')

            print(f"  • {field_name}")
            print(f"    Type: {field_type}")
            print(f"    ID: {field_id}")
            print()

    # Save to file
    output_file = f"schema_inspection_{base_id}.json"
    with open(output_file, 'w') as f:
        json.dump(schema, f, indent=2)
    print(f"\n✓ Full schema saved to: {output_file}")


def main():
    """Main inspection function."""
    api_key = os.getenv('AIRTABLE_API_KEY')

    if not api_key:
        print("❌ Error: AIRTABLE_API_KEY environment variable not set")
        print("\nGet your token from: https://airtable.com/create/tokens")
        print("Then run: export AIRTABLE_API_KEY='your_token'")
        return

    if len(sys.argv) < 2:
        print("Usage: python inspect_existing_base.py <base_id>")
        print("\nBase IDs from your share links:")
        print("  app1MhJmZGREczxSx")
        print("  appj6RU7hVn11srUi")
        return

    base_id = sys.argv[1]

    try:
        print(f"Fetching schema for base: {base_id}...")
        schema = get_base_schema(api_key, base_id)
        print_schema_report(base_id, schema)

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 401:
            print("\nAuthentication failed. Check your API key has:")
            print("  • schema.bases:read scope")
            print("  • Access to this base")
        elif e.response.status_code == 404:
            print("\nBase not found. Check the base ID is correct.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    main()
