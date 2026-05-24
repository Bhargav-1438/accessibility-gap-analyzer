# Accessibility Gap Analyzer — Master Documentation

## 1. Project Overview

### Problem Statement
Urban planning and resource allocation often suffer from spatial inequalities, where certain neighborhoods lack adequate access to fundamental civic services such as healthcare and education. Identifying these "blind spots" manually is a tedious, data-intensive process that hinders rapid policy response.

### Vision
To create a democratized, open-source geospatial intelligence platform that empowers city planners, researchers, and citizens to visually identify and quantify spatial inequalities in urban infrastructure.

### Purpose
The Accessibility Gap Analyzer serves as a functional diagnostic tool. It ingests live, open-source city data and highlights underserved wards, translating complex spatial relationships into easily actionable, visually compelling insights.

### Prototype Goals
The primary goal of this Phase 1 prototype was to build a robust, deployment-ready foundation. It targets a single city (Hyderabad, India) to prove the viability of automated data ingestion, Euclidean distance-based accessibility scoring, and interactive web-based map rendering without requiring massive enterprise infrastructure.

---

## 2. Project Evolution

### How the Idea Evolved
Initially conceptualized as a static, script-based analytical tool, the project quickly evolved. Recognizing that spatial data is best understood visually, the focus shifted from generating static CSV reports to building an interactive, map-centric web application.

### Transition to Interactive Platform
The shift to Streamlit and Folium marked a major milestone. What began as an invisible backend process was transformed into a "modern civic-tech dashboard." This involved transitioning from basic mathematical outputs to an intuitive UI featuring dynamic sidebars, live filtering, and interactive hover tooltips that allow non-technical users to explore the data safely.

### Major Milestones
1. **Data Pipeline:** Successfully querying OpenStreetMap via OSMnx for live facility data.
2. **Analysis Engine:** Implementing the core distance and scoring mathematics.
3. **Visualization:** Integrating Folium to render interactive Esri satellite maps and choropleths.
4. **UI/UX Polish:** Upgrading to a premium, dark-themed civic dashboard with live metrics and toasts.
5. **Optimization:** Resolving CRS warnings, caching unhashable data types, and ensuring deployment stability.

---

## 3. System Architecture

The project utilizes a strict, modular three-tier architecture ensuring separation of concerns:

### `src/data_ingestion.py` (Data Layer)
*   **Responsibility:** Handles all external data sourcing.
*   **Flow:** Loads static GeoJSON files (like city ward boundaries) using GeoPandas, and makes dynamic API calls to OpenStreetMap via OSMnx to fetch the latest hospital and school coordinates.

### `src/analysis_engine.py` (Logic Layer)
*   **Responsibility:** The mathematical core of the platform.
*   **Flow:** Takes the raw spatial data, reprojects it to a safe coordinate system, calculates zone centroids, computes distances to the nearest facilities, and applies the scoring algorithm to generate the final 0–100 Gap Score. 

### `src/visualization.py` (Presentation Layer)
*   **Responsibility:** Generates the visual map outputs.
*   **Flow:** Ingests the scored data and builds a Folium map object. It layers Esri satellite tiles, a color-coded choropleth, point markers, and interactive hover tooltips.

### `app.py` (Controller/Dashboard Layer)
*   **Responsibility:** The main Streamlit entry point.
*   **Flow:** Manages the user interface, sidebar inputs, layout, and metrics. It orchestrates the flow of data between the three `src` modules, aggressively caches expensive operations, and injects custom CSS for the dark theme.

---

## 4. Technology Stack

*   **Streamlit:** Chosen for its rapid prototyping capabilities. It allows the creation of complex, reactive web dashboards purely in Python without requiring a separate frontend framework (like React).
*   **Folium:** A powerful Python wrapper for Leaflet.js. Chosen because it excels at rendering interactive, layered web maps seamlessly within Streamlit.
*   **GeoPandas:** Essential for handling spatial data operations. It extends Pandas to support geometric types, making spatial joins, buffering, and CRS transformations trivial.
*   **OSMnx:** Chosen for its direct, Pythonic interface to the OpenStreetMap Overpass API. It eliminates the need to manually download or scrape POI (Point of Interest) datasets.
*   **Shapely:** The underlying geometry engine used by GeoPandas. Used implicitly to calculate centroids and Euclidean distances between polygons and points.
*   **Pandas & NumPy:** Standard libraries utilized for rapid, vectorized data manipulation, mathematical normalization, and statistical handling of the gap scores.

