# Accessibility Gap Analyzer — Master Documentation

## 1. Platform Overview
Urban infrastructure is rarely distributed equally. Systemic accessibility inequality results in entire neighborhoods facing critical barriers to essential services like healthcare and education. While traditional GIS systems excel at visualizing static data, they often fail to model real-world topology or offer actionable intelligence for intervention.

The **Accessibility Gap Analyzer** is a topology-aware urban accessibility intelligence and intervention planning system. Moving beyond geometric proximity approximations, the platform models real pedestrian networks, autonomously discovers systemic infrastructure deserts via spatial machine learning, and serves as an interactive decision-support infrastructure. It empowers urban planners and municipal agencies not only to identify *where* the problems are, but to mathematically optimize *how* to solve them.

---

## 2. Engineering Evolution Timeline

The platform was built through a rigorous, phased engineering evolution:

*   **Phase 1: Accessibility Visualization (Geometric Approximation)**
    *   *Motivation:* Establish a baseline data ingestion and visualization pipeline.
    *   *Transition:* Relied on Euclidean (straight-line) distance. While computationally cheap, this was mathematically insufficient for real urban environments, ignoring physical barriers like rivers and highways.
*   **Phase 2: Topology-Aware Routing Engine**
    *   *Motivation:* Transition to topological realism.
    *   *Transition:* Stripped out Euclidean logic in favor of `OSMnx` and `NetworkX` to navigate actual walkable street networks, generating highly accurate pedestrian accessibility scores based on graph topology.
*   **Phase 2.5: Spatial Machine Learning (DBSCAN Clustering)**
    *   *Motivation:* Shift from individual ward-level scoring to regional intelligence.
    *   *Transition:* Integrated `scikit-learn` to cluster adjacent high-gap wards into systemic "Infrastructure Deserts", generating regional convex hulls for strategic awareness.
*   **Phase 3A: Interactive Urban Intervention Simulation**
    *   *Motivation:* Evolve from static analytics to hypothesis testing.
    *   *Transition:* Engineered an isolated simulation layer to dynamically inject hypothetical facilities into in-memory graphs, recalculating gap scores in real-time to visualize intervention impact (Delta Choropleth).
*   **Phase 3B: Automated Intervention Optimization**
    *   *Motivation:* Provide automated decision-support intelligence.
    *   *Transition:* Implemented a True Greedy, p-median inspired optimization algorithm to evaluate candidate wards and automatically recommend placements that maximize gap reduction.
*   **Phase 3C: Isochrone Coverage Intelligence**
    *   *Motivation:* Move from point-based markers to real-world service area modeling.
    *   *Transition:* Leveraged `nx.ego_graph` and convex hulls to render network-constrained walk-time polygons (walksheds), displaying exact physical coverage capabilities.
*   **Phase 3D: Civic Infrastructure Platformization**
    *   *Motivation:* Transform the academic dashboard into deployable operational software.
    *   *Transition:* Introduced a FastAPI gateway, multi-city dynamic fallbacks, session persistence, Docker-compose dual-container architecture, and zero cold-start graph precomputation.

---

## 3. Final System Architecture

The project utilizes a strict modular, decoupled architecture:

