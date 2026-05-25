# Accessibility Gap Analyzer

**Urban Accessibility Intelligence & Decision-Support Infrastructure**

[![Railway](https://img.shields.io/badge/Railway-Deployed-0B0D0E?style=flat&logo=railway)](https://railway.app)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=flat&logo=streamlit)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![OSMnx](https://img.shields.io/badge/OSMnx-Network_Routing-green?style=flat)]()

## 2. Platform Overview
Urban infrastructure is rarely distributed equally. Systemic accessibility inequality results in entire neighborhoods facing critical barriers to essential services like healthcare and education. While traditional GIS systems excel at visualizing static data, they often fail to model real-world topology or offer actionable intelligence for intervention.

The Accessibility Gap Analyzer is a topology-aware urban accessibility intelligence and intervention planning system. Moving beyond geometric proximity approximations, the platform models real pedestrian networks, autonomously discovers systemic infrastructure deserts, and serves as an interactive decision-support infrastructure. It empowers urban planners and municipal agencies not only to identify *where* the problems are, but to mathematically optimize *how* to solve them.

## 3. Key Features
- **Network-Based Accessibility Scoring:** Replaces flawed Euclidean distance with true walkable street topology routing.
- **Interactive Intervention Simulation:** Planners can inject hypothetical facilities into the graph and visualize real-time delta impact scores.
- **Automated Optimization Engine:** A p-median inspired True Greedy search algorithm identifies the absolute highest-impact facility placement locations to structurally reduce urban accessibility inequality.
- **Isochrone Coverage Intelligence:** Network-constrained convex hull walksheds model real-world service boundaries.
- **Spatial Machine Learning:** Autonomous multi-ward DBSCAN clustering identifies hidden infrastructure deserts.
- **Decoupled API Architecture:** The intelligence engine is accessible headlessly via FastAPI.
- **Pilot-Zone Deployment Architecture:** Optimized for stable, memory-safe execution on free-tier cloud infrastructure via precomputed GraphML caching.

## 4. Engineering Evolution Timeline
The platform was built through a rigorous, phased engineering evolution:
- **Phase 1 (Euclidean Model):** Established baseline data ingestion and scoring via straight-line geometric proximity.
- **Phase 2 (Topology-Aware Routing):** Replaced Euclidean logic with OSMnx and NetworkX to navigate physical pedestrian barriers.
- **Phase 2.5 (Spatial Intelligence):** Implemented DBSCAN to elevate analysis from single wards to regional infrastructure deserts.
- **Phase 3A (Simulation):** Engineered in-memory graph mutation to simulate interventions safely and recalculate spatial impact deltas.
- **Phase 3B (Optimization):** Deployed a True Greedy AI reasoning engine to rank optimal facility placements.
- **Phase 3C (Coverage Intelligence):** Transitioned from point markers to polygon walksheds via ego-graph traversal.
- **Phase 3D (Platformization):** Hardened the architecture into a multi-city, API-accessible, Dockerized infrastructure.

## 5. System Architecture
The platform is built on a strict, decoupled layer architecture:
- `api/main.py`: Headless FastAPI REST gateway.
- `app.py`: Streamlit-based interactive planner dashboard.
- `src/routing.py`: OSMnx graph ingestion, caching, and shortest-path calculation.
- `src/analysis_engine.py`: Distance normalization and topological gap scoring.
- `src/ml_engine.py`: Scikit-learn DBSCAN clustering and convex hull generation.
- `src/simulation_engine.py`: Safe in-memory graph mutation and delta scoring.
- `src/optimization_engine.py`: True Greedy p-median iteration and human-readable reasoning generation.
- `src/coverage_engine.py`: Ego-graph walkshed traversal and polygon simplification.

## 6. Deployment Engineering Challenges
Transitioning this platform from a local prototype to a production-stable cloud deployment presented severe engineering challenges, primarily concerning memory exhaustion (OOM) on Railway's 500MB free tier.
- **Streamlit Rerender Architecture:** Streamlit's reactive architecture triggered full script top-to-bottom re-execution on every sidebar interaction. We solved this by locking all analysis behind explicit `st.form` submissions and strict lazy-loading states, ensuring the server idles safely.
- **Runtime Graph Generation Spikes:** `osmnx.graph_from_polygon` parses massive JSON responses and allocates massive `MultiDiGraph` objects dynamically, spiking memory to ~320MB and causing immediate Railway termination.
- **The Precomputed GraphML Breakthrough:** We completely eliminated runtime OSM generation. The deployment architecture now relies on statically executing `generate_pilot_graph.py` locally, committing the `hyderabad_pilot.graphml` to the repository, and using `@st.cache_resource` to load the graph as an immutable memory singleton. 
- **Pilot-Zone Constraints:** To maintain stability, we aggressively throttled the deployment to an 8-ward Pilot Zone, disabled DBSCAN clustering during baseline load, and restricted optimization candidate permutations.

## 7. Screenshots
*(Placeholder for Baseline Choropleth)*  
*(Placeholder for Intervention Simulation)*  
*(Placeholder for Optimization Recommendations)*  
*(Placeholder for Isochrone Coverage Intelligence)*  
*(Placeholder for Deployment Architecture)*

## 8. Tech Stack
- **Backend & API:** Python 3.11, FastAPI, Uvicorn, Pydantic
- **Frontend UI:** Streamlit, Streamlit-Folium
- **Geospatial & Routing:** GeoPandas, Shapely, OSMnx, NetworkX, Folium
- **Data & ML:** Pandas, NumPy, Scikit-learn
- **Infrastructure:** Docker, Docker Compose, Railway

## 9. Local Setup
```bash
# 1. Clone the repository
git clone https://github.com/Bhargav-1438/accessibility-gap-analyzer.git
cd accessibility-gap-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate static pilot graph (Required for stable deployment)
python generate_pilot_graph.py

# 4. Run the API Gateway
uvicorn api.main:app --reload --port 8000

# 5. Run the Planner Dashboard
streamlit run app.py
```

## 10. Railway Deployment
This repository is optimized for one-click deployment on Railway.
- **Docker Architecture:** Uses a Python 3.11 slim image. The `docker-compose.yml` orchestrates the `api` and `dashboard` services.
- **Precomputed Strategy:** The `data/graphs/hyderabad_pilot.graphml` file must be tracked in Git. The deployment bypasses all runtime Overpass API communication, booting instantly from the local cache.

## 11. Future Scope
- **GTFS Integration:** Fusing public transit schedules into the routing graph.
- **WorldPop Weighting:** Integrating highly granular block-level population density for vulnerability-weighted gap scoring.
- **Municipal Policy Scenario Modeling:** Optimizing placements based on specific government land availability and budget constraints.
- **Cloud-Native Scaling:** Moving the `.graphml` caching layer to an AWS S3/Redis architecture to support simultaneous nationwide processing.

## 12. License
This project is licensed under the MIT License.
