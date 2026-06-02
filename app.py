import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import uuid
import logging

# Configure logging for memory-heavy ops
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import custom modules
from src.data_ingestion import fetch_facilities
from src.analysis_engine import calculate_network_distances, calculate_gap_score
from src.visualization import create_map
from src.ml_engine import cluster_underserved_zones, generate_cluster_hulls
from src.simulation_engine import compute_delta_scores

# Phase 3D Platform Modules
from src.city_manager import get_city_boundary, SUPPORTED_CITIES
from src.report_engine import generate_session_report, export_to_markdown
from src.session_manager import save_session

# --- Cached Functions for Performance ---

@st.cache_data
def get_boundaries(city_name):
    logger.info(f"Loading boundaries for {city_name}")
    return get_city_boundary(city_name)

@st.cache_data
def get_facilities(city_name):
    logger.info(f"Fetching facilities for {city_name}")
    return fetch_facilities(city_name)

@st.cache_data
def run_analysis(city_name, _zones_gdf, _hospitals_gdf, _schools_gdf):
    import time
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    start_time = time.time()
    logger.info(f"[MEM: {process.memory_info().rss / 1024 / 1024:.2f} MB] Executing heavy network analysis...")
    
    zones_with_distances = calculate_network_distances(city_name, _zones_gdf, _hospitals_gdf, _schools_gdf)
    logger.info(f"[MEM: {process.memory_info().rss / 1024 / 1024:.2f} MB] Routing completed in {time.time() - start_time:.2f}s")
    
    scored_zones = calculate_gap_score(zones_with_distances)
    
    # TEMPORARY RAILWAY DEPLOYMENT OVERRIDE: Disable DBSCAN entirely
    logger.info("Railway Override: Skipping DBSCAN clustering and convex hull generation to prevent OOM crash.")
    clustered_zones = scored_zones.copy()
    # Add a dummy cluster_id column so mapping doesn't break if it expects one
    if 'cluster_id' not in clustered_zones.columns:
        clustered_zones['cluster_id'] = -1
    cluster_hulls = None
    
    logger.info(f"[MEM: {process.memory_info().rss / 1024 / 1024:.2f} MB] Analysis pipeline finalized.")
    return clustered_zones, cluster_hulls

# ----------------------------------------

