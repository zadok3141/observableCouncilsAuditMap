#!/usr/bin/env python3
"""
Geocode councils by their street addresses using LINZ NZ Addresses dataset.

Replaces the Nominatim-based approach with local LINZ CSV lookups for much
better accuracy (house-number precision vs road midpoints).

Usage:
    .venv/bin/python scripts/geocode_addresses.py

Prerequisites:
    Download NZ Addresses CSV from LINZ Data Service:
    https://data.linz.govt.nz/layer/105689-nz-addresses/
    Export as CSV with NZGD2000 CRS, save to scripts/nz-addresses.csv

Outputs:
    scripts/geocode-comparison.json      — machine-readable comparison data
    scripts/geocode-comparison-data.js   — same data as JS variable for review page
"""

import csv
import json
import os
import re
import statistics
import sys
from collections import defaultdict

from geopy.distance import geodesic

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_CSV = os.path.join(PROJECT_ROOT, "Final LG Audit Opinion Dashboard Content.csv")
COORDS_JSON = os.path.join(PROJECT_ROOT, "src", "data", "council-coordinates.json")
LINZ_CSV = os.path.join(SCRIPT_DIR, "nz-addresses.csv")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "geocode-comparison.json")
OUTPUT_JS = os.path.join(SCRIPT_DIR, "geocode-comparison-data.js")

# Road type: abbreviation/variant -> canonical lowercase
ROAD_TYPE_CANON = {
    "street": "street", "st": "street", "str": "street",
    "road": "road", "rd": "road",
    "avenue": "avenue", "ave": "avenue", "av": "avenue",
    "drive": "drive", "dr": "drive", "drv": "drive",
    "place": "place", "pl": "place",
    "terrace": "terrace", "tce": "terrace", "ter": "terrace",
    "crescent": "crescent", "cres": "crescent", "cr": "crescent",
    "way": "way",
    "lane": "lane", "ln": "lane",
    "close": "close", "cl": "close",
    "court": "court", "ct": "court", "crt": "court",
    "quay": "quay",
    "parade": "parade", "pde": "parade",
    "grove": "grove", "gr": "grove", "grv": "grove",
    "rise": "rise",
    "mews": "mews",
    "boulevard": "boulevard", "blvd": "boulevard",
    "highway": "highway", "hwy": "highway",
    "esplanade": "esplanade", "esp": "esplanade",
    "square": "square", "sq": "square",
    "loop": "loop",
    "track": "track", "trk": "track",
    "path": "path",
    "row": "row",
    "mall": "mall",
    "walk": "walk",
    "circle": "circle", "cir": "circle",
    "end": "end",
}

# Town/city name normalization for NZ spelling variants
TOWN_ALIASES = {
    "wanganui": "whanganui",
}

# Precompile regex for detecting multiple street addresses in garbled input
_ALL_TYPES = sorted(ROAD_TYPE_CANON.keys(), key=len, reverse=True)
_TYPES_RE = "|".join(re.escape(t) for t in _ALL_TYPES)
_MULTISTREET_RE = re.compile(
    rf"\d+\s+\S+(?:\s+\S+)*?\s+(?:{_TYPES_RE})\b", re.I
)


def normalize_road_type(rt):
    """Normalize a road type to canonical form."""
    return ROAD_TYPE_CANON.get(rt.lower().rstrip("."), rt.lower().rstrip("."))


def normalize_town(town):
    """Normalize town/city name, handling known NZ spelling variants."""
    t = town.lower().strip()
    return TOWN_ALIASES.get(t, t)


def split_street(street_str):
    """
    Split a street string into (number, road_name, road_type, extra).

    'extra' contains any words after the road type that might be a suburb
    or locality (e.g. "Richmond" from "Queen Street Richmond").

    Examples:
        "135 Albert Street"        -> ("135", "albert", "street", "")
        "Victoria Avenue"          -> (None, "victoria", "avenue", "")
        "11-15 Victoria Avenue"    -> ("11-15", "victoria", "avenue", "")
        "The Octagon"              -> (None, "the octagon", "", "")
        "388 Main South Rd"        -> ("388", "main south", "road", "")
        "189 Queen Street Richmond"-> ("189", "queen", "street", "richmond")
    """
    s = street_str.strip()

    # Extract leading number (possibly a range like "11-15" or "838 - 842")
    number = None
    m = re.match(r"^(\d+(?:\s*[-\u2013]\s*\d+)?)\s+", s)
    if m:
        number = re.sub(r"\s+", "", m.group(1)).replace("\u2013", "-")
        s = s[m.end():]

    words = s.split()

    # Scan from end: find rightmost word that is a recognized road type
    for i in range(len(words) - 1, 0, -1):
        canon = ROAD_TYPE_CANON.get(words[i].lower().rstrip("."))
        if canon:
            road_name = " ".join(words[:i]).lower()
            extra = " ".join(words[i + 1 :]).lower() if i + 1 < len(words) else ""
            return number, road_name, canon, extra

    return number, s.lower(), "", ""


