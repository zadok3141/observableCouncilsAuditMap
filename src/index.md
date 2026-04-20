---
toc: false
title: 2024/25 Council audit opinions
---

```js
// Cell 1: Import libraries and load data
import { icon, layer } from 'npm:@fortawesome/fontawesome-svg-core';
import { faCircle, faBuildingColumns } from 'npm:@fortawesome/free-solid-svg-icons';
import { extractCouncilCoordinates, createCouncilMapMarkers, createSelectableCouncilTable, createFilterableFieldTable, refreshFilteredDisplay, createDisplayRefresher, updateFilterAndRefresh, renderFilterTables, hasOpinionType } from './components/utils.js';
// Lodash is already imported in utils.js

// Load the data and pre-process coordinates
const rawCouncils = await FileAttachment("./data/CouncilsAuditData2025.csv").csv();
// Pre-process all councils to extract coordinates once
const councils = rawCouncils.map(council => {
  extractCouncilCoordinates(council); // This now stores coordinates on the council object
  council["Emphasis of matter paragraph"] = hasOpinionType(council, "Emphasis of matter paragraph");
  council["Qualified opinion"] = hasOpinionType(council, "Qualified opinion");
  return council;
});

// Create and insert the note div before #field_tables_container
// Note: This static help text is hardcoded, not user-supplied content
const ftc = document.getElementById('field_tables_container');

```

```js
// Cell 2: Define configuration options
const columns = ["Council","Opinion type","Qualified opinion","Emphasis of matter paragraph"];
const layout = "fixed";
```

```js
// Cell 3: Initialize map
const councils_map = L.map('councils_div')
    .setView([-40.9, 175.232], 5);

const osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
})
    .addTo(councils_map);

// Initialize map layers
const councilMarkerLayer = L.layerGroup().addTo(councils_map);
const councilMarkerReferences = [];
```

```js
// Cell 4: Define filter state (reactive)
const filterState = {
    "Financial year": [],
    "Type 1": [],
    "Opinion type": [],
    "Nature 1": []
};
```

```js
// Cell 5: Create display options object
const displayOptions = {
    columns,
    layout,
    allData: councils
};
```

```js
// Cell 6: Create refresh function and reset button
const refreshView = createDisplayRefresher(
    councils,
    filterState,
    councilMarkerLayer,
    councilMarkerReferences,
    councils_map,
    displayOptions,
    'field_tables_container'
);

// Add reset button
const resetButton = Inputs.button("Reset filters", {
    value: null,
    reduce: () => {
        // Clear all filter selections
        filterState["Financial year"] = [];
        filterState["Type 1"] = [];
        filterState["Opinion type"] = [];
        filterState["Nature 1"] = [];

        // Reset map to default view
        councils_map.setView([-40.9, 175.232], 5);

        // Refresh the display with cleared filters
        refreshView();
    }
});

// Create a container for the reset button and add it to the page
const resetButtonContainer = html`<div class="reset-button-container"></div>`;
resetButtonContainer.appendChild(resetButton);

// Add the reset button to the DOM immediately
const fieldTablesContainer = document.getElementById('field_tables_container');
if (fieldTablesContainer) {
    fieldTablesContainer.parentNode.insertBefore(resetButtonContainer, fieldTablesContainer.nextSibling);
}

// Return the container as the last expression so Observable will display it
// This ensures the button is visible when the cell is re-evaluated
resetButtonContainer
```

```js
// Cell 7: Initial display and handle reactivity
// This cell will re-run when filterState changes
filterState;  // Reference filterState to make this cell depend on it

// Refresh the display
refreshView();
```

<style>
/* Add styling for councils with missing coordinates */
.missing-coordinates {
  color: #ff0000;
  font-style: italic;
}
/* Break the iframe height feedback loop: Observable Framework sets
   min-height: calc(100vh - 20rem) on #observablehq-main, but inside an
   iframe 100vh = iframe viewport height.  When the parent resizes the
   iframe based on scrollHeight, 100vh grows, min-height grows,
   scrollHeight grows → runaway loop.  Override to 0 for embedded use. */
#observablehq-main {
    min-height: 0 !important;
}
</style>

<div class="field-tables-container" id="field_tables_container">
  <!-- Field tables will be inserted here by JavaScript -->
</div>

<div class="grid grid-cols-4" style="grid-auto-rows: auto;">
  <div id="councils_div" class="card grid-colspan-2" style="height:625px;"></div>
  <div class="card grid-colspan-2" id="table_div">
  </div>
</div>

<div id="nature_filter_container">
  <!-- Grouped nature filter will be inserted here by JavaScript -->
</div>

<script>
  // Post iframe height to parent via postMessage.
  // Debounced to avoid capturing transient DOM states while Observable
  // cells render (tables briefly appear at full height before max-height
  // constrains them).  ResizeObserver catches async rendering changes.
  var _postHeightTimer;
  function postHeight() {
    clearTimeout(_postHeightTimer);
    _postHeightTimer = setTimeout(function() {
      var height = document.body.scrollHeight;
      window.parent.postMessage({type: 'iframeHeight', height: height}, '*');
    }, 150);
  }
  window.addEventListener('resize', postHeight);
  new ResizeObserver(postHeight).observe(document.body);
</script>