*   **`src/routing.py` (Routing Layer):** Manages local caching and graph navigation via `OSMnx` and `NetworkX`.
*   **`src/analysis_engine.py` (Analysis Layer):** Translates raw network distances into normalized 0-100 gap scores while handling unreachable nodes safely.
*   **`src/ml_engine.py` (Spatial ML Layer):** Ingests scored data and applies DBSCAN clustering to locate infrastructure deserts.
*   **`src/simulation_engine.py` (Simulation Layer):** Safely injects hypothetical nodes into a copied memory graph and routes a before/after pipeline to calculate spatial deltas.
*   **`src/optimization_engine.py` (Optimization Layer):** Orchestrates the True Greedy iterative loop to recommend optimal facility placements.
*   **`src/coverage_engine.py` (Coverage Intelligence Layer):** Uses network ego-graphs to extract walksheds and generates mathematically safe isochrone polygons.
*   **`src/report_engine.py` (Reporting Layer):** Compiles active session state and ML intelligence into structured Markdown and JSON exports.
*   **`src/session_manager.py` (Session Persistence Layer):** Serializes active workflows to disk, ensuring critical planning sessions survive reboots.
*   **`src/city_manager.py` (Multi-City Management Layer):** Abstracts geometry loading, dynamically downloading OSM boundaries if local files are missing.
*   **`api/main.py` (API Gateway):** Exposes the platform’s core intelligence engines via headless FastAPI REST endpoints.

---

## 4. Routing Intelligence & Topological Accessibility

Euclidean distance is scientifically insufficient for real urban accessibility analysis. Two wards geometrically close together may be topologically isolated by a railway track or river, leading to dangerous overestimations of healthcare access.

The routing layer solves this by downloading and caching physical walkable street graphs via `OSMnx`. Geometries are snapped to the nearest street nodes using vectorized k-d trees (`scikit-learn`). The system then utilizes `NetworkX`'s highly optimized multi-source shortest-path algorithms to calculate exact physical walking distances. Unreachable topographies trigger graceful failure handling, capping distances intelligently to preserve the normalization scale.

---

## 5. Spatial Intelligence & Infrastructure Desert Detection

Discovering multi-ward failures is achieved using Density-Based Spatial Clustering of Applications with Noise (DBSCAN). Wards flagged as `High` or `Critical` severity are extracted and projected into a metric CRS (EPSG:3857) to ensure uniform distance calculations.

Configured with a mathematically defendable `eps=2000m` (walkability threshold) and `min_samples=2`, the ML engine groups these adjacent wards and wraps them in convex hulls. The platform thus autonomously discovers systemic multi-ward accessibility failures (e.g., a "North-East Healthcare Desert"), elevating analysis from localized symptoms to regional diseases.

---

## 6. Interactive Intervention Simulation

Transitioning from static analytics into live intervention intelligence required deep isolation logic. When a planner drops a simulated hospital on the map, the simulation engine creates a safe, in-memory `.copy()` of the routing graph. 

It assigns the new facility a unique ID, snaps it to the network with a zero-weight edge, and recalculates the entire city's accessibility matrix. It mathematically derives a `delta_score` (where a negative delta equates to accessibility improvement) and instantly updates the UI, rendering a "Delta Choropleth" that visibly shrinks the infrastructure desert clusters in real-time.

---

## 7. Automated Optimization Intelligence

To automatically identify high-impact infrastructure interventions, the platform utilizes a True Greedy optimization loop inspired by the p-median facility location problem. 

To ensure performance, candidate filtering restricts testing strictly to the centroids of `Critical` or `High` severity wards. For each candidate, the engine routes a full simulation, evaluates the total gap score reduction, and estimates the affected population. Once the single best location is identified, it is officially injected into the "Current State" baseline. The engine then iterates, ensuring that Intervention #2 is optimized against the newly improved urban landscape, preventing overlapping or redundant recommendations. Finally, it generates explainable, human-readable reasoning for every placement.

---

## 8. Isochrone Coverage Intelligence

To model real-world service areas, the platform transitions from point-based facility markers to network-constrained isochrone polygons (walksheds). 

The coverage engine uses `nx.ego_graph` to traverse outward from a facility along street edges, extracting all nodes reachable within 5, 10, 15, and 30-minute thresholds. These node clouds are bound by a computationally fast Convex Hull. To ensure UI stability, the polygons are aggressively simplified (`tolerance=0.0005`, `preserve_topology=True`), drastically reducing vertex counts while maintaining accurate topological boundaries.

---

## 9. Multi-City Scalability Architecture

