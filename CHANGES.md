# Changes

## 2026-02-25 (continued)

- Replaced Nominatim geocoding with LINZ NZ Addresses dataset lookups in
  `scripts/geocode_addresses.py` — no network calls, house-number precision
  instead of road-midpoint matches
- Requires user to download LINZ CSV (~500MB) to `scripts/nz-addresses.csv`
- Added `scripts/nz-addresses.csv` to `.gitignore`

## 2026-02-25

- Repurposed from schools audit map to councils audit map
- New data source: `Final LG Audit Opinion Dashboard Content.csv` (78 NZ councils)
- Added `scripts/geocode_councils.py` for one-time geocoding via Nominatim
- Added `scripts/preprocess_councils.py` to clean raw CSV (fix duplicate headers,
  missing columns, Hawke's Bay data offset, Buller missing audit type)
- Extended type filtering from 3 columns (Type 1-3) to 8 columns (Type 1-8)
- Replaced "Education region" filter with "Type of audit report" (Standard/Non-standard)
- Popup now groups findings by category (Qualified, Emphasis of Matter, etc.)
- Changed map icon from school to building-columns
- Removed school-specific data correction scripts
- Added address-based geocoding verification workflow:
  - `scripts/geocode_addresses.py` — geocodes council street addresses from CSV,
    compares against existing name-based coordinates
  - `scripts/geocode-comparison-map.html` — Leaflet template for per-council
    comparison screenshots (current vs address-geocoded pins)
  - `scripts/generate_comparison_screenshots.cjs` — Puppeteer script to generate
    comparison screenshots for all councils with >10m discrepancy
  - `scripts/geocode-review.html` — interactive review page with filtering,
    screenshots, and per-council coordinate selection (export to JSON)