def parse_address(raw_address):
    """
    Parse a multi-line address into structured components.

    Typical formats:
        "Cnr Havelock & Baring Streets\\nAshburton Ashburton\\nNew Zealand"
        "ASB Building\\n135 Albert Street\\nAuckland Central\\nAuckland Auckland 1010\\nNew Zealand"

    Returns dict with keys: street, city, postcode, building, raw_street
    """
    lines = [l.strip() for l in raw_address.strip().split("\n") if l.strip()]

    if lines and lines[-1].lower() == "new zealand":
        lines = lines[:-1]

    if not lines:
        return None

    city_line = lines[-1]
    lines = lines[:-1]

    postcode = ""
    postcode_match = re.search(r"\b(\d{4})\s*$", city_line)
    if postcode_match:
        postcode = postcode_match.group(1)
        city_line = city_line[: postcode_match.start()].strip()

    city_words = city_line.split()
    if len(city_words) >= 2:
        mid = len(city_words) // 2
        first_half = " ".join(city_words[:mid])
        second_half = " ".join(city_words[mid:])
        if first_half.lower() == second_half.lower():
            city = first_half
        else:
            city = city_line
    else:
        city = city_line

    building = ""
    street_lines = lines

    if len(street_lines) >= 2:
        first = street_lines[0]
        if not re.search(r"\d", first) and not re.match(
            r"(?i)(cnr|corner)\b", first
        ):
            building = first
            street_lines = street_lines[1:]

    raw_street = " ".join(street_lines)
    street = raw_street

    cnr_match = re.match(r"(?i)(?:cnr|corner)\s+(.+?)\s*[&,]\s*(.+)", street)
    if cnr_match:
        street = cnr_match.group(1).strip()
        if not re.search(
            r"(?i)(street|st|road|rd|ave|avenue|drive|dr|place|pl|terrace|crescent|way|quay)\s*$",
            street,
        ):
            second = cnr_match.group(2).strip()
            suffix_match = re.search(
                r"\b(Streets?|Roads?|Avenues?|Drives?|Places?|Terraces?|Crescents?)\s*$",
                second,
                re.I,
            )
            if suffix_match:
                suffix = suffix_match.group(1)
                if suffix.lower().endswith("s") and not suffix.lower().endswith("ss"):
                    suffix = suffix[:-1]
                street = f"{street} {suffix}"

    if "," in street:
        parts = [p.strip() for p in street.split(",")]
        for part in parts:
            if re.match(r"\d+\s+\w", part):
                street = part
                break

    street = re.sub(r"^Level\s+\d+,?\s*", "", street, flags=re.I)

    return {
        "street": street,
        "city": city,
        "postcode": postcode,
        "building": building,
        "raw_street": raw_street,
    }


# ---------------------------------------------------------------------------
# LINZ index loading
# ---------------------------------------------------------------------------


