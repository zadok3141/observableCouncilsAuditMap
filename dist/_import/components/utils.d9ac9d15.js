import * as Inputs from "../../_observablehq/stdlib/inputs.46f60fd4.js";
import _ from "../../_npm/lodash@4.17.23/dde5ae91.js";
import { icon, layer } from "../../_npm/@fortawesome/fontawesome-svg-core@7.2.0/4d97ac5b.js";
import { faCircle, faBuildingColumns } from "../../_npm/@fortawesome/free-solid-svg-icons@7.2.0/7f2a1866.js";

const TYPE_COLUMNS = ["Type 1", "Type 2", "Type 3", "Type 4", "Type 5", "Type 6", "Type 7", "Type 8"];

/**
 * Extract coordinates from a council data item
 * @param {Object} item - The council data item containing latitude and longitude
 * @returns {Object} An object with lat and lng properties
 */
export function extractCouncilCoordinates(item) {
    // If the item already has processed coordinates, return them
    if (item.validLat !== undefined && item.validLng !== undefined) {
        return { lat: item.validLat, lng: item.validLng };
    }

    // Default coordinates deliberately set in the ocean to highlight missing data
    const defaultLat = -34;
    const defaultLng = 165;

    // Check if values exist and are not "#N/A"
    const lat = item.Latitude && item.Latitude !== "#N/A" ? parseFloat(item.Latitude.trim()) : defaultLat;
    const lng = item.Longitude && item.Longitude !== "#N/A" ? parseFloat(item.Longitude.trim()) : defaultLng;

    // Additional check for NaN after parsing
    const validLat = !isNaN(lat) ? lat : defaultLat;
    const validLng = !isNaN(lng) ? lng : defaultLng;

    // Store the processed coordinates on the item for future use
    item.validLat = validLat;
    item.validLng = validLng;
    item.hasRealCoordinates = item.Latitude &&
                             item.Latitude !== "#N/A" &&
                             item.Longitude &&
                             item.Longitude !== "#N/A" &&
                             !isNaN(lat) && !isNaN(lng);

    return { lat: validLat, lng: validLng };
}

/**
 * Creates a table displaying values for a specific field with counts
 * @param {Array} filteredData - The filtered data for counts
 * @param {Array} [allData=null] - Optional complete dataset for all possible values
 * @param {string} fieldName - The field to extract values from
 * @param {string} displayTitle - The title for the table
 * @param {Function} onSelectionChange - Callback function when selection changes
 * @param {Array} initialSelections - Array of initially selected values
 * @returns {HTMLElement} The created table element
 */
export function createFilterableFieldTable(filteredData, allData = null, fieldName, displayTitle, onSelectionChange, initialSelections = []) {
    // Determine which dataset to use for possible values
    const dataForValues = allData || filteredData;

    // Get all possible values from the dataset
    const allPossibleValues = new Set();

    // For Type fields, we need to check all type columns
    if (fieldName === "Type 1") {
        dataForValues.forEach(item => {
            TYPE_COLUMNS.forEach(col => {
                if (item[col]) allPossibleValues.add(item[col]);
            });
        });
    } else {
        // For other fields, just check the specific field
        dataForValues.forEach(item => {
            if (item[fieldName]) allPossibleValues.add(item[fieldName]);
        });
    }

    // Count occurrences in the filtered data
    const fieldValueCounts = new Map();

    // Initialize all possible values with count 0 if we're using allData
    if (allData) {
        allPossibleValues.forEach(value => {
            fieldValueCounts.set(value, 0);
        });
    }

    // Count occurrences in filtered data
    if (fieldName === "Type 1") {
        // For Type, count across all type columns
        filteredData.forEach(item => {
            TYPE_COLUMNS.forEach(col => {
                if (item[col] && allPossibleValues.has(item[col])) {
                    fieldValueCounts.set(item[col], (fieldValueCounts.get(item[col]) || 0) + 1);
                }
            });
        });
    } else {
        // For other fields, just count the specific field
        filteredData.forEach(item => {
            if (item[fieldName] && allPossibleValues.has(item[fieldName])) {
                fieldValueCounts.set(item[fieldName], (fieldValueCounts.get(item[fieldName]) || 0) + 1);
            }
        });
    }

    // Convert to array (no manual sorting needed)
    const valueCountsArray = Array.from(fieldValueCounts.entries());

    // Create data array for table
    const tableRowData = valueCountsArray.map(([value, count]) => ({
        [displayTitle]: value,
        "Count": count
    }));

    // Find which rows should be initially selected
    let initialValue = [];
    if (initialSelections && initialSelections.length > 0) {
        initialValue = tableRowData.filter(row =>
            initialSelections.includes(row[displayTitle])
        );
    }

    // Create the table with initial selections
    const table = Inputs.table(tableRowData, {
        columns: [displayTitle, "Count"],
        layout: "fixed",
        sort: "Count", // Sort by Count column
        reverse: true, // Sort in descending order
        rows: 7, // Show up to 7 rows
        multiple: true,
        width: "100%",
        required: false,
        value: initialValue
    });

    // Add selection event listener
    if (onSelectionChange) {
        table.addEventListener('input', () => {
            const selectedValues = table.value ?
                table.value.map(item => item[displayTitle]) :
                [];
            onSelectionChange(fieldName, selectedValues);
        });
    }

    return table;
}

