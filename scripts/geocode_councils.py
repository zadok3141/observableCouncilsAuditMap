#!/usr/bin/env python3
"""
One-time geocoding script to produce council-coordinates.json.

Uses geopy + Nominatim (OpenStreetMap) to geocode each council name.
Query format: "<council name>, New Zealand"

Usage:
    pip install geopy
    python scripts/geocode_councils.py

Output: src/data/council-coordinates.json
"""

import csv
import json
import os
import time
import urllib.request
import urllib.parse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_CSV = os.path.join(PROJECT_ROOT, "Final LG Audit Opinion Dashboard Content.csv")
OUTPUT_JSON = os.path.join(PROJECT_ROOT, "src", "data", "council-coordinates.json")

# Manual overrides for councils that don't geocode well
MANUAL_COORDINATES = {
    "Chatham Islands Council": {"lat": -43.8853, "lng": -176.4578},
    "Environment Canterbury Regional Council": {"lat": -43.5321, "lng": 172.6362},
    "Environment Southland (Southland Regional Council)": {"lat": -46.4132, "lng": 168.3538},
    "Manawatu-Wanganui Regional Council (Horizons)": {"lat": -40.3523, "lng": 175.6118},
}


def geocode_with_nominatim(name):
    """Geocode a council name using Nominatim API directly (no geopy needed)."""
    query = f"{name}, New Zealand"
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "nz",
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "NZ-Council-Audit-Map/1.0 (geocoding script)"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if data:
        return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}
    return None


def main():
    # Read council names from CSV
    councils = set()
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Council", "").strip()
            if name:
                councils.add(name)

    print(f"Found {len(councils)} unique councils")

    coordinates = {}
    for name in sorted(councils):
        if name in MANUAL_COORDINATES:
            coordinates[name] = MANUAL_COORDINATES[name]
            print(f"  {name}: {coordinates[name]} (manual)")
            continue

        try:
            result = geocode_with_nominatim(name)
            if result:
                coordinates[name] = result
                print(f"  {name}: {result}")
            else:
                print(f"  {name}: NOT FOUND - needs manual entry")
            time.sleep(1.1)  # Nominatim rate limit: 1 req/sec
        except Exception as e:
            print(f"  {name}: ERROR - {e}")
            time.sleep(1.1)

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(coordinates, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(coordinates)} entries to {OUTPUT_JSON}")
    missing = councils - set(coordinates.keys())
    if missing:
        print(f"Missing {len(missing)} councils: {sorted(missing)}")


if __name__ == "__main__":
    main()