---

## 5. Geospatial Analysis Logic

### GeoJSON Boundaries
The city is divided into polygons (wards/zones) defined in a GeoJSON file. GeoPandas loads these polygons into a `GeoDataFrame`.

### CRS Handling (EPSG:4326 vs EPSG:3857)
*   **EPSG:4326:** The standard geographic coordinate system representing data in Latitude and Longitude degrees. (Used by GeoJSON and Folium).
*   **EPSG:3857:** A projected coordinate system representing the earth on a flat, 2D plane measured in **meters**.
*   **The Logic:** Calculating flat distances on a curved earth (EPSG:4326) creates mathematical distortion and triggers GeoPandas warnings. Before any math is done, the engine safely projects data to `EPSG:3857`, performs the calculation in meters, and then safely returns the data in `EPSG:4326` so Folium can plot it correctly.

### Calculations
*   **Centroids:** The absolute geographic center point of each ward polygon is calculated.
*   **Euclidean Distance:** The system loops through each ward's centroid and measures the straight-line (Euclidean) distance to every single hospital and school, recording the minimum (nearest) value.

### Gap Scoring Logic
1.  **Averaging:** The nearest hospital distance and nearest school distance are averaged to create a `combined_distance`.
2.  **Min-Max Normalization:** This raw meter value is mathematically compressed into a uniform `0 to 100` scale. The ward with the best access becomes `0`, and the worst becomes `100`.
3.  **Categorization:** 
    *   0–30: Low
    *   31–60: Moderate
    *   61–80: High
    *   81–100: Critical

---

## 6. Dashboard Features

*   **Satellite Map:** High-resolution Esri World Imagery serves as the base layer for realistic urban context.
*   **Choropleth Visualization:** Wards are filled with a translucent `RdYlGn_r` color gradient, visually highlighting problem areas in red.
*   **Sidebar Filters:** Allows users to dynamically toggle hospital/school markers and filter out wards based on minimum gap scores.
*   **Metrics Cards:** A top row of KPI widgets displaying Visible Wards, Critical Zones, and Facility counts.
*   **Search System:** A text input that isolates and zooms the map to a specific ward by name.
*   **Hover Tooltips:** Interactive popups that reveal exact scores, distances, and ward names when mousing over the map.
*   **Severity Badges:** Emoji-based color badges (🟢 🟡 🟠 🔴) in the tooltips for immediate cognitive recognition of gap severity.
*   **Dynamic Filtering:** The map and metrics update instantly in response to sidebar inputs.
*   **Loading Toasts:** Unobtrusive, slide-in notifications that provide professional feedback during the data loading and processing phases.
*   **Caching System:** Ensures the app remains lightning-fast by preventing redundant API calls and recalculations.

---

## 7. UI/UX Design Decisions

The UI was intentionally designed as a **modern, dark-themed civic-tech dashboard**.
*   **Dark Theme:** Custom CSS (`#0E1117` background, `#1A202C` cards) reduces eye strain, makes brightly colored map data pop, and provides a premium analytics feel.
*   **Wide Layout:** Streamlit's `layout="wide"` and the map's `use_container_width=True` ensure maximum screen real estate is dedicated to the spatial data.
*   **Sidebar Structure:** Moves utilitarian controls out of the main view, keeping the user focused on the map and top-line metrics.
*   **Tooltip Design:** Opting for hover tooltips over click-popups significantly speeds up data exploration.

---

## 8. Performance Optimization

*   **Streamlit Caching (`@st.cache_data`):** Network requests (OSMnx) and heavy geometry math are cached. If a user moves a slider, the app instantly retrieves the cached calculations instead of re-running the backend.
*   **Map Reload Prevention:** Implementing `st_folium(..., returned_objects=[])` is a critical optimization. It prevents the entire Streamlit application from crashing or stuttering when the user clicks or pans the map.
*   **GeoDataFrame Trimming:** Before sending data to Folium, `zones_clean` is created to strip out heavy, unnecessary columns. This drastically shrinks the GeoJSON payload, ensuring the browser renders the map smoothly without memory bloat.

