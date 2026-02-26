---
title: Opinion-type colored map markers
type: feat
status: active
date: 2026-02-26
---

# Opinion-type colored map markers

## Context

All council markers currently look identical on the map (default Leaflet blue pins when unselected, same red highlighted icon when selected). This makes it impossible to visually distinguish opinion types at a glance. We need to color-code markers by opinion type so users can immediately see the audit outcome distribution across NZ.

## Proposed solution

Add opinion-type-aware icons with two states (default and selected) and three color variants.

**Color mapping:**
| Opinion type | Color | Hex |
|---|---|---|
| Standard | Green | `#2e7d32` |
| Non-standard | Red | `#c62828` |
| Incomplete | Cold blue | `#1565c0` |
| Fallback | Gray | `#757575` |

**Default (unselected):** Opinion-colored circle background + white `faBuildingColumns`
**Selected:** White circle background + opinion-colored `faBuildingColumns` + small `faCheck` badge in corner

## Files to modify

1. `src/components/utils.js` -- all icon logic
2. `src/custom.css` -- remove Leaflet default divIcon styling

## Implementation steps

### Step 1: Add import and constants (`utils.js`, top of file)

- Add `faCheck` to the `free-solid-svg-icons` import (line 8)
- After `TYPE_COLUMNS` (line 12), add:
  - `OPINION_COLORS` map: `{ "Standard": "#2e7d32", "Non-standard": "#c62828", "Incomplete": "#1565c0" }`
  - `OPINION_FALLBACK_COLOR = "#757575"`
  - `getOpinionColor(opinionType)` helper that returns the color or fallback
  - `defaultIconCache` and `selectedIconCache` maps for memoization
  - `markerDefaultIconMap` -- a `Map<L.Marker, L.DivIcon>` to remember each marker's default icon for deselection

### Step 2: Replace `createHighlightedIcon()` with two new functions (`utils.js`, ~lines 407-435)

**`createDefaultIcon(opinionType)`:**
- Look up in `defaultIconCache` first; return cached if exists
- Use `layer()` with:
  - `faCircle` at size 64, y: -28, color = `getOpinionColor(opinionType)`
  - `faBuildingColumns` at size 36, x: -2, y: -28, color = `white`
- Create `L.divIcon` with className `council-marker`, same iconSize/iconAnchor/popupAnchor as current
- Cache and return

**`createSelectedIcon(opinionType)`:**
- Look up in `selectedIconCache` first; return cached if exists
- Use `layer()` with:
  - `faCircle` at size 64, y: -28, color = `white`
  - `faBuildingColumns` at size 36, x: -2, y: -28, color = `getOpinionColor(opinionType)`
  - `faCheck` at small size (~16), positioned in corner (x: ~10, y: ~-18), color = `getOpinionColor(opinionType)` -- tune visually
- Create `L.divIcon` with className `selected-council-marker`, same dimensions
- Cache and return

Delete `createHighlightedIcon()`.

### Step 3: Update `createCouncilMapMarkers()` (`utils.js`, ~lines 228-253)

- After `councilMarkerMap.clear()` (line 237), add `markerDefaultIconMap.clear()`
- When creating each marker, get the default icon: `const defaultIcon = createDefaultIcon(item["Opinion type"])`
- Pass it to the marker: `L.marker([...], { icon: defaultIcon })`
- Store the association: `markerDefaultIconMap.set(marker, defaultIcon)`

### Step 4: Update `createSelectableCouncilTable()` (`utils.js`, ~lines 447-539)

- Remove `const highlightedIcon = createHighlightedIcon()` (line 449)
- In the deselect loop (~line 464): replace `marker.setIcon(L.Icon.Default.prototype)` with `marker.setIcon(markerDefaultIconMap.get(marker))`
- In the select loop (~line 483): replace `marker.setIcon(highlightedIcon)` with `marker.setIcon(createSelectedIcon(row["Opinion type"]))`

### Step 5: CSS (`src/custom.css`)

Add after the existing `.leaflet-popup-content` block:

```css
.council-marker,
.selected-council-marker {
    background: none;
    border: none;
}
```

This overrides Leaflet's default `.leaflet-div-icon` white background/border.

## Verification

1. Run `yarn dev` and open the map in a browser
2. Confirm default markers show correct colors: green (Standard), red (Non-standard), cold blue (Incomplete)
3. Select a council from the table -- marker should swap to white background with colored icon and check badge
4. Deselect -- marker should revert to colored background with white icon
5. Use the "Opinion type" filter to show only Non-standard -- confirm only red markers remain
6. Reset filters -- all markers reappear with correct colors
7. Check that popups still open correctly on selection
