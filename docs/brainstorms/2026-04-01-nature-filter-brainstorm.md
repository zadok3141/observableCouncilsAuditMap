---
date: 2026-04-01
topic: nature-of-finding-filter
---

# Nature of finding filter and April data update

## What we're building

Two pieces of work delivered together:

1. **Data migration** -- process the April CSV (`Council-audit-data-April.csv`) into the format the app expects (`src/data/CouncilsAuditData2025.csv`), applying data cleanup and joining coordinates from the existing dataset.

2. **Nature of finding filter** -- a new combined filter table that lets users filter councils by the thematic nature of their audit findings (e.g. "Future of water delivery", "Service performance: Smooth travel exposure"). Placed below the existing filter tables, before the map and data table grid.

## Why this approach

The existing filter infrastructure (`createFilterableFieldTable`, `renderFilterTables`, `filterState`) already supports aggregating values across multiple columns (the "Type 1" filter checks Type 1--8). The Nature filter follows the same pattern, aggregating across Nature columns plus using type labels for Key audit matter / Other matter paragraph entries. No new abstractions needed.

A single combined filter (rather than separate qualified/EoM filters) was chosen because users care about the theme regardless of opinion type.

## Key decisions

- **Combined filter**: All nature values (qualified opinion natures, EoM natures, "Key audit matter", "Other matter paragraph") appear in one filter table.
- **Coordinates via join**: Match council names between old and new CSV (78/78 match confirmed). Drop the Address column from new data.
- **Column naming**: New CSV columns will be normalised to match existing code expectations (e.g. "Type of audit report" -> "Opinion type", "Type 1 (qualified opinion)" -> "Type 1").
- **Nature columns added to CSV**: Six new columns (Nature of qualified opinion 1/2/3, Nature of EoM 4/5/6) carried through to the processed CSV.
- **Type 7/8 nature**: No dedicated Nature column -- the filter uses the type name itself ("Key audit matter", "Other matter paragraph") as the nature value.

## Data cleanup (applied during processing)

| Fix | Scope |
|---|---|
| Normalise double space in "Water services  - counting..." | 2 councils |
| "Financial statement" -> "Financial statements" | 1 council |
| "Flood Protection" -> "Flood protection" | 1 council |
| "Greenhouse gas emissions" -> "Inherent uncertainties in the measurement of greenhouse gas emissions" (EoM only) | 7 councils |
| "Three waters assets" -> "Uncertainty over the fair value of three waters assets" | 1 council |
| "Key Audit Matter" -> "Key audit matter" | Auckland |
| Hawke's Bay Type 8: restore "Other matter paragraph" label (description was placed in type column) | 1 council |
| Join coordinates from old CSV by council name | All 78 |
| Drop Address column | All |

## Filter behaviour

- Aggregates nature values across Nature columns, plus Type 7/8 labels.
- Selecting a nature value filters to councils with at least one finding of that nature.
- Counts reflect filtered data; all possible values shown from complete dataset (matching existing filter pattern).
- Filter state integrated with existing reset button.

## Open questions

None -- requirements are confirmed.

## Next steps

-> `/workflows:plan` for implementation details
