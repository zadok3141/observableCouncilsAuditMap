#!/usr/bin/env python3
"""
Preprocess the raw council audit CSV into a clean dataset.

Fixes:
1. Duplicate "Description 6" header → rename second to "Description 7"
2. Missing "Description 8" column → add it
3. Simplify type headers: strip parenthetical annotations → "Type 1" .. "Type 8"
4. Rename Nature headers to short form: "Nature 1" .. "Nature 6"
5. Rename "Type of audit report" → "Opinion type"
6. Fix Buller District Council's empty "Opinion type" → "Incomplete"
7. Drop the Address column (not needed at runtime)
8. Add Latitude/Longitude from council-coordinates.json
9. Fix Hawke's Bay Regional Council's offset data (Other Matter Paragraph
   data shifted due to the missing Description 8 column in source)
10. Clean nature values: normalise spacing, case, and labels

Usage:
    python scripts/preprocess_councils.py

Input:  Council-audit-data-April.csv
Output: src/data/CouncilsAuditData2025.csv
"""

import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_CSV = os.path.join(PROJECT_ROOT, "Council-audit-data-April.csv")
COORDS_JSON = os.path.join(PROJECT_ROOT, "src", "data",
                           "council-coordinates.json")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "src", "data",
                          "CouncilsAuditData2025.csv")

# Nature column renaming: raw header → clean header
NATURE_HEADER_MAP = {
    "Nature of qualified opinion 1": "Nature 1",
    "Nature of qualified opinion 2": "Nature 2",
    "Nature of qualified opinion 3": "Nature 3",
    "Nature of EoM 4": "Nature 4",
    "Nature of EoM 5": "Nature 5",
    "Nature of EoM 6": "Nature 6",
}

# Nature value cleanups applied to Nature 1-6
NATURE_CLEANUPS = {
    # Spacing fix
    "Service performance: Water services  - counting the number of complaints":
        "Service performance: Water services - counting the number of complaints",
    # Singular -> plural
    "Financial statement": "Financial statements",
    # Sentence case
    "Service performance: Flood Protection":
        "Service performance: Flood protection",
    # Three waters normalisation
    "Three waters assets":
        "Uncertainty over the fair value of three waters assets",
}

# Additional cleanup applied to EoM Nature columns (4-6) only
EOM_NATURE_CLEANUPS = {
    "Greenhouse gas emissions":
        "Inherent uncertainties in the measurement of greenhouse gas emissions",
}


def fix_headers(raw_headers):
    """Fix the raw CSV headers: deduplicate, rename, simplify."""
    fixed = []
    desc6_count = 0
    for h in raw_headers:
        h = h.strip()
        if h == "Description 6":
            desc6_count += 1
            if desc6_count == 2:
                fixed.append("Description 7")
                continue
        # Rename "Type of audit report" → "Opinion type"
        if h == "Type of audit report":
            fixed.append("Opinion type")
            continue
        # Rename Nature headers to short form
        if h in NATURE_HEADER_MAP:
            fixed.append(NATURE_HEADER_MAP[h])
            continue
        # Simplify Type headers: "Type 1 (qualified opinion)" → "Type 1"
        if h.startswith("Type ") and "(" in h:
            h = h.split("(")[0].strip()
        fixed.append(h)

    # Add missing Description 8 at the end
    if "Description 8" not in fixed:
        fixed.append("Description 8")

    return fixed


def fix_hawkes_bay(row):
    """
    Fix Hawke's Bay Regional Council's offset data.

    In the raw CSV, Hawke's Bay has "Other Matter Paragraph" in what becomes
    Description 7 (the renamed second "Description 6") and the actual description
    in what becomes Type 8. Description 8 is missing from the source.

    We need to move: Description 7 → Type 8, Type 8 → Description 8
    """
    if row.get("Council", "").strip() != "Hawke's Bay Regional Council":
        return row

    desc7 = row.get("Description 7", "").strip()
    type8 = row.get("Type 8", "").strip()

    # "Other Matter Paragraph" is a type value, not a description
    if desc7 == "Other Matter Paragraph":
        row["Description 7"] = ""
        row["Type 8"] = desc7  # "Other Matter Paragraph"
        row["Description 8"] = type8  # The actual description text
    return row


TYPE_LABEL_MAP = {
    "Qualified": "Qualified opinion",
    "Emphasis of Matter": "Emphasis of matter paragraph",
    "Key Audit Matter": "Key audit matter",
    "Other Matter Paragraph": "Other matter paragraph",
}


def relabel_types(row):
    """Rename type values to their display labels."""
    for i in range(1, 9):
        key = f"Type {i}"
        val = row.get(key, "").strip()
        if val in TYPE_LABEL_MAP:
            row[key] = TYPE_LABEL_MAP[val]
    return row


def clean_nature_values(row):
    """Normalise nature column values: spacing, case, labels."""
    for i in range(1, 7):
        key = f"Nature {i}"
        val = row.get(key, "").strip()
        if not val:
            continue
        # Apply general cleanups
        if val in NATURE_CLEANUPS:
            val = NATURE_CLEANUPS[val]
        # Apply EoM-specific cleanups (Nature 4-6 only)
        if i >= 4 and val in EOM_NATURE_CLEANUPS:
            val = EOM_NATURE_CLEANUPS[val]
        row[key] = val
    return row


def main():
    # Load coordinates
    with open(COORDS_JSON, "r", encoding="utf-8") as f:
        coordinates = json.load(f)

    # Read raw CSV — use raw field reading to handle header issues
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        raw_headers = next(reader)
        fixed_headers = fix_headers(raw_headers)

        rows = []
        for raw_row in reader:
            # Pad row to match fixed headers length
            while len(raw_row) < len(fixed_headers):
                raw_row.append("")
            row = dict(zip(fixed_headers, raw_row))
            rows.append(row)

    print(f"Read {len(rows)} rows")

    # Fix Buller's missing audit report type
    for row in rows:
        if row.get("Council", "").strip() == "Buller District Council":
            if not row.get("Opinion type", "").strip():
                row["Opinion type"] = "Incomplete"
                print(
                    "  Fixed Buller District Council: Opinion type → Incomplete"
                )

    # Fix Hawke's Bay offset
    for row in rows:
        old_desc7 = row.get("Description 7", "")
        fix_hawkes_bay(row)
        if row.get("Description 7", "") != old_desc7:
            print(
                "  Fixed Hawke's Bay Regional Council: shifted Other Matter Paragraph data"
            )

    # Relabel type values
    for row in rows:
        relabel_types(row)

    # Clean nature values
    for row in rows:
        clean_nature_values(row)

    # Build output
    output_headers = [h for h in fixed_headers if h != "Address"]
    output_headers += ["Latitude", "Longitude"]

    output_rows = []
    missing_coords = set()
    for row in rows:
        name = row.get("Council", "").strip()
        coord = coordinates.get(name, {})
        if not coord:
            missing_coords.add(name)

        out = {
            h: row.get(h, "").strip()
            for h in fixed_headers if h != "Address"
        }
        out["Latitude"] = str(coord.get("lat", ""))
        out["Longitude"] = str(coord.get("lng", ""))
        output_rows.append(out)

    if missing_coords:
        print(f"  WARNING: No coordinates for: {sorted(missing_coords)}")

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_headers)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} rows to {OUTPUT_CSV}")
    print(f"Columns: {output_headers}")


if __name__ == "__main__":
    main()
