---
module: System
date: 2026-02-26
problem_type: integration_issue
component: tooling
symptoms:
  - "12 of 78 councils resolved to road midpoints instead of house-number precision"
  - "Geocoding errors up to 22km (e.g. Kaipara District Council)"
  - "Nominatim rate limiting required ~3 min per run (1.1s sleep per query)"
root_cause: wrong_api
resolution_type: code_fix
severity: high
tags: [geocoding, nominatim, linz, nz-addresses, data-quality]
---

# Troubleshooting: Nominatim Poor House-Number Resolution for NZ Addresses

## Problem

The Nominatim geocoder returned road-level matches (street midpoints) instead
of house-number precision for 12 of 78 NZ council addresses, causing coordinate
errors up to 22km. This made the map pins unreliable for precise council office
locations.

## Environment

- Module: Geocoding (scripts/geocode_addresses.py)
- Framework: Observable Framework (JavaScript) with Python geocoding scripts
- Affected Component: Address geocoding pipeline
- Date: 2026-02-26

## Symptoms

- 12 of 78 councils got road-level matches only (Nominatim dropped the house
  number and returned the street midpoint)
- Largest error: Kaipara District Council at 22.1km off (42 Hokianga Road,
  Dargaville resolved to the road midpoint instead of number 42)
- Other large errors: Southland DC (121km, wrong city entirely),
  Thames-Coromandel DC (36.8km)
- Nominatim's `addressdetails` response lacked `house_number` for affected
  results, confirming road-level resolution
- Each script run took ~3 minutes due to Nominatim's 1-request-per-second
  rate limit (78 councils x 2 queries each x 1.1s sleep)

## What Didn't Work

**Attempted Solution 1:** Structured Nominatim queries with street/city/country
parameters
- **Why it failed:** Nominatim still dropped house numbers for many NZ
  addresses, returning road-level matches

**Attempted Solution 2:** Freeform Nominatim queries as fallback (concatenating
building + street + city + postcode)
- **Why it failed:** Freeform queries also returned road-level matches for the
  same addresses. When the street had a house number but Nominatim only matched
  at road level, neither structured nor freeform resolved it.

## Solution

Replaced Nominatim API calls entirely with local LINZ NZ Addresses dataset
lookups. The LINZ dataset contains ~2 million addressed properties in NZ with
precise coordinates.

**Key changes to `scripts/geocode_addresses.py`:**

```python
# Before (Nominatim API - network calls with rate limiting):
def geocode_address(parsed):
    results = nominatim_query({"street": parsed["street"], "city": parsed["city"]})
    time.sleep(1.1)  # Rate limit
    # ... freeform fallback ...

# After (LINZ CSV - local lookup, no network):
def load_linz_index(csv_path):
    """Build in-memory index: (road_name, road_type, town_city) -> [records]"""
    city_index = defaultdict(list)
    # ... read ~2M rows, index by street/city ...
    return city_index, suburb_index

def geocode_with_linz(parsed, city_index, suburb_index):
    number, road_name, road_type, extra = split_street(parsed["street"])
    match, method, _ = _try_street_in_city(
        road_name, road_type, city, city_index, suburb_index, number
    )
    # ... cascading fallbacks ...
```

**Matching strategy with cascading fallbacks:**
1. Exact `(road_name, road_type, town_city)` in city index
2. City name as suburb in suburb index
3. Partial city match (first word, e.g. "Auckland Central" -> "Auckland")
4. Type-agnostic lookup (ignores road type mismatch)
5. "Saint"/"St" alias in road name
6. Extra words from street line as alternate city/suburb
7. Full street name as road_name with no type (handles "West End")
8. Multi-street regex fallback (handles garbled data entry errors)

**Edge cases handled:**
- Road type normalization: "St" -> "Street", "Rd" -> "Road", etc.
- Town spelling variants: "Wanganui" -> "Whanganui"
- Corner addresses: average coordinates from both streets
- Range numbers: "11-15" -> midpoint 13, find closest match
- No-number streets: median coordinates of all addresses on street
- Data entry errors (Selwyn): regex to detect two concatenated addresses

## Why This Works

1. **Root cause:** Nominatim's NZ address data is incomplete at the
   house-number level. Many NZ addresses only exist as road segments in
   OpenStreetMap, not as individual addressed points. Nominatim can only return
   what OSM has.

2. **Why LINZ solves it:** The LINZ NZ Addresses dataset is the authoritative
   source for NZ property addresses, maintained by Land Information New Zealand.
   It contains precise coordinates for every addressed property, including rural
   addresses that OSM lacks. NZGD2000 coordinates are effectively WGS84
   (sub-meter difference).

3. **Performance:** Loading the ~2M row CSV takes ~10-20 seconds. After that,
   all 78 lookups are O(1) dict lookups (vs ~3 minutes of network calls with
   Nominatim). Total runtime drops from ~3 minutes to ~15 seconds.

## Prevention

- For NZ address geocoding, prefer LINZ over Nominatim/Google/etc. The LINZ
  dataset is free, authoritative, and has complete coverage
- When geocoding results lack precision (road-level instead of house-level),
  check the source data completeness before adding more query strategies
- Always compare geocoded coordinates against known reference points to detect
  systematic precision issues early
- The LINZ CSV (~500MB) is too large to commit; document the download step and
  add to `.gitignore`

## Related Issues

No related issues documented yet.