// Alias for backward compatibility - will be deprecated
export const createFilterableFieldTableWithAllOptions = createFilterableFieldTable;

// Map to store council-to-marker references for quick lookup
const councilMarkerMap = new Map();

/**
 * Creates a unique hash for a council item
 * @param {Object} item - The council data object
 * @returns {string} A unique hash string
 */
function createCouncilItemHash(item) {
    return JSON.stringify(item);
}

/**
 * Creates popup content for a council, grouping findings by category.
 * Note: Content comes from our own preprocessed CSV data, not user input.
 * @param {Object} item - The council data object
 * @returns {string} HTML content for the popup
 */
function createCouncilPopupContent(item) {
    const parts = [];
    parts.push('<h1 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">');
    parts.push(item["Council"]);
    parts.push('</h1>');

    if (item["Type of audit report"]) {
        parts.push('<p style="margin: 0 0 8px 0"><strong>');
        parts.push(item["Type of audit report"]);
        parts.push('</strong></p>');
    }
    if (item["Financial year"]) {
        parts.push('<p style="margin: 0 0 8px 0">');
        parts.push(item["Financial year"]);
        parts.push('</p>');
    }

    // Group findings by category
    const categories = {};
    for (let i = 1; i <= 8; i++) {
        const type = item["Type " + i];
        const desc = item["Description " + i];
        if (type && desc) {
            if (!categories[type]) categories[type] = [];
            categories[type].push(desc);
        }
    }

    // Render grouped findings
    for (const [category, descriptions] of Object.entries(categories)) {
        parts.push('<h2 style="margin: 12px 0 4px 0; font-size: 14px; font-weight: bold; border-top: 1px solid #ccc; padding-top: 8px;">');
        parts.push(category);
        parts.push('</h2>');
        descriptions.forEach(desc => {
            parts.push('<p style="margin: 0 0 8px 0">');
            parts.push(desc);
            parts.push('</p>');
        });
    }

    return parts.join('');
}

/**
 * Creates map markers for each council and adds them to the map
 * @param {Array} councils - Array of council data objects
 * @param {L.LayerGroup} markerLayer - Leaflet layer group to add markers to
 * @param {Array} markerReferences - Array to store references to created markers
 * @param {L.Map} mapInstance - The Leaflet map instance
 */
export function createCouncilMapMarkers(councils, markerLayer, markerReferences, mapInstance) {
    mapInstance.eachLayer(function(layer) {
        if (typeof layer._popup != 'undefined') {
            layer.remove()
        }
    });

    // Clear the markerReferences array and marker map
    markerReferences.length = 0;
    councilMarkerMap.clear();

    councils.forEach(function(item) {
        // Use the pre-processed coordinates directly
        var marker = L.marker([item.validLat, item.validLng])
            .bindPopup(createCouncilPopupContent(item));

        // Store references to the marker using a unique hash
        markerReferences.push(marker);
        const uniqueHash = createCouncilItemHash(item);
        councilMarkerMap.set(uniqueHash, marker);

        marker.addTo(markerLayer);
    });

    markerLayer.addTo(mapInstance);
}

/**
 * Updates filter state and triggers display refresh
 * @param {string} fieldName - The field name that was changed
 * @param {Array} selectedValues - The new selected values
 * @param {Object} filterState - The filters object to update
 * @param {Function} refreshCallback - Callback function to refresh the display
 */
export function updateFilterAndRefresh(fieldName, selectedValues, filterState, refreshCallback) {
    filterState[fieldName] = selectedValues;
    refreshCallback();
}

