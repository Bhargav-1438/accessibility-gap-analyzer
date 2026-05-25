# Accessibility Gap Analyzer — Engineering Evolution Journal

This document records the architectural upgrades, mathematical transitions, optimization strategies, and engineering decisions throughout the lifecycle of the Accessibility Gap Analyzer platform. It serves as a research development log and infrastructure transition record.

---

## Phase 1: Visualization & Accessibility Scoring
**Status:** Completed
**Focus:** Foundation and UI

- **Objective:** Establish the core data ingestion and visualization pipeline.
- **Data Sourcing:** Integrated `OSMnx` for live fetching of OpenStreetMap facility data (Hospitals, Schools) and `GeoPandas` for loading static ward boundaries.
- **Scoring Engine:** Implemented a Euclidean (straight-line) distance metric between ward centroids and nearest facilities. Applied Min-Max normalization to generate a 0-100 `gap_score`.
- **Visualization:** Created a Streamlit dashboard with a Folium choropleth map overlaid with facility markers, using Esri World Imagery.

*Limitations Recognized:* Straight-line distance ignores physical topology (rivers, highways, lack of pedestrian crossings), leading to mathematically flawed accessibility models in real urban environments.

---

## Phase 2: Real-World Routing Topology
**Status:** Completed
**Focus:** Mathematical Validity & Infrastructure

- **Objective:** Replace Euclidean approximations with true walking-network distances.
- **Routing Module (`src/routing.py`):** Introduced a decoupled infrastructure layer leveraging `OSMnx` to fetch and `NetworkX` to navigate walking street graphs.
- **Caching Mechanism:** Implemented `.graphml` caching in `data/graphs/` to bypass redundant, expensive API calls and reduce latency from minutes to seconds, improving scalability.
- **Algorithm Optimization:** Utilized `nx.shortest_path_length` (multi-source shortest path) and `osmnx.nearest_nodes` (scikit-learn k-d tree) for scalable distance computation.
- **Scoring Update:** The `analysis_engine.py` was fundamentally rewritten to source distances strictly from the network routing engine. Travel time was calculated and stored for future use but kept out of the primary `gap_score` to maintain isolation from demographic/speed assumptions.

*Impact:* The system transitioned from a geometric toy to a mathematically rigorous urban model, identifying previously hidden topological barriers.

---

## Phase 2.5: DBSCAN Clustering Engine
**Status:** Completed
**Focus:** Spatial Intelligence & Underserved-Region Discovery

- **Objective:** Transform isolated ward-level scoring into regional urban-scale underserved zone intelligence.
- **Machine Learning (`src/ml_engine.py`):** Integrated `scikit-learn` to apply DBSCAN clustering to wards exhibiting High or Critical accessibility gaps.
- **Algorithm Parameters:** 
  - `eps = 2000m`: Determined as the optimal urban walkability threshold to connect adjacent underserved wards without over-clustering the city.
  - `min_samples = 2`: Configured to be sensitive to early-stage or isolated infrastructure failures.
- **Convex Hull Generation:** Grouped clustered wards using `GeoPandas` and wrapped them in convex hulls to geometrically represent "Infrastructure Deserts". 
- **Visualization Update:** Convex hulls overlay directly on the Folium map to instantly communicate regional failures (e.g., "North-East Healthcare Desert") rather than individual ward statistics.

*Impact:* The platform shifts from "visualization software" into a true "geospatial urban intelligence system" capable of identifying strategic intervention regions.

---

## Phase 3A: Interactive Urban Intervention Simulation
**Status:** Completed
**Focus:** Hypothesis Testing & Delta Analysis

- **Objective:** Allow urban planners to simulate hypothetical infrastructure placements and instantly visualize the topological impact on accessibility gap scores.
- **Simulation Engine (`src/simulation_engine.py`):** A strictly isolated intervention layer that injects hypothetical facility nodes into an in-memory copy of the routing graph. This explicitly avoids mutating the cached `.graphml` files while allowing the engine to treat the new facility exactly like a real hospital or school.
- **Delta-Scoring Pipeline:** The engine routes and scores the network *twice*—once on the baseline graph and once on the injected graph. It computes absolute score changes, percent improvement, and severity shifts.
- **Mathematical Integrity:** Implemented delta scoring where a negative delta is scientifically defined as an accessibility improvement (lower gap score = better accessibility).
- **Interactive Map Response System:** Integrated Streamlit session state and Folium click-capture to allow live interaction. Planners click the map, and the system autonomously reroutes the network, renders a visually distinct glowing simulated marker, and overlays a Delta Choropleth highlighting improved corridors in green while leaving unresolved areas red.