def inject_custom_css():
    st.markdown("""
        <style>
        /* Base Theme */
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #2D3748; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        [data-testid="stToolbar"] { visibility: hidden !important; }
        [data-testid="stSidebarCollapseButton"] { display: none !important; }
        
        /* Typography */
        .hero-title { font-size: 2.75rem; font-weight: 800; margin-bottom: 0.5rem; color: #FFFFFF; font-family: 'Inter', sans-serif; letter-spacing: -0.02em; }
        .hero-subtitle { font-size: 1.1rem; color: #A0AEC0; margin-bottom: 2rem; font-family: 'Inter', sans-serif; max-width: 800px; }
        .status-badge { background-color: rgba(72, 187, 120, 0.15); color: #48BB78; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; display: inline-block; margin-bottom: 1rem; border: 1px solid rgba(72, 187, 120, 0.3); }
        
        /* Metric Cards */
        div[data-testid="stMetric"] { background-color: #1A202C; border: 1px solid #2D3748; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease; }
        div[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; color: #FFFFFF; }
        div[data-testid="stMetricLabel"] { color: #A0AEC0; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 0.5rem; }
        
        /* Map Section */
        .map-section-header { font-size: 1.5rem; font-weight: 600; margin-top: 3rem; margin-bottom: 1.5rem; color: #E2E8F0; border-bottom: 1px solid #2D3748; padding-bottom: 0.75rem; }
        .stSpinner > div > div { border-top-color: #48BB78 !important; }

        /* High-Contrast UI for Dark Mode Controls */
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stWidgetLabel p,
        [data-testid="stSidebar"] .stCheckbox p,
        [data-testid="stSidebar"] .stToggle p {
            color: #F7FAFC !important;
            font-weight: 500 !important;
        }
        div[data-testid="stExpander"] details summary p {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* --- MOBILE RESPONSIVE ENGINEERING --- */
        @media (max-width: 768px) {
            /* 1. Layout Engineering: Fix horizontal overflow and excess padding */
            .block-container { padding-top: 1.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100vw !important; overflow-x: hidden; }
            
            /* 2. Typography Scaling: Reduce oversized headings */
            .hero-title { font-size: 1.8rem; }
            .hero-subtitle { font-size: 0.95rem; margin-bottom: 1.5rem; }
            .map-section-header { font-size: 1.25rem; margin-top: 2rem; margin-bottom: 1rem; }
            
            /* 3. Metric Cards: Compress for stacking */
            div[data-testid="stMetric"] { padding: 1rem; margin-bottom: 0.5rem; }
            div[data-testid="stMetricValue"] { font-size: 1.75rem; }
            
            /* 4. Sidebar UX: Touch-friendly buttons and condensed expanders */
            [data-testid="stSidebar"] { min-width: 100vw !important; } /* Full width sidebar on mobile */
            [data-testid="stSidebarCollapseButton"] { display: flex !important; } /* Re-enable collapse specifically for mobile to free viewport */
            .stButton > button { min-height: 3rem; font-weight: 600; margin-top: 0.25rem; } /* Touch targets */
            div[data-testid="stExpander"] details summary { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
            
            /* Prevent sliders and toggles from clipping */
            .stSlider { padding-bottom: 0.5rem; }
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Accessibility Gap Analyzer", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
    
    # --- Session State Initialization ---
    if 'last_clicked_coords' not in st.session_state: st.session_state.last_clicked_coords = None
    if 'recommendations' not in st.session_state: st.session_state.recommendations = None
    if 'session_id' not in st.session_state: st.session_state.session_id = str(uuid.uuid4())[:8]
    
    # LAZY LOADING GATE
    if 'baseline_run' not in st.session_state: st.session_state.baseline_run = False
    
    inject_custom_css()
    
    # --- Sidebar Controls ---
    with st.sidebar:
        st.markdown('<div class="hero-title" style="font-size: 1.8rem; margin-bottom: 1rem;">Controls</div>', unsafe_allow_html=True)
        
        st.subheader("Global Region")
        city_name = st.selectbox("Select Active City", options=SUPPORTED_CITIES, index=0)
        
        # Explicit Execution Gate
        if st.button("🚀 Load Data & Run Baseline", use_container_width=True):
            st.session_state.baseline_run = True
            st.session_state.recommendations = None
            st.session_state.last_clicked_coords = None
            
        st.markdown("---")
        
        # Rerun Protected Filters (Forms)
        with st.expander("🗺️ Map Layers & Filters", expanded=False):
            with st.form("filter_form"):
                show_hospitals = st.checkbox("Show Hospitals", value=True)
                show_schools = st.checkbox("Show Schools", value=True)
                min_gap_score = st.slider("Minimum Gap Score", min_value=0, max_value=100, value=0, step=5)
                search_ward = st.text_input("Search ward by name", placeholder="e.g. Khairatabad")
                apply_filters = st.form_submit_button("Apply Filters")

        with st.expander("⚡ Phase 3A: Intervention Simulation", expanded=False):
            with st.form("simulation_form"):
                simulation_mode = st.toggle("Enable Simulation Mode", value=False)
                sim_facility_type = st.selectbox("Facility to Inject", options=["hospital", "school"])
                sim_submit = st.form_submit_button("Apply Simulation State")
                
            if simulation_mode:
                st.info("Click anywhere on the map to inject the facility.")
            else:
                st.session_state.last_clicked_coords = None
                
        with st.expander("🧠 Phase 3B: Auto-Suggest Engine", expanded=False):
            auto_suggest_mode = st.toggle("Enable Auto-Suggest", value=False)
            if auto_suggest_mode:
                with st.form("optimize_form"):
                    opt_facility_type = st.selectbox("Facility to Optimize", options=["hospital", "school"])
                    opt_count = st.slider("Number of Interventions", min_value=1, max_value=2, value=1)
                    run_optimization = st.form_submit_button("Run Optimization Engine")
            else:
                st.session_state.recommendations = None
                run_optimization = False
                
        with st.expander("🚶 Phase 3C: Coverage Intelligence", expanded=False):
            with st.form("coverage_form"):
                coverage_mode = st.toggle("Enable Isochrones", value=False, help="Render true walkable service areas.")
                cov_submit = st.form_submit_button("Apply Coverage Layer")
            
        with st.expander("📄 Phase 3D: Export & Session", expanded=False):
            st.caption(f"Active Session: `{st.session_state.session_id}`")
            generate_report = st.button("Generate Operational Report")

    # --- Hero Section ---
    st.markdown('<div class="status-badge">● LIVE OSM DATA</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Accessibility Gap Analyzer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-subtitle">Identifying urban areas with poor access to essential facilities using network routing and spatial ML in <b>{city_name}</b>.</div>', unsafe_allow_html=True)

    # 1. LAZY LOADING BLOCK
    if not st.session_state.baseline_run:
        st.info("👋 Welcome to the Accessibility Gap Analyzer! Please select a city and click **'Load Data & Run Baseline'** in the sidebar to securely load the topological routing models.")
        st.stop()

    # 2. Load Data (Now safely gated behind baseline_run)
    try:
        zones_gdf = get_boundaries(city_name)
    except Exception as e:
        logger.error(f"Boundary Error: {e}")
        st.error("Could not load boundary topology.")
        st.stop()

    try:
        hospitals_gdf, schools_gdf = get_facilities(city_name)
    except Exception as e:
        logger.error(f"Facility Error: {e}")
        st.error("Could not fetch facility data.")
        st.stop()

    # 3. Run Core Analytics
    scored_zones, cluster_hulls = run_analysis(city_name, zones_gdf, hospitals_gdf, schools_gdf)

    # Handle Optimization Logic (State Protected so it doesn't re-run on map click)
    if auto_suggest_mode and run_optimization:
        logger.info("Starting Auto-Suggest P-Median execution.")
        with st.spinner("Running P-Median Optimization..."):
            from src.optimization_engine import find_optimal_locations
            recs = find_optimal_locations(city_name, scored_zones, hospitals_gdf, schools_gdf, n=opt_count, facility_type=opt_facility_type)
            st.session_state.recommendations = recs
            if recs:
                st.toast("✅ Optimization complete! Recommendations stored safely.", icon="🧠")
                save_session(st.session_state.session_id, {"city": city_name, "recommendations": recs})
            else:
                st.warning("No valid interventions found.")

    # Apply Form-Based Filters safely
    filtered_zones = scored_zones.copy()
    
    # Setup default state variables safely
    _min_gap = min_gap_score if 'min_gap_score' in locals() else 0
    _search = search_ward.strip() if 'search_ward' in locals() else ""
    _show_h = show_hospitals if 'show_hospitals' in locals() else True
    _show_s = show_schools if 'show_schools' in locals() else True
    _sim_mod = simulation_mode if 'simulation_mode' in locals() else False
    _sim_type = sim_facility_type if 'sim_facility_type' in locals() else "hospital"
    _cov_mod = coverage_mode if 'coverage_mode' in locals() else False

    if _min_gap > 0:
        filtered_zones = filtered_zones[filtered_zones['gap_score'] >= _min_gap]
    if _search:
        if 'name' in filtered_zones.columns:
            filtered_zones = filtered_zones[filtered_zones['name'].str.contains(_search, case=False, na=False)]
            
    display_hospitals = hospitals_gdf if _show_h else hospitals_gdf.iloc[0:0]
    display_schools = schools_gdf if _show_s else schools_gdf.iloc[0:0]
    
    # --- Phase 3C: Coverage Intelligence ---
    isochrones_list = []
    if _cov_mod:
        logger.info("Generating Isochrones...")
        from src.coverage_engine import generate_isochrones
        if _sim_mod and st.session_state.last_clicked_coords:
            lat, lon = st.session_state.last_clicked_coords
            with st.spinner("Generating walksheds for simulation..."):
                isochrones_list.append(generate_isochrones(city_name, lat, lon))
        elif auto_suggest_mode and st.session_state.recommendations:
            with st.spinner("Generating walksheds for top AI recommendation (memory protected)..."):
                # Restrict memory overhead by only generating coverage for the #1 ranked recommendation
                for rec in st.session_state.recommendations[:1]:
                    isochrones_list.append(generate_isochrones(city_name, rec['lat'], rec['lon']))
                    
    final_isochrones = pd.concat(isochrones_list, ignore_index=True) if isochrones_list else None

    # --- Phase 3D: Report Generation ---
    if 'generate_report' in locals() and generate_report:
        import json
        logger.info("Generating Session Report.")
        with st.spinner("Compiling Civic Intelligence Report..."):
            report_dict = generate_session_report(city_name, filtered_zones, st.session_state.recommendations, final_isochrones)
            md_content = export_to_markdown(report_dict)
            st.download_button("📥 Download Report (Markdown)", data=md_content, file_name=f"Accessibility_Report_{city_name.split(',')[0]}.md", mime="text/markdown")
            st.download_button("📥 Download Raw Data (JSON)", data=json.dumps(report_dict, indent=2), file_name=f"Intelligence_{city_name.split(',')[0]}.json", mime="application/json")

    # --- Metrics Section ---
    total_wards = len(filtered_zones)
    critical_zones = len(filtered_zones[filtered_zones['gap_category'] == 'Critical']) if total_wards > 0 else 0
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(label="Visible Wards", value=f"{total_wards:,}")
    with col2: st.metric(label="Critical Zones", value=f"{critical_zones:,}")
    with col3: st.metric(label="Hospitals Displayed", value=f"{len(display_hospitals):,}")
    with col4: st.metric(label="Schools Displayed", value=f"{len(display_schools):,}")

    # --- Map Rendering ---
    st.markdown('<div class="map-section-header">Spatial Analysis View</div>', unsafe_allow_html=True)
    
    if filtered_zones.empty:
        st.warning("No zones match the current filter criteria.")
    else:
        if _sim_mod and st.session_state.last_clicked_coords:
            lat, lon = st.session_state.last_clicked_coords
            logger.info("Computing Delta Scores for Simulation.")
            with st.spinner("Computing network deltas..."):
                sim_zones, sim_facility, sim_hulls = compute_delta_scores(city_name, filtered_zones, hospitals_gdf, schools_gdf, lat, lon, _sim_type)
                m = create_map(sim_zones, display_hospitals, display_schools, cluster_hulls_gdf=sim_hulls, simulation_mode=True, sim_facility_gdf=sim_facility, recommendations=st.session_state.recommendations, isochrones_gdf=final_isochrones)
        else:
            logger.info("Rendering Baseline Map.")
            with st.spinner("Rendering map..."):
                m = create_map(filtered_zones, display_hospitals, display_schools, cluster_hulls_gdf=cluster_hulls, recommendations=st.session_state.recommendations, isochrones_gdf=final_isochrones)
        
        # Reduced height to 500 to prevent scroll-trapping on mobile devices while maintaining visual quality
        map_data = st_folium(m, use_container_width=True, height=500, returned_objects=["last_clicked"] if _sim_mod else [])
        
        if _sim_mod and map_data and map_data.get("last_clicked"):
            lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
            if st.session_state.last_clicked_coords != (lat, lon):
                st.session_state.last_clicked_coords = (lat, lon)
                st.rerun()

if __name__ == "__main__":
    main()