/**
 * Creates and renders filter tables for data filtering
 * @param {Array} filteredData - The currently filtered data
 * @param {string} containerId - The ID of the container element
 * @param {Function} selectionHandler - The handler function for selection changes
 * @param {Object} filterState - The current filters
 * @param {Function} refreshCallback - Callback function to refresh the display
 * @param {Array} allData - The complete unfiltered dataset
 */
export function renderFilterTables(filteredData, containerId, selectionHandler, filterState, refreshCallback, allData) {
    // Get the existing container
    const tablesContainer = document.getElementById(containerId);
    // Clear the container
    tablesContainer.textContent = '';

    // Create field tables with preserved selections
    const filterFields = [
        { field: "Financial year", title: "Year" },
        { field: "Type 1", title: "Type" },
        { field: "Type of audit report", title: "Report Type" }
    ];

    // Use Lodash forEach for cleaner iteration
    _.forEach(filterFields, ({ field, title }) => {
        const tableDiv = document.createElement('div');
        tableDiv.className = 'field-table';

        // Create the table with all possible values from the complete dataset
        // but show counts from the filtered data
        const table = createFilterableFieldTable(
            filteredData,  // For counts
            allData,       // For all possible values
            field,
            title,
            (fieldName, selectedValues) => selectionHandler(fieldName, selectedValues, filterState, refreshCallback),
            filterState[field] // Pass current selections
        );

        tableDiv.appendChild(table);
        tablesContainer.appendChild(tableDiv);
    });
}

/**
 * Creates a function that refreshes the display with current filters
 * @param {Array} councilData - The original unfiltered councils data
 * @param {Object} filterState - Object containing filter selections for different fields
 * @param {L.LayerGroup} markerLayer - Leaflet layer group for council markers
 * @param {Array} markerReferences - Array to store references to created markers
 * @param {L.Map} mapInstance - The Leaflet map instance
 * @param {Object} displayOptions - Additional options including columns, layout, and icons
 * @param {string} filterContainerId - The ID of the container for filter tables
 * @returns {Function} A function that refreshes the display
 */
export function createDisplayRefresher(councilData, filterState, markerLayer, markerReferences, mapInstance, displayOptions, filterContainerId) {
    return function refreshView() {
        // Use Lodash for proper deep cloning of options
        const refreshOptions = _.cloneDeep(displayOptions);
        refreshOptions.refreshCallback = refreshView;
        refreshOptions.allData = councilData;  // Ensure the complete dataset is available

        return refreshFilteredDisplay(councilData, filterState, markerLayer, markerReferences, mapInstance, refreshOptions, filterContainerId);
    };
}

/**
 * Updates the display based on current filters
 * @param {Array} councilData - The original unfiltered councils data
 * @param {Object} filterState - Object containing filter selections for different fields
 * @param {L.LayerGroup} markerLayer - Leaflet layer group for council markers
 * @param {Array} markerReferences - Array to store references to created markers
 * @param {L.Map} mapInstance - The Leaflet map instance
 * @param {Object} displayOptions - Additional options including columns, layout, and icons
 * @param {string} filterContainerId - The ID of the container for filter tables
 * @returns {Array} The filtered results
 */
export function refreshFilteredDisplay(councilData, filterState, markerLayer, markerReferences, mapInstance, displayOptions, filterContainerId) {
    // Filter the councils based on selected values using Lodash
    const filteredCouncils = _.filter(councilData, item => {
        // If no filters are set for a category, it passes that filter
        const yearFilter = filterState["Financial year"].length === 0 ||
                          filterState["Financial year"].includes(item["Financial year"]);

        // Type filter - exclusive approach (must have ALL selected types)
        const typeFilter = filterState["Type 1"].length === 0 ||
                          filterState["Type 1"].every(type => {
                              // Check if this type appears in any of the type fields
                              return TYPE_COLUMNS.some(col => item[col] === type);
                          });

        const reportTypeFilter = filterState["Type of audit report"].length === 0 ||
                            filterState["Type of audit report"].includes(item["Type of audit report"]);

        return yearFilter && typeFilter && reportTypeFilter;
    });

    // Update the map
    createCouncilMapMarkers(filteredCouncils, markerLayer, markerReferences, mapInstance);

    // Update the main table
    const tableDiv = document.getElementById('table_div');
    tableDiv.textContent = '';  // Clear existing content

    // Create and add the table display
    tableDiv.appendChild(createSelectableCouncilTable(
        filteredCouncils,
        displayOptions.columns,
        displayOptions.layout,
        markerReferences,
        mapInstance
    ));

    // Update filter tables with the new filtered data and all possible options
    renderFilterTables(
        filteredCouncils,
        filterContainerId,
        updateFilterAndRefresh,
        filterState,
        displayOptions.refreshCallback,
        displayOptions.allData || councilData  // Pass the complete dataset
    );

    return filteredCouncils;
}