*Impact:* The platform evolved from "urban accessibility intelligence" into "interactive urban intervention intelligence," setting the final foundational stage for automated Phase 3B optimization.

---

## Phase 3B: Automated Urban Intervention Optimization
**Status:** Completed
**Focus:** Decision-Support & AI Recommendation

- **Objective:** Automatically identify the most impactful facility placement locations to structurally reduce urban accessibility inequality.
- **Optimization Engine (`src/optimization_engine.py`):** Implemented a True Greedy, p-median inspired optimization algorithm. It evaluates the impact of placing a facility in candidate wards, confirms the placement that maximizes overall gap reduction, officially updates the baseline city state, and iterates for the next best placement.
- **Candidate Filtering Optimization:** To prevent combinatorial explosion and excessive runtime, candidate locations are strictly limited to the centroids of wards classified as `Critical` or `High`. This focuses the AI directly on intervention urgency.
- **Explainable Planning Intelligence:** Built a text-generation layer into the optimization engine that outputs human-readable reasoning for every recommended placement (e.g., projected gap reduction, affected population, wards shifted out of critical status).
- **Auto-Suggest UX:** Added an Auto-Suggest sidebar interface allowing planners to request $N$ optimized interventions. The system responds by placing distinct, color-ranked star markers on the map, complete with diagnostic popups detailing the projected regional impact.

*Impact:* The platform has officially transitioned from an intervention simulator to a true **Urban Decision-Support Infrastructure**, answering not just "where are the problems", but "how do we solve them most effectively."

---

## Phase 3C: Isochrone Coverage Intelligence
**Status:** Completed
**Focus:** Real-World Service Area Modeling

- **Objective:** Visually transition the platform from "point-based facility visualization" to "real-world service-area coverage" by generating network-constrained walkable polygons (walksheds).
- **Coverage Engine (`src/coverage_engine.py`):** Engineered a dedicated service-area layer using `networkx.ego_graph()` to extract subgraphs reachable within 5, 10, 15, and 30 minutes of walking (at 5 km/h).
- **Polygon Construction Strategy:** Extracted network nodes are bounded by a mathematically fast Convex Hull rather than a computationally heavy Concave Hull (Alpha Shape). The polygon is then aggressively simplified via `Shapely` (`tolerance=0.0005`, `preserve_topology=True`) to maintain a responsive rendering UX without crashing Folium with thousands of excessive vertices.
- **Targeted Intelligence:** To prevent map clutter (polygon soup), isochrones are *not* rendered globally. They are dynamically generated only for *Active Interventions* (Simulated Facilities and AI Recommendations).
- **UX Integration:** When "Coverage Intelligence" is toggled on, hovering over the semi-transparent nested polygons reveals the walk-time threshold, the estimated physical coverage area (sq.km), and a synthetic population coverage estimate.

*Impact:* The platform now visually answers exactly "what physical urban boundaries are successfully served by this intervention," completing the real-world accessibility modeling arc.

---

## Phase 3D: Civic Infrastructure Platformization
**Status:** Completed
**Focus:** Deployment, Scalability, and APIs

- **Objective:** Platformize the entire project, transforming it from a research-grade academic dashboard into a scalable, multi-city, operational civic-tech system.
- **API Gateway (`api/main.py`):** Introduced a FastAPI microservice architecture. The platform's intelligence (scoring, routing, optimization, clustering) is now accessible headlessly via structured REST endpoints, decoupling the analytical engine from the Streamlit UI.
- **Multi-City Architecture (`src/city_manager.py`):** Transitioned away from hardcoded boundaries. The platform now dynamically supports any city globally by integrating `osmnx.geocode_to_gdf` as an intelligent fallback. If a local boundary file is missing, the engine autonomously scrapes, cleans, and caches the administrative boundary directly from OpenStreetMap.
- **Report Engine (`src/report_engine.py`):** Added a planner-oriented export pipeline capable of aggregating a session's AI recommendations, gap scores, and coverage metadata into structured Markdown and JSON intelligence reports.
- **Deployment Hardening & Docker:** Engineered a dual-container `docker-compose` setup housing the API and Dashboard independently. A critical `precompute.py` script was introduced to force graph generation during the Docker build phase, guaranteeing zero cold-start API latency in production.
- **Scenario Persistence (`src/session_manager.py`):** Empowered planners to persist their workflows by writing active session JSON blobs to disk, ensuring critical optimization runs aren't lost across reboots.

*Impact:* The Accessibility Gap Analyzer is now an **operational civic-tech platform**, fully deployable, institutionally scalable, and perfectly positioned for government pilots or open-source contribution.