---

## 9. Deployment Documentation

*   **GitHub Integration:** The project relies on standard version control. Pushing code to the `main` branch acts as the source of truth for deployment.
*   **Streamlit Community Cloud:** The easiest and recommended deployment route. It hooks directly into the GitHub repository and auto-deploys `app.py`.
*   **Dependency Considerations:** The `requirements.txt` is crucial. Geospatial libraries (like `geopandas` and `shapely`) rely on heavy C-binaries (GDAL, GEOS). Streamlit Cloud's default Linux environment handles these reasonably well, but strict versioning in the future may be required to prevent conflicts.

---

## 10. Troubleshooting History

*   **Streamlit Permissions:** Initial issues running Streamlit natively were resolved by ensuring execution via `python -m streamlit run app.py` to correctly initialize the server context.
*   **GeoJSON Serialization:** Folium choropleths failed to map data because of ID mismatches. Fixed by explicitly generating a string `zone_id` column and mapping `key_on='feature.properties.zone_id'`.
*   **CRS Warnings:** GeoPandas threw `Geometry is in a geographic CRS` warnings during math operations. Resolved by explicitly chaining `.to_crs(epsg=3857)` for math, and converting back to `4326` for mapping.
*   **Cache Hashing Errors:** Streamlit crashed with an `UnhashableParamError` when trying to cache `GeoDataFrames`. Fixed by renaming parameters to `_zones_gdf`, instructing the engine to bypass hashing for those objects.

---

## 11. Current Limitations

*   **Single-City Support:** The app currently hardcodes "Hyderabad, India" and relies on a static local file (`ghmc-wards.geojson`). It cannot dynamically switch cities yet.
*   **Euclidean Approximation:** Straight-line (as the crow flies) distance is used. This does not account for roads, traffic, rivers, or actual walking paths.
*   **No Routing Engine:** The prototype lacks integration with routing graphs (like OSRM or NetworkX).
*   **No ML Clustering:** Facilities are mapped individually, without density clustering (e.g., DBSCAN) to identify macro-patterns.

---

## 12. Future Roadmap

*   **Multi-City Architecture:** Implement a dynamic dropdown that fetches boundary GeoJSONs from an external AWS S3 bucket or GitHub raw link.
*   **Network-Based Routing:** Upgrade distance calculations from Euclidean to actual street-network walking distances using OSMnx graph features.
*   **DBSCAN Clustering:** Add Machine Learning algorithms to automatically group high-density facility areas and identify statistical "deserts."
*   **Predictive Placement:** Implement an algorithm that suggests optimal GPS coordinates for a new hospital or school to maximize gap reduction.
*   **Public APIs:** Expose the accessibility scoring engine via FastAPI so other developers can query the data.
*   **Real-time Data:** Integrate population density datasets to weight the gap score (e.g., a gap in a highly populated area scores worse than a gap in an industrial zone).

---

## 13. Repository Structure

```text
accessibility-gap-analyzer-main/
│
├── data/
│   └── boundaries/
│       └── ghmc-wards.geojson      # Static city boundary data
│
├── src/
│   ├── __init__.py                 # Package initializer
│   ├── data_ingestion.py           # Loads GeoJSON & fetches OSM API data
│   ├── analysis_engine.py          # Math, CRS handling, and scoring algorithms
│   └── visualization.py            # Folium map, tooltip, and layer generation
│
├── app.py                          # Main Streamlit dashboard UI and layout
├── requirements.txt                # Python library dependencies
├── PRD.md                          # Initial Project Requirements Document
└── ACCESSIBILITY_GAP_ANALYZER_DOCUMENTATION.md # Master project documentation
```

---

## 14. Final Summary

The Accessibility Gap Analyzer is a testament to the power of modern, open-source Python geospatial stacks. By seamlessly combining Streamlit's reactive UI, GeoPandas' spatial processing, and OSMnx's live data capabilities, the project transforms raw, unorganized city data into an elegant, deployment-ready civic-tech tool. 

It successfully demonstrates that complex urban infrastructure problems can be visualized and analyzed rapidly, providing a strong, highly scalable foundation for future Machine Learning and advanced routing enhancements.
