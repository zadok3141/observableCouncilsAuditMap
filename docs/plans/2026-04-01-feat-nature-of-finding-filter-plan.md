---
title: "feat: Add nature of finding filter and April data update"
type: feat
status: active
date: 2026-04-01
---

# Add nature of finding filter and April data update

## Overview

Update the council audit data with the April 2026 CSV (which adds "Nature of..."
columns grouping findings by theme) and add a new combined "Nature of finding"
filter to the map interface. This filter lets users explore councils by the
thematic nature of their audit findings (e.g. "Future of water delivery",
"Service performance: Smooth travel exposure").

## Problem statement / motivation

The existing filters let users narrow by opinion type and type of non-standard
paragraph, but not by the *subject matter* of findings. The new April data
includes "Nature of..." columns that categorise each finding thematically. Adding
a filter for these values lets users answer questions like "which councils have
water services findings?" or "who has greenhouse gas emissions issues?" without
reading every popup.

## Proposed solution

Two coordinated changes:

1. **Data pipeline update** -- modify `scripts/preprocess_councils.py` to handle
   the new April CSV, carrying through the 6 Nature columns, applying data
   cleanups, and joining coordinates from the existing dataset.

2. **Nature of finding filter** -- add a single combined filter table to the UI
   that aggregates nature values across all finding types (qualified opinions,
   EoMs, key audit matters, other matter paragraphs).

## Technical approach

### Phase 1: Data pipeline (`scripts/preprocess_councils.py`)

Update the preprocessing script to handle the new CSV format.

**Input file change:**
- Old: `Final LG Audit Opinion Dashboard Content.csv`
- New: `Council-audit-data-April.csv`

**Header fixes** (update `fix_headers()`):
- Strip parenthetical annotations from Type headers (existing)
- Rename "Type of audit report" to "Opinion type" (new -- replaces old header name)
- Rename Nature columns to short form: "Nature of qualified opinion 1" -> "Nature 1", etc.
  - Map: `Nature of qualified opinion {1,2,3}` -> `Nature {1,2,3}`
  - Map: `Nature of EoM {4,5,6}` -> `Nature {4,5,6}`
- Fix duplicate "Description 6" -> "Description 7" (existing)
- Add missing "Description 8" (existing)

**Data cleanups** (new function `clean_nature_values()`):

```python
NATURE_CLEANUPS = {
    # Spacing fix
    "Service performance: Water services  - counting the number of complaints":
        "Service performance: Water services - counting the number of complaints",
    # Singular -> plural
    "Financial statement": "Financial statements",
    # Sentence case
    "Service performance: Flood Protection":
        "Service performance: Flood protection",
    # EoM: short label -> full label
    "Greenhouse gas emissions":
        "Inherent uncertainties in the measurement of greenhouse gas emissions",
    # Three waters normalisation
    "Three waters assets":
        "Uncertainty over the fair value of three waters assets",
}
```

The "Greenhouse gas emissions" cleanup is an **exact match only** applied to
Nature 4/5/6 columns (EoM natures). It must NOT affect "Service performance:
Greenhouse gas emissions" in Nature 1/2/3 columns.

**Existing fixes to retain:**
- Buller District Council: empty opinion type -> "Incomplete"
- Hawke's Bay Regional Council: shifted Other Matter Paragraph data
- Type value relabelling (Qualified -> Qualified opinion, etc.)
- "Key Audit Matter" -> "Key audit matter" (sentence case, handled by existing `TYPE_LABEL_MAP`)

**Coordinate joining:**
- Read coordinates from `src/data/council-coordinates.json` (existing)
- Join by council name (78/78 match confirmed)
- Drop Address column (existing)

**Output CSV column order:**

```
Council, Financial year, Opinion type,
Type 1, Nature 1, Description 1,
Type 2, Nature 2, Description 2,
Type 3, Nature 3, Description 3,
Type 4, Nature 4, Description 4,
Type 5, Nature 5, Description 5,
Type 6, Nature 6, Description 6,
Type 7, Description 7,
Type 8, Description 8,
Latitude, Longitude
```