/**
 * Creates a highlighted icon for selected councils
 * @returns {L.DivIcon} The created icon
 */
function createHighlightedIcon() {
    return L.divIcon({
        html: layer((push) => {
            push(icon(faCircle, {
                transform: {
                    size: 64,
                    y: -28
                },
                styles: {
                    'color': 'white'
                }
            }))
            push(icon(faBuildingColumns, {
                transform: {
                    size: 36,
                    x: -2,
                    y: -28
                },
                styles: {
                    'color': 'red'
                }
            }))
        }).html,
        className: 'selected-council-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -36]
    });
}


/**
 * Creates and configures the Inputs table with event listeners for selection
 * @param {Array} councils - Array of council data objects
 * @param {Array} columnConfig - Array of column names to display
 * @param {string} layoutStyle - Layout style for the table
 * @param {Array} markerReferences - Array of map markers
 * @param {L.Map} mapInstance - The Leaflet map instance
 * @returns {HTMLElement} The created table element
 */
export function createSelectableCouncilTable(councils, columnConfig, layoutStyle, markerReferences, mapInstance) {
    // Create the highlighted icon once
    const highlightedIcon = createHighlightedIcon();

    const selection = Inputs.table(councils, {
        columns: columnConfig,
        layout: layoutStyle,
        sort: "Council",
        rows: 27,
        multiple: true,
        required: false
    });

    // Add a selection event listener
    selection.addEventListener('input', () => {
        // Reset all markers to default state
        markerReferences.forEach(marker => {
            marker.setIcon(L.Icon.Default.prototype);
            marker.setZIndexOffset(Math.round(marker.getLatLng().lat)); // Use latitude as default z-index
            marker.closePopup();
        });

        if (selection.value && selection.value.length > 0) { // Check if there are selected rows
            // Create bounds to fit all selected markers
            const bounds = L.latLngBounds();

            // Process each selected row
            selection.value.forEach(row => {
                // Get marker using the unique hash
                const uniqueHash = createCouncilItemHash(row);
                const marker = councilMarkerMap.get(uniqueHash);

                if (marker) {
                    marker.setIcon(highlightedIcon);
                    marker.setZIndexOffset(1000);

                    // Only open popup if exactly one item is selected
                    if (selection.value.length === 1) {
                        marker.openPopup();
                    } else {
                        marker.closePopup();
                    }

                    bounds.extend(marker.getLatLng());
                }
            });

            // If we have selected markers, fit the map to show all of them
            if (!bounds.isValid()) {
                mapInstance.setView([-40.9, 175.232], 5); // Reset to default view if no valid bounds
            } else {
                // Add extra padding when only one marker is selected to accommodate popup
                if (selection.value.length === 1) {
                    // Get marker using the unique hash
                    const uniqueHash = createCouncilItemHash(selection.value[0]);
                    const marker = councilMarkerMap.get(uniqueHash);

                    if (marker) {
                        marker.openPopup();
                        // Wait for popup to be created and rendered
                        setTimeout(() => {
                            const popupElement = marker.getPopup().getElement();
                            // Set a maximum height of 495px for the popup
                            const maxPopupHeight = 495;
                            const popupHeight = Math.min(
                                popupElement ? popupElement.offsetHeight : 150, // fallback to 150 if can't measure
                                maxPopupHeight
                            );

                            // Add extra padding when only one marker is selected to accommodate popup
                            const paddingOptions = {
                                paddingTopLeft: L.point(50, popupHeight + 50), // popup height plus some extra space
                                paddingBottomRight: L.point(50, 50)
                            };
                            mapInstance.fitBounds(bounds, paddingOptions);
                        }, 100); // Short delay to ensure popup is rendered
                    }
                } else {
                    const paddingOptions = {
                        paddingTopLeft: L.point(50, 50),
                        paddingBottomRight: L.point(50, 50)
                    };
                    mapInstance.fitBounds(bounds, paddingOptions);
                }
            }
        } else {
            // If no selection, reset to default view
            mapInstance.setView([-40.9, 175.232], 5);
        }
    });

    return selection;
}