def load_linz_index(csv_path):
    """
    Load LINZ NZ Addresses CSV and build lookup indices.

    Returns:
        city_index:   {(road_name, road_type, town_city)} -> [records]
        suburb_index: {(road_name, road_type, suburb)}    -> [records]

    Each record is a tuple:
        (addr_num, addr_num_high, lat, lng, full_address)
    """
    print(f"Loading LINZ addresses from {csv_path}...")
    city_index = defaultdict(list)
    suburb_index = defaultdict(list)
    count = 0

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            count += 1
            if count % 500000 == 0:
                print(f"  ...{count:,} rows")

            road_name = (row.get("road_name") or "").strip().lower()
            if not road_name:
                continue

            road_type = normalize_road_type(row.get("road_type_name") or "")
            town = (row.get("town_city") or "").strip().lower()
            suburb = (row.get("suburb_locality") or "").strip().lower()

            try:
                lat = float(row["gd2000_ycoord"])
                lng = float(row["gd2000_xcoord"])
            except (ValueError, TypeError, KeyError):
                continue

            addr_num_str = (row.get("address_number") or "").strip()
            addr_num_high_str = (row.get("address_number_high") or "").strip()
            full_address = (row.get("full_address") or "").strip()

            try:
                addr_num = int(addr_num_str) if addr_num_str else None
            except ValueError:
                addr_num = None
            try:
                addr_num_high = int(addr_num_high_str) if addr_num_high_str else None
            except ValueError:
                addr_num_high = None

            rec = (addr_num, addr_num_high, lat, lng, full_address)

            if town:
                city_index[(road_name, road_type, town)].append(rec)
            if suburb:
                suburb_index[(road_name, road_type, suburb)].append(rec)

    print(
        f"  Loaded {count:,} rows -> "
        f"{len(city_index):,} city keys, {len(suburb_index):,} suburb keys"
    )
    return city_index, suburb_index


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------


def find_best_match(records, target_number):
    """
    Given LINZ records on a street, find the best coordinate match.

    If target_number given: find exact address_number match, else closest.
    If no target_number: return median coordinates of all records.
    """
    if not records:
        return None

    if target_number is not None:
        # Parse target (may be range "11-15" -> midpoint 13)
        parts = target_number.split("-")
        try:
            target = (
                (int(parts[0]) + int(parts[-1])) / 2
                if len(parts) == 2
                else int(parts[0])
            )
        except ValueError:
            target = None

        if target is not None:
            # Exact match on address_number
            exact = [r for r in records if r[0] is not None and r[0] == int(target)]
            if not exact and len(parts) == 2:
                # For ranges, try matching the low end
                try:
                    low = int(parts[0])
                    exact = [r for r in records if r[0] is not None and r[0] == low]
                except ValueError:
                    pass
            if exact:
                r = exact[0]
                return {"lat": r[2], "lng": r[3], "full_address": r[4]}

            # Closest by number
            numbered = [
                (r, abs(r[0] - target)) for r in records if r[0] is not None
            ]
            if numbered:
                numbered.sort(key=lambda x: x[1])
                r = numbered[0][0]
                return {"lat": r[2], "lng": r[3], "full_address": r[4]}

    # No target number or no numbered records -> median coordinates
    lats = [r[2] for r in records]
    lngs = [r[3] for r in records]
    return {
        "lat": statistics.median(lats),
        "lng": statistics.median(lngs),
        "full_address": f"[median of {len(records)} addresses on street]",
    }


def _lookup(road_name, road_type, location, index, target_number):
    """Try a single exact-key lookup in an index."""
    records = index.get((road_name, road_type, location), [])
    if records:
        return find_best_match(records, target_number), len(records)
    return None, 0


def _try_street_in_city(
    road_name, road_type, city, city_index, suburb_index, target_number
):
    """
    Look up a street in a city/town, trying multiple fallback strategies:
      1. Exact (road_name, road_type, city) in city_index
      2. City name as suburb in suburb_index
      3. Partial city match (first word, e.g. "auckland central" -> "auckland")
      4. Without road_type (type mismatch)
      5. "saint" <-> "st" in road name
    """
    norm_city = normalize_town(city)

    # 1. Exact city match
    match, count = _lookup(road_name, road_type, norm_city, city_index, target_number)
    if match:
        return match, "linz_city", count

    # 2. City name as suburb
    match, count = _lookup(
        road_name, road_type, norm_city, suburb_index, target_number
    )
    if match:
        return match, "linz_suburb", count

    # 3. Partial city: first word (e.g. "auckland central" -> "auckland")
    city_first = norm_city.split()[0] if norm_city else ""
    if city_first and city_first != norm_city:
        match, count = _lookup(
            road_name, road_type, city_first, city_index, target_number
        )
        if match:
            return match, "linz_city_partial", count
        match, count = _lookup(
            road_name, road_type, city_first, suburb_index, target_number
        )
        if match:
            return match, "linz_suburb_partial", count

    # 4. Without road type (scan city_index keys)
    if road_type:
        for key, recs in city_index.items():
            if key[0] == road_name and key[2] == norm_city:
                m = find_best_match(recs, target_number)
                if m:
                    return m, "linz_no_type", len(recs)
        if city_first and city_first != norm_city:
            for key, recs in city_index.items():
                if key[0] == road_name and key[2] == city_first:
                    m = find_best_match(recs, target_number)
                    if m:
                        return m, "linz_no_type_partial", len(recs)

    # 5. "st" <-> "saint" in road name
    alt_name = None
    if road_name.startswith("st "):
        alt_name = "saint " + road_name[3:]
    elif road_name.startswith("saint "):
        alt_name = "st " + road_name[6:]
    if alt_name:
        match, count = _lookup(
            alt_name, road_type, norm_city, city_index, target_number
        )
        if match:
            return match, "linz_saint_alias", count

    return None, None, 0


