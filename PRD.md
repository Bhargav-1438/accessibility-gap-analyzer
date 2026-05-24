# **PROJECT REQUIREMENTS DOCUMENT (PRD)**

## Accessibility Gap Analyzer — Prototype Version

---

## **1. Objective**

To design and develop a web-based system that identifies urban areas with poor access to essential services such as hospitals and schools, and visualizes these accessibility gaps using a satellite-based geospatial interface.

---

## **2. Scope (Prototype Phase)**

### **In Scope**

* City selection (Hyderabad as default)
* Extraction of hospital and school locations
* Area/zone-based accessibility analysis
* Gap score calculation for each zone
* Satellite map visualization with overlays

### **Out of Scope (Future Phases)**

* Machine Learning clustering (DBSCAN, K-Means)
* Multi-modal transport analysis
* Optimal facility placement algorithms
* Full-scale production deployment

---

## **3. Target Users**

* Students / Researchers (demo use)
* Urban planning enthusiasts
* Municipal-level conceptual use (prototype stage)

---

## **4. System Overview**

The system consists of three main layers:

### **Layer 1: Data Collection**

* Fetch hospital and school data from OpenStreetMap
* Load city boundary / zone data (GeoJSON / shapefile)

### **Layer 2: Analysis Engine**

* Compute distance from each zone to nearest facility
* Assign a gap score (0–100 scale)

### **Layer 3: Visualization**

* Render a satellite map
* Overlay zones with color-coded gap scores
* Display facility markers

---

## **5. Core Features**

### **Feature 1: City Input**

* User selects or loads a city (Hyderabad default)
* System loads corresponding zone boundaries

---

### **Feature 2: Facility Data Ingestion**

* Extract:

  * Hospitals
  * Schools
* Data stored as geospatial points

---

### **Feature 3: Distance Analysis**

* Calculate distance from zone centroid to nearest facility
* Initial implementation uses straight-line (Euclidean distance)

---

### **Feature 4: Gap Score Calculation**

* Score range: 0–100

**Formula (Prototype):**
Gap Score = Distance Factor + (Optional Population Weight)

**Classification:**

* 0–30 → Low Gap
* 31–60 → Moderate Gap
* 61–80 → High Gap
* 81–100 → Critical Gap

---

### **Feature 5: Satellite Map Visualization**

* Use satellite tile layer (Mapbox / Esri)
* Overlay:

  * Colored zones (choropleth)
  * Facility markers (icons)
* Interactive map (zoom, pan)

---

### **Feature 6: Basic Controls**

* Toggle:

  * Hospitals ON/OFF
  * Schools ON/OFF
* Gap score legend display

---

## **6. UI/UX Design Requirements**

### **Design Type**

* Web-based dashboard

### **Layout**

* Main screen: Full-width satellite map
* Side panel:

  * Controls (toggles)
  * Legend (gap score colors)

### **Design Principles**

* Minimalistic
* Data-focused
* High contrast (clear red/green zones)
* No unnecessary animations

---

## **7. Technology Stack**

### **Frontend / UI**

* Streamlit (web interface)
* Folium (map rendering)

### **Mapping**

* Leaflet (via Folium)
* Satellite tiles:

  * Mapbox Satellite OR Esri World Imagery

### **Backend**

* Python 3.11

### **Geospatial Processing**

* GeoPandas
* Shapely

### **Data Source**

* OpenStreetMap (via OSMnx)

### **Optional**

* Pandas (data handling)
* NumPy (calculations)

---

## **8. Data Requirements**

### **Required**

* Hospital locations (latitude, longitude)
* School locations (latitude, longitude)
* Zone/ward boundaries (GeoJSON or shapefile)

### **Optional**

* Population data (for improved scoring)

---

## **9. System Flow**

1. User selects city
2. System loads zone boundaries
3. Fetch hospital & school data
4. Compute nearest distances
5. Calculate gap scores
6. Render satellite map
7. Display colored zones + markers

---

## **10. Output**

* Interactive satellite map
* Color-coded zones showing accessibility levels
* Visible markers for facilities
* Clear identification of underserved areas

---

## **11. Constraints**

* Prototype-level accuracy (not production-grade)
* Limited to available open-source data
* Distance calculation simplified (no full routing yet)

---

## **12. Success Criteria**

* System runs without errors
* Map loads correctly with satellite view
* Zones are visibly differentiated by gap score
* User can clearly identify high-gap areas

---

## **13. Future Enhancements**

* ML-based clustering (DBSCAN)
* Network-based walking distance analysis
* Optimal facility placement suggestions
* Multi-city scalability
* Full dashboard with analytics

---

## **14. Summary**

The prototype focuses on building a functional and visually clear system that demonstrates accessibility gap analysis using geospatial data. The emphasis is on clarity, usability, and a strong foundation for future expansion.
