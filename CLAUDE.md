# CLAUDE.md

## Project Description

Interactive map of NZ council audit findings using Observable Framework.
Displays audit opinions, findings (qualified opinions, emphasis of matter,
key audit matters, other matter paragraphs) for local government councils.

## Authoritative Documentation

- `README.md` — project overview and setup
- `CHANGES.md` — changelog
- `CLAUDE.md` — this file (agent guidance)

## Common Mistakes / Confusion Points

The role of this file is to describe common mistakes and confusion points that agents might encounter as they work in this project. If you encounter something in the project that surprises you, please alert the developer working with you and indicate that this is the case in the CLAUDE.md file to help prevent future agents from having the same issue.

- The raw CSV (`Final LG Audit Opinion Dashboard Content.csv`) has a
  **duplicate header** (`Description 6` appears twice) and is **missing**
  `Description 8`. The preprocessing script (`scripts/preprocess_councils.py`)
  fixes these issues. Always use the preprocessed
  `src/data/CouncilsAuditData2025.csv`, never the raw CSV at runtime.

- **Hawke's Bay Regional Council** has offset data in the raw CSV due to the
  missing `Description 8` column. The preprocessing script detects and shifts
  this automatically.

- **Buller District Council** has an empty `Type of audit report` in the raw
  CSV. The preprocessing script sets it to `Standard`.

- The filter field `"Type 1"` is used as the key for type filtering but
  actually searches across all 8 type columns (`Type 1` through `Type 8`).

- Council coordinates come from `src/data/council-coordinates.json`, produced
  by `scripts/geocode_councils.py`. Some entries were manually overridden
  (Chatham Islands, regional councils with parenthetical names, etc.).

- **Chatham Islands Council** is at longitude ~-176.5, far east of mainland
  NZ. The default map view won't show it without scrolling.