def geocode_with_linz(parsed, city_index, suburb_index):
    """
    Geocode a parsed address using LINZ indices.

    Handles corner addresses, building-only addresses, multi-street data
    entry errors, and spelling variants.

    Returns dict with lat, lng, full_address, method — or None.
    """
    street = parsed["street"]
    city = parsed["city"]
    raw_street = parsed["raw_street"]

    # --- Corner addresses: try both streets, average if both found ---
    cnr_match = re.match(r"(?i)(?:cnr|corner)\s+(.+?)\s*[&,]\s*(.+)", raw_street)
    if cnr_match:
        street1 = cnr_match.group(1).strip()
        street2 = cnr_match.group(2).strip()
        results = []
        for s in [street1, street2]:
            num, rn, rt, _extra = split_street(s)
            m, _method, cnt = _try_street_in_city(
                rn, rt, city, city_index, suburb_index, num
            )
            if m:
                results.append(m)
        if len(results) == 2:
            return {
                "lat": (results[0]["lat"] + results[1]["lat"]) / 2,
                "lng": (results[0]["lng"] + results[1]["lng"]) / 2,
                "full_address": (
                    f"Corner: {results[0]['full_address']}"
                    f" / {results[1]['full_address']}"
                ),
                "method": "linz_corner",
            }
        elif results:
            results[0]["method"] = "linz_corner_partial"
            return results[0]
        # Fall through to standard lookup with parsed["street"]

    # --- Standard street lookup ---
    number, road_name, road_type, extra = split_street(street)
    match, method, _ = _try_street_in_city(
        road_name, road_type, city, city_index, suburb_index, number
    )
    if match:
        match["method"] = method
        return match

    # --- Try extra words as city/suburb ---
    # Handles cases like "Queen Street Richmond" where city is "Tasman" but
    # the actual town "Richmond" ended up appended to the street line.
    if extra:
        match, method, _ = _try_street_in_city(
            road_name, road_type, extra, city_index, suburb_index, number
        )
        if match:
            match["method"] = method + "_extra"
            return match
        # Also try first word of extra
        extra_first = extra.split()[0]
        if extra_first != extra:
            match, method, _ = _try_street_in_city(
                road_name, road_type, extra_first, city_index, suburb_index, number
            )
            if match:
                match["method"] = method + "_extra"
                return match

    # --- Try full street name as road_name with no type ---
    # Handles "West End" where split_street sees road_type="end" but LINZ
    # might store road_name="West End" with no type.
    if road_type:
        full_name = f"{road_name} {road_type}"
        match, method, _ = _try_street_in_city(
            full_name, "", city, city_index, suburb_index, number
        )
        if match:
            match["method"] = method + "_fullname"
            return match

    # --- Multi-street fallback (Selwyn-like data entry errors) ---
    # If raw_street contains multiple "number Street Type" segments, try each.
    substreets = _MULTISTREET_RE.findall(raw_street)
    if len(substreets) > 1:
        for sub in substreets:
            num, rn, rt, _extra = split_street(sub.strip())
            m, method, _ = _try_street_in_city(
                rn, rt, city, city_index, suburb_index, num
            )
            if m:
                m["method"] = method + "_multiline"
                return m

    # --- Try shorter road names ---
    # "Main South Road" might be indexed as just "Main" in some contexts.
    if " " in road_name:
        words = road_name.split()
        for i in range(len(words) - 1, 0, -1):
            shorter = " ".join(words[:i])
            m, method, _ = _try_street_in_city(
                shorter, road_type, city, city_index, suburb_index, number
            )
            if m:
                m["method"] = method + "_short"
                return m

    return None


