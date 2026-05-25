import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import uuid

# Import our custom modules
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
    """Caches the dynamic loading of the GeoJSON boundary file."""
    return get_city_boundary(city_name)

@st.cache_data
def get_facilities(city_name):
    """Caches the OSMnx API call to fetch hospitals and schools."""
    return fetch_facilities(city_name)

@st.cache_data
def run_analysis(city_name, _zones_gdf, _hospitals_gdf, _schools_gdf):
    """Caches the heavy network routing and ML clustering calculations."""
    zones_with_distances = calculate_network_distances(city_name, _zones_gdf, _hospitals_gdf, _schools_gdf)
    scored_zones = calculate_gap_score(zones_with_distances)
    
    # Run Phase 2.5 ML Clustering
    clustered_zones = cluster_underserved_zones(scored_zones, score_threshold=60.0)
    cluster_hulls = generate_cluster_hulls(clustered_zones)
    
    return clustered_zones, cluster_hulls

# ----------------------------------------

def inject_custom_css():
    """Injects custom CSS to style the app as a premium dark civic-tech dashboard."""
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #2D3748; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        [data-testid="stToolbar"] { visibility: hidden !important; }
        [data-testid="stSidebarCollapseButton"] { display: none !important; }
        .hero-title { font-size: 2.75rem; font-weight: 800; margin-bottom: 0.5rem; color: #FFFFFF; font-family: 'Inter', sans-serif; letter-spacing: -0.02em; }
        .hero-subtitle { font-size: 1.1rem; color: #A0AEC0; margin-bottom: 2rem; font-family: 'Inter', sans-serif; max-width: 800px; }
        .status-badge { background-color: rgba(72, 187, 120, 0.15); color: #48BB78; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; display: inline-block; margin-bottom: 1rem; border: 1px solid rgba(72, 187, 120, 0.3); }
        div[data-testid="stMetric"] { background-color: #1A202C; border: 1px solid #2D3748; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease; }
        div[data-testid="stMetric"]:hover { transform: translateY(-2px); }
        div[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; color: #FFFFFF; }
        div[data-testid="stMetricLabel"] { color: #A0AEC0; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 0.5rem; }
        .map-section-header { font-size: 1.5rem; font-weight: 600; margin-top: 3rem; margin-bottom: 1.5rem; color: #E2E8F0; border-bottom: 1px solid #2D3748; padding-bottom: 0.75rem; }
        .stSpinner > div > div { border-top-color: #48BB78 !important; }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Accessibility Gap Analyzer", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
    
    if 'last_clicked_coords' not in st.session_state: st.session_state.last_clicked_coords = None
    if 'recommendations' not in st.session_state: st.session_state.recommendations = None
    if 'session_id' not in st.session_state: st.session_state.session_id = str(uuid.uuid4())[:8]
    
    inject_custom_css()
    
    # --- Sidebar Controls ---
    with st.sidebar:
        st.markdown('<div class="hero-title" style="font-size: 1.8rem; margin-bottom: 1rem;">Controls</div>', unsafe_allow_html=True)
        
        st.subheader("Global Region")
        city_name = st.selectbox("Select Active City", options=SUPPORTED_CITIES, index=0, help="Dynamically switches urban topologies.")
        
        with st.expander("🗺️ Map Layers & Filters", expanded=True):
            show_hospitals = st.checkbox("Show Hospitals", value=True)
            show_schools = st.checkbox("Show Schools", value=True)
            min_gap_score = st.slider("Minimum Gap Score", min_value=0, max_value=100, value=0, step=5)
            search_ward = st.text_input("Search ward by name", placeholder="e.g. Khairatabad")

        with st.expander("⚡ Phase 3A: Intervention Simulation", expanded=False):
            simulation_mode = st.toggle("Enable Simulation Mode", value=False)
            if simulation_mode:
                sim_facility_type = st.selectbox("Facility to Inject", options=["hospital", "school"], key="sim_sel")
                st.info("Click anywhere on the map to inject the facility.")
            else:
                st.session_state.last_clicked_coords = None
                
        with st.expander("🧠 Phase 3B: Auto-Suggest Engine", expanded=False):
            auto_suggest_mode = st.toggle("Enable Auto-Suggest", value=False)
            if auto_suggest_mode:
                opt_facility_type = st.selectbox("Facility to Optimize", options=["hospital", "school"], key="opt_sel")
                opt_count = st.slider("Number of Interventions", min_value=1, max_value=5, value=3)
                run_optimization = st.button("Run Optimization Engine")
            else:
                st.session_state.recommendations = None
                run_optimization = False
                
        with st.expander("🚶 Phase 3C: Coverage Intelligence", expanded=False):
            coverage_mode = st.toggle("Enable Isochrones", value=False, help="Render true walkable service areas for active simulated/optimized interventions.")
            
        with st.expander("📄 Phase 3D: Export & Session", expanded=False):
            st.caption(f"Active Session: `{st.session_state.session_id}`")
            generate_report = st.button("Generate Operational Report")

    # --- Hero Section ---
    st.markdown('<div class="status-badge">● LIVE OSM DATA</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Accessibility Gap Analyzer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-subtitle">Identifying urban areas with poor access to essential facilities using network routing and spatial ML in <b>{city_name}</b>.</div>', unsafe_allow_html=True)

    # 2. Load Data
    try:
        with st.spinner(f"Loading boundary topology for {city_name}..."):
            zones_gdf = get_boundaries(city_name)
    except Exception as e:
        st.error(f"Could not load boundary topology. Error: {e}")
        st.stop()

    try:
        with st.spinner(f"Fetching network facilities for {city_name}..."):
            hospitals_gdf, schools_gdf = get_facilities(city_name)
    except Exception as e:
        st.error(f"Could not fetch facility data. Error: {e}")
        st.stop()

    # 3. Run Core Analytics
    with st.spinner("Computing network routing and regional intelligence..."):
        scored_zones, cluster_hulls = run_analysis(city_name, zones_gdf, hospitals_gdf, schools_gdf)

    # Handle Optimization Logic before mapping
    if auto_suggest_mode and run_optimization:
        with st.spinner("Running P-Median Optimization... (Evaluating critical topology)"):
            from src.optimization_engine import find_optimal_locations
            recs = find_optimal_locations(city_name, scored_zones, hospitals_gdf, schools_gdf, n=opt_count, facility_type=opt_facility_type)
            st.session_state.recommendations = recs
            if recs:
                st.toast("✅ Optimization complete! Top recommendations generated.", icon="🧠")
                save_session(st.session_state.session_id, {"city": city_name, "recommendations": recs})
            else:
                st.warning("No valid interventions found to improve the current map state.")

    # Apply Dynamic Filters
    filtered_zones = scored_zones.copy()
    if min_gap_score > 0:
        filtered_zones = filtered_zones[filtered_zones['gap_score'] >= min_gap_score]
    if search_ward.strip():
        if 'name' in filtered_zones.columns:
            filtered_zones = filtered_zones[filtered_zones['name'].str.contains(search_ward.strip(), case=False, na=False)]
            
    display_hospitals = hospitals_gdf if show_hospitals else hospitals_gdf.iloc[0:0]
    display_schools = schools_gdf if show_schools else schools_gdf.iloc[0:0]

    # --- Phase 3C: Coverage Intelligence Generation ---
    isochrones_list = []
    if coverage_mode:
        from src.coverage_engine import generate_isochrones
        if simulation_mode and st.session_state.last_clicked_coords:
            lat, lon = st.session_state.last_clicked_coords
            with st.spinner("Generating topology-aware walksheds for simulation..."):
                isochrones_list.append(generate_isochrones(city_name, lat, lon))
        elif auto_suggest_mode and st.session_state.recommendations:
            with st.spinner("Generating topology-aware walksheds for AI recommendations..."):
                for rec in st.session_state.recommendations:
                    isochrones_list.append(generate_isochrones(city_name, rec['lat'], rec['lon']))
                    
    final_isochrones = pd.concat(isochrones_list, ignore_index=True) if isochrones_list else None

    # --- Phase 3D: Report Generation ---
    if generate_report:
        with st.spinner("Compiling Civic Intelligence Report..."):
            report_dict = generate_session_report(city_name, filtered_zones, st.session_state.recommendations, final_isochrones)
            md_content = export_to_markdown(report_dict)
            st.download_button("📥 Download Report (Markdown)", data=md_content, file_name=f"Accessibility_Report_{city_name.split(',')[0]}.md", mime="text/markdown")
            st.download_button("📥 Download Raw Data (JSON)", data=json.dumps(report_dict, indent=2), file_name=f"Intelligence_{city_name.split(',')[0]}.json", mime="application/json")
            st.success("Reports generated successfully!")

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
        if simulation_mode and st.session_state.last_clicked_coords:
            lat, lon = st.session_state.last_clicked_coords
            with st.spinner(f"Injecting hypothetical facility and computing network deltas..."):
                sim_zones, sim_facility, sim_hulls = compute_delta_scores(city_name, filtered_zones, hospitals_gdf, schools_gdf, lat, lon, sim_facility_type)
                m = create_map(sim_zones, display_hospitals, display_schools, cluster_hulls_gdf=sim_hulls, simulation_mode=True, sim_facility_gdf=sim_facility, recommendations=st.session_state.recommendations, isochrones_gdf=final_isochrones)
                st.toast("✅ Simulation complete! Delta impacts rendered.", icon="⚡")
        else:
            with st.spinner("Rendering interactive map with spatial intelligence overlays..."):
                m = create_map(filtered_zones, display_hospitals, display_schools, cluster_hulls_gdf=cluster_hulls, recommendations=st.session_state.recommendations, isochrones_gdf=final_isochrones)
        
        map_data = st_folium(m, use_container_width=True, height=700, returned_objects=["last_clicked"] if simulation_mode else [])
        
        if simulation_mode and map_data and map_data.get("last_clicked"):
            lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
            if st.session_state.last_clicked_coords != (lat, lon):
                st.session_state.last_clicked_coords = (lat, lon)
                st.rerun()

if __name__ == "__main__":
    main()