To ensure the platform can scale to virtually any urban region globally without manual code rewrites, `src/city_manager.py` implements a dynamic boundary fallback system. 

When a user selects a new city (e.g., Chennai or Bangalore), the engine searches for local GeoJSON bounds. If absent, it autonomously executes `osmnx.geocode_to_gdf()`, scrapes the administrative geometry from OpenStreetMap, cleans the data structures, and permanently caches it locally. 

---

## 10. API & Platformization Layer

The platform’s analytical core is decoupled from the dashboard frontend via a FastAPI gateway (`api/main.py`). Endpoints such as `/optimize` and `/isochrones` utilize strict `Pydantic` validation to ingest parameters and return deeply structured JSON intelligence. This operational architecture allows external municipal software, mobile applications, or third-party researchers to integrate directly with the Gap Analyzer's routing and ML engines.

---

## 11. Deployment & Infrastructure Hardening

To guarantee production reliability, the system utilizes a dual-container `docker-compose` architecture, cleanly separating the API microservice from the Streamlit frontend. 

Crucially, geospatial systems face severe cold-start penalties when downloading massive urban graphs from the Overpass API. To solve this, `precompute.py` is executed directly within the `Dockerfile` build step. This forces the pre-generation and caching of all `OSMnx` graphs and boundaries. When the Docker container is deployed to a cloud instance, it boots instantly with zero external API latency.

---

## 12. Planner Workflow & Operational UX

The platform is designed to support human + AI collaborative urban planning. Planners navigate via a modular sidebar composed of collapsible UX elements (`st.expander`), keeping the interface uncluttered. 

A standard workflow involves: observing the baseline infrastructure deserts, toggling the Auto-Suggest Engine to request optimized interventions, and clicking an AI Recommendation Pin to trigger the Simulation Engine. This instantly renders the Delta Choropleth and Isochrone Coverage layers, allowing the planner to visually validate the AI's mathematical reasoning. Session persistence ensures that these workflows can be saved and resumed.

---

## 13. Export & Reporting Systems

Actionable intelligence requires exportability. The `src/report_engine.py` aggregates the planner's active session—including systemic gap summaries, ranked intervention coordinates, expected severity shifts, and isochrone coverage areas—into structured Markdown and JSON reports. This allows insights to easily transition from the digital dashboard into government review panels, NGO planning meetings, or policy documents.

---

## 14. Scalability & Performance Engineering

Optimization is computationally expensive. The platform maintains responsiveness through aggressive architectural performance engineering:
*   **Vectorized Node Mapping:** `scikit-learn` k-d trees map thousands of coordinates to graph nodes in milliseconds.
*   **Graph Reuse:** The base routing graph is cached to disk and strictly copied in-memory for simulations, avoiding redundant Overpass API hits.
*   **Polygon Simplification:** Isochrone hulls are stripped of excess vertices to preserve Folium rendering performance.
*   **Candidate Filtering:** The optimization engine deliberately ignores `Low` and `Moderate` wards, drastically reducing the routing permutation space.

---

## 15. Future Evolution Roadmap

While the platform is a fully operational decision-support system, future architectural evolutions could include:
*   **Real Census Integration:** Fusing actual demographic block data into the Gap Score for vulnerability-weighted accessibility modeling.
*   **Public Transit Routing:** Introducing General Transit Feed Specification (GTFS) data to complement the pedestrian walking networks with multimodal commute times.
*   **Weighted Facility Costs:** Upgrading the optimization engine to account for municipal land costs and budget constraints.
*   **Cloud-Native Scaling:** Transitioning the local `.graphml` caching layer into a distributed Redis or AWS S3 architecture for massive horizontal scaling.

---

## 16. Production Deployment Journey

Transitioning the platform from a powerful local prototype to a production-stable cloud deployment on Railway's free-tier infrastructure (500MB RAM limit) presented severe engineering challenges. The stabilization process required deep architectural pivots:

