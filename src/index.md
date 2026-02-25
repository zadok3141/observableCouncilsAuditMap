---
toc: false
title: School audits UI prototype
---

```js
// Cell 1: Import libraries and load data
import { icon, layer } from 'npm:@fortawesome/fontawesome-svg-core';
import { faCircle, faSchoolCircleCheck } from 'npm:@fortawesome/free-solid-svg-icons';
import { extractSchoolCoordinates, createSchoolMapMarkers, createSelectableSchoolTable, createFilterableFieldTable, refreshFilteredDisplay, createDisplayRefresher, updateFilterAndRefresh, renderFilterTables } from './components/utils.js';
// Lodash is already imported in utils.js

// Load the data and pre-process coordinates
const rawSchools = await FileAttachment("./data/SchoolsAuditData2018-2024.csv").csv();
// Pre-process all schools to extract coordinates once
const schools = rawSchools.map(school => {
  extractSchoolCoordinates(school); // This now stores coordinates on the school object
  return school;
});

// Create and insert the note div before #field_tables_container
const ftc = document.getElementById('field_tables_container');

const noteDiv = document.createElement('div');
noteDiv.innerHTML = `
  <input type="checkbox" id="note1_toggle" aria-expanded="false" aria-controls="note1_content">
  <div id="note1_div" class="note">
    <label for="note1_toggle" aria-label="How to use this map (press Space to toggle)">How to use this map</label>
    <ul id="note1_content" aria-labelledby="note1_toggle">
      <li>Click one or more checkboxes to select Financial years, Types and/or Education regions to filter the list of schools.</li>
      <li>Select one or more schools from the sortable lists on the right of (on a mobile: under) the map. Click on a school's marker on the map to see what type of non-standard audit opinion was issued and why.</li>
      <li>Click on any table heading to sort the data.</li>
    </ul>
  </div>
`;
ftc.parentNode.insertBefore(noteDiv,ftc);
```

```js
// Cell 2: Define configuration options
const columns = ["School","Education region","Financial year"];
const layout = "fixed";
```

```js
// Cell 3: Initialize map
const schools_map = L.map('schools_div')
    .setView([-40.9, 175.232], 5);

const osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
})
    .addTo(schools_map);

// Initialize map layers
const schoolMarkerLayer = L.layerGroup().addTo(schools_map);
const schoolMarkerReferences = [];
```

```js
// Cell 4: Define filter state (reactive)
const filterState = {
    "Financial year": [],
    "Type 1": [],
    "Education region": []
};
```

```js
// Cell 5: Create display options object
const displayOptions = {
    columns,
    layout,
    allData: schools
};
```

```js
// Cell 6: Create refresh function and reset button
const refreshView = createDisplayRefresher(
    schools, 
    filterState, 
    schoolMarkerLayer, 
    schoolMarkerReferences, 
    schools_map, 
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
        filterState["Education region"] = [];
        
        // Reset map to default view
        schools_map.setView([-40.9, 175.232], 5);
        
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
/* Add styling for schools with missing coordinates */
.missing-coordinates {
  color: #ff0000;
  font-style: italic;
}
</style>

<div class="field-tables-container" id="field_tables_container">
  <!-- Field tables will be inserted here by JavaScript -->
</div>

<div class="grid grid-cols-4" style="grid-auto-rows: auto;">
  <div id="schools_div" class="card grid-colspan-2" style="height:625px;"></div>
  <div class="card grid-colspan-2" id="table_div">
  </div>
</div>