def classify_distance(distance_m):
    """Classify distance into green/amber/red."""
    if distance_m < 10:
        return "green"
    elif distance_m <= 50:
        return "amber"
    else:
        return "red"


def main():
    if not os.path.exists(LINZ_CSV):
        print(f"ERROR: LINZ addresses CSV not found at {LINZ_CSV}")
        print()
        print("Download from: https://data.linz.govt.nz/layer/105689-nz-addresses/")
        print("  1. Click Export -> Format: CSV -> CRS: NZGD2000 (default)")
        print(f"  2. Save to {LINZ_CSV}")
        sys.exit(1)

    # Load LINZ index
    city_index, suburb_index = load_linz_index(LINZ_CSV)

    # Load current coordinates
    with open(COORDS_JSON, "r", encoding="utf-8") as f:
        current_coords = json.load(f)

    # Read addresses from CSV (one per council, deduped)
    addresses = {}
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Council", "").strip()
            if name and name not in addresses:
                addresses[name] = row.get("Address", "").strip()

    print(f"\nFound {len(addresses)} councils with addresses")
    print(f"Current coordinates for {len(current_coords)} councils\n")

    results = []

    for name in sorted(addresses.keys()):
        raw_addr = addresses[name]
        parsed = parse_address(raw_addr)
        current = current_coords.get(name, {})

        print(f"[{len(results)+1}/{len(addresses)}] {name}")
        if parsed:
            print(
                f"    Street: {parsed['street']} | City: {parsed['city']}"
            )

        if not parsed:
            print("    SKIP: could not parse address")
            results.append(
                {
                    "council": name,
                    "raw_address": raw_addr,
                    "current": current if current else None,
                    "address_geocoded": None,
                    "distance_m": None,
                    "nominatim_display": None,
                    "method": None,
                    "status": "failed",
                }
            )
            continue

        geocoded = geocode_with_linz(parsed, city_index, suburb_index)

        if not geocoded:
            print("    FAILED: no LINZ match")
            results.append(
                {
                    "council": name,
                    "raw_address": raw_addr,
                    "current": current if current else None,
                    "address_geocoded": None,
                    "distance_m": None,
                    "nominatim_display": None,
                    "method": None,
                    "status": "failed",
                }
            )
            continue

        # Calculate distance from current coordinates
        distance_m = None
        if current:
            distance_m = geodesic(
                (current["lat"], current["lng"]),
                (geocoded["lat"], geocoded["lng"]),
            ).meters
            distance_m = round(distance_m, 1)
            status = classify_distance(distance_m)
        else:
            status = "red"

        print(
            f"    -> ({geocoded['lat']:.6f}, {geocoded['lng']:.6f})"
            f" [{geocoded['method']}]"
        )
        if distance_m is not None:
            print(f"    Distance: {distance_m:.0f}m ({status})")
        print(f"    LINZ: {geocoded['full_address']}")

        results.append(
            {
                "council": name,
                "raw_address": raw_addr,
                "current": current if current else None,
                "address_geocoded": {
                    "lat": geocoded["lat"],
                    "lng": geocoded["lng"],
                },
                "distance_m": distance_m,
                "nominatim_display": geocoded["full_address"],
                "method": geocoded["method"],
                "status": status,
            }
        )

    # Summary
    print(f"\n{'='*60}")
    print(f"Results: {len(results)} councils")
    print(
        f"  Green (<10m):   {sum(1 for r in results if r['status']=='green')}"
    )
    print(
        f"  Amber (10-50m): {sum(1 for r in results if r['status']=='amber')}"
    )
    print(
        f"  Red (>50m):     {sum(1 for r in results if r['status']=='red')}"
    )
    print(
        f"  Failed:         {sum(1 for r in results if r['status']=='failed')}"
    )

    # Sort by distance (largest first), failed at end
    results.sort(key=lambda r: (r["status"] == "failed", -(r["distance_m"] or 0)))

    # Write JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUTPUT_JSON}")

    # Write JS (for file:// loading in review page)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by geocode_addresses.py\n")
        f.write("var COMPARISON_DATA = ")
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write(";\n")
    print(f"Wrote {OUTPUT_JS}")


if __name__ == "__main__":
    main()