*   **Initial Build-Time Failures:** Attempting to precompute massive urban routing graphs inside the Docker build step using `precompute.py` caused timeouts and memory collapse during container compilation.
*   **Streamlit Reactive Rerender Issues:** Streamlit's architecture natively triggers a top-to-bottom script re-execution on every UI interaction. Adjusting a slider would re-trigger a full graph analysis, instantly causing an Out-Of-Memory (OOM) kill and a 502 Bad Gateway error. We resolved this using explicit `st.form` execution gates and `st.session_state` locking.
*   **Runtime Memory Pressure & Topology Bottlenecks:** The `osmnx.graph_from_polygon()` command dynamically constructs `NetworkX` graphs by parsing massive JSON responses from the Overpass API. This caused the memory footprint to instantly spike to ~320MB.
*   **The Pilot-Zone Breakthrough:** To ensure baseline rendering stability, we aggressively restricted the operational scope from the 150-ward metropolis to an 8-ward Pilot Zone, mathematically clipping the OSMnx downloads.
*   **The Precomputed GraphML Paradigm:** We permanently eliminated runtime graph generation. The system now loads a static `.graphml` file committed directly to the repository via an `@st.cache_resource` singleton, entirely neutralizing the Overpass API bottleneck.

---

## 17. Pilot-Zone Deployment Architecture

Deploying the full 150-ward Hyderabad topology was computationally unviable for a free-tier cloud instance. To achieve a memory-safe operational deployment mode without sacrificing the underlying architectural logic, we introduced the Pilot-Zone architecture.

Rather than relying on `osmnx.graph_from_place()`, the `src/city_manager.py` dynamically slices the legacy `ghmc-wards.geojson` to extract a small, central, contiguous 8-ward subset. This pilot polygon becomes the single source of truth for the entire platform. By passing the exact `unary_union` polygon coordinates directly to `osmnx.features_from_polygon()`, we bypass text-based geocoding (Nominatim) entirely, ensuring perfect alignment between the generated street graph, the clipped facilities, and the visualization layer.

---

## 18. Runtime Memory Engineering

We engineered an aggressive "Deployment Optimization Layer" to prevent Streamlit from crashing during interactive sessions. This is not a downgrade; it is a vital adaptation for constrained cloud environments.

*   **DBSCAN Amputation:** The `scikit-learn` DBSCAN clustering and subsequent Convex Hull generations were identified as secondary memory spikes. For the Railway deployment mode, DBSCAN is explicitly bypassed. 
*   **GeoDataFrame Duplication:** Deep `.copy()` operations were minimized, and forms now securely hold state to prevent duplicate DataFrame generation.
*   **Logging Diagnostics:** We injected `psutil` and `time` trackers directly into the `run_analysis()` pipeline to expose exact memory thresholds during `NetworkX` routing paths, allowing us to actively monitor the overhead.

---

## 19. Precomputed Topology Strategy

This is the most critical architectural update for deployment survivability. Real-time topology extraction from OpenStreetMap is unpredictable, latency-prone, and highly memory-intensive.

*   **Local Generation Workflow:** A dedicated `generate_pilot_graph.py` script is executed strictly on the developer's local machine. It uses the pilot polygon to download and compile the `NetworkX` walking graph.
*   **GraphML Artifacts:** The resulting `hyderabad_pilot.graphml` file is committed directly to the Git repository.
*   **Runtime Disk Loading:** In production, the `routing.py` module no longer executes `ox.graph_from_polygon()`. It instantly loads the local XML structure into memory.
*   **Singleton Caching:** Using `@st.cache_resource`, the massive graph object is held as a persistent global singleton across all Streamlit sessions, ensuring zero redundant memory allocation and achieving near-instantaneous baseline choropleth rendering.

---

## 20. Final Architecture State

The operational stack represents a mature, institutional-grade civic-tech infrastructure system:

*   **Frontend UI:** Streamlit (Form-gated, session-persistent, reactive)
*   **API Gateway:** FastAPI (Headless JSON intelligence extraction)
*   **Spatial Operations:** GeoPandas & Shapely (Polygon clipping, CRS conversion)
*   **Topology Engine:** OSMnx & NetworkX (Topological routing, ego-graph traversal)
*   **Machine Learning:** Scikit-learn (DBSCAN desert discovery, vectorized k-d trees)
*   **Topology Storage:** Precomputed `.graphml` caching
*   **Hosting:** Dockerized container architecture deployed on Railway

---

## 21. Operational Modes

The platform supports two distinct architectural modes, defined by their compute environments:

*   **Research Mode (Local Execution):** Executes the full metropolitan analysis. Supports full `scikit-learn` DBSCAN infrastructure desert discovery, complete True Greedy optimization permutations, multi-city topology generation, and dynamic Overpass API communication.
*   **Deployment Mode (Railway Hosted):** Executes the memory-safe Pilot-Zone. Relies entirely on the `@st.cache_resource` precomputed topology. DBSCAN is disabled, optimization candidates are aggressively restricted, and the UX is heavily gated behind forms to protect the server from OOM crashes.

---

## 23. Responsive UX & Mobile Stabilization Layer

Once the core algorithmic intelligence and Railway deployment layers were stabilized, the platform transitioned from a desktop-only research prototype into a publicly deployed decision-support tool. This shift necessitated robust cross-device usability, as civic stakeholders frequently access intelligence dashboards directly from mobile devices.

Deploying Streamlit and Folium for mobile browsers introduced several critical UI challenges:
*   **Streamlit Sidebar Overflow:** The deep configuration controls and form-gated elements stacked awkwardly, leading to horizontal overflow and extreme scrolling fatigue.
*   **Folium Scroll-Traps:** A standard 700px Folium iframe on a mobile screen consumes 100% of the viewport, trapping the user in map zoom gestures and preventing vertical page scrolling.
*   **Typography Scaling:** Desktop-calibrated titles (`2.75rem`) and metric indicators broke layout boundaries on smaller screens.
*   **Visibility Constraints:** Crucial dark-mode control labels (checkboxes, select boxes, toggles) lacked the high-contrast legibility required for outdoor mobile usage.

To solve this without jeopardizing the hard-won memory safety of the Railway infrastructure, we engineered a **Deployment-Safe CSS Injection Philosophy**. Rather than introducing heavy JavaScript frontend frameworks (e.g., React/Vue) which would fracture the monolithic Streamlit architecture and drastically increase server-side processing overhead, we implemented a lightweight, pure-CSS media-query strategy (`@media (max-width: 768px)`).

*   **Intelligent Viewport Scaling:** Typography and metric cards scale down dynamically, and horizontal overflow bounds are aggressively restricted.
*   **Map Height Reduction:** The Folium canvas is explicitly constrained to `500px` on mobile layouts, ensuring sufficient viewport padding exists above and below the iframe for safe vertical touch-scrolling.
*   **Touch-Friendly UX:** The sidebar collapse mechanics were re-enabled for mobile, expander padding was compressed, and button hit-targets were expanded to `3rem` to support thumb interactions.
*   **High-Contrast Dark Mode:** Injected specific high-contrast white `#FFFFFF` overrides for all functional UI labels to ensure perfect readability.

This responsive stabilization layer acts as a perfect complement to the deployment architecture: it transforms the platform into a modern, production-grade web application entirely on the client-side browser, requiring absolutely zero additional compute overhead from the constrained Railway server.

---

## 24. Final System Status

The **Accessibility Gap Analyzer** is officially:
*   **Live-Deployed**
*   **Topology-Aware**
*   **Memory-Stabilized**
*   **Mobile-Responsive**
*   **Cross-Device Deployment Ready**
*   **Railway-Operational**
*   **Institution-Ready**