Note: Type 7 and Type 8 have no Nature column. Their nature values ("Key audit
matter", "Other matter paragraph") are derived from the Type value in JavaScript.

### Phase 2: JavaScript -- filter infrastructure (`src/components/utils.js`)

**2a. Add `NATURE_COLUMNS` constant** (after existing `TYPE_COLUMNS` at line 14):

```js
const NATURE_COLUMNS = ["Nature 1", "Nature 2", "Nature 3", "Nature 4", "Nature 5", "Nature 6"];
```

**2b. Update `createFilterableFieldTable`** (lines 116-208):

Add a new branch for `fieldName === "Nature 1"` alongside the existing `"Type 1"` branch.

When gathering values:
- Iterate `NATURE_COLUMNS` for explicit nature values
- Also check Type 7 and Type 8: if a Type 7/8 value exists, include that type
  label as a nature value (e.g. "Key audit matter", "Other matter paragraph")
- Each council counted once per distinct nature value

When counting:
- Same logic -- iterate NATURE_COLUMNS + Type 7/8, deduplicate per council

**2c. Update `refreshFilteredDisplay`** (lines 421-468):

Add a `natureFilter` condition. **Uses OR (disjunctive) logic**, unlike the
existing Type filter which uses AND:

```js
// src/components/utils.js -- inside refreshFilteredDisplay filter logic
const natureFilter = filterState["Nature 1"].length === 0 ||
    filterState["Nature 1"].some(nature => {
        // Check explicit Nature columns
        if (NATURE_COLUMNS.some(col => item[col] === nature)) return true;
        // Check Type 7/8 labels as implicit nature values
        if (item["Type 7"] === nature || item["Type 8"] === nature) return true;
        return false;
    });
```

The `.some()` means: council passes if it has **any** of the selected nature
values (OR logic). This differs from the Type filter's `.every()` (AND logic)
because with 19 nature values, AND would produce empty results for most
multi-value selections.

**2d. Update `renderFilterTables`** (lines 342-386):

Add the nature filter entry to the `filterFields` array:

```js
{
    field: "Nature 1",
    title: "Nature of finding"
}
```

This is placed after the existing three entries (Year, Opinion type, Type of
non-standard opinion).

### Phase 3: Page updates (`src/index.md`)

**3a. Update `filterState`** (lines 65-69):

```js
const filterState = {
    "Financial year": [],
    "Type 1": [],
    "Opinion type": [],
    "Nature 1": []
};
```

**3b. Update reset button** (lines 96-108):

Add `filterState["Nature 1"] = [];` to the reset handler.

**3c. Update help text** (lines 28-38):

Update the instruction text to mention the nature filter:

> "Click one or more checkboxes to select Opinion type, Type of non-standard
> paragraph, and/or Nature of finding to filter the list of councils."

### Phase 4: Build and verify

1. Run `python scripts/preprocess_councils.py` to generate updated CSV
2. Run `yarn dev` to preview
3. Verify:
   - All 78 councils render on map with correct markers
   - Nature filter table appears below existing filters with 19 values
   - Selecting a nature value filters map and table correctly (OR logic)
   - Combined filtering works (nature + opinion type + type)
   - Reset button clears all filters including nature
   - Long nature labels display acceptably in filter table
4. Run `yarn build` to generate production output

## Acceptance criteria

- [x] `scripts/preprocess_councils.py` updated to process `Council-audit-data-April.csv`
- [x] All 9 data cleanups applied (spacing, singular/plural, sentence case, GHG, three waters, Auckland Key Audit Matter, Hawke's Bay Type 8)
- [x] Output CSV includes Nature 1-6 columns with correct values
- [x] Coordinates joined for all 78 councils
- [x] Buller District Council retains "Incomplete" opinion type fix
- [x] New "Nature of finding" filter table appears in UI
- [x] Filter aggregates across Nature 1-6 plus Type 7/8 labels
- [x] Multi-selection uses OR logic (disjunctive)
- [x] Nature filter works in combination with existing filters
- [x] Reset button clears nature filter state
- [x] Help text updated to mention nature filter
- [x] `yarn build` produces working production output

## Dependencies and risks

**Dependencies:**
- `Council-audit-data-April.csv` must be present in project root
- `src/data/council-coordinates.json` must exist with all 78 council coordinates

**Risks:**
- Long nature labels (up to 82 chars) may display poorly in narrow filter
  tables. The existing `layout: "auto"` and `flex: 1 1 300px` CSS should handle
  this with wrapping, but may need visual review.
- OR logic for nature filter is inconsistent with AND logic for the Type filter.
  This is intentional (19 values makes AND impractical) but could confuse users
  who expect consistent behavior across filters.

## Out of scope

- Changing popup content to show nature values
- Adding nature-related columns to the main data table
- Changing the Type filter from AND to OR logic
- Increasing the filter table `rows` parameter (stays at 7)

## References

- Brainstorm: `docs/brainstorms/2026-04-01-nature-filter-brainstorm.md`
- Existing filter infrastructure: `src/components/utils.js:116-468`
- Preprocessing script: `scripts/preprocess_councils.py`
- Current data: `src/data/CouncilsAuditData2025.csv`
- New data: `Council-audit-data-April.csv`
- Filter reference spreadsheet: `TypeEoMAndQopinion.ods`
