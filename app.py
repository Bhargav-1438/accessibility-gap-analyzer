import streamlit as st
from streamlit_folium import st_folium

# Import our custom modules
from src.data_ingestion import load_city_boundaries, fetch_facilities
from src.analysis_engine import calculate_nearest_distances, calculate_gap_score
from src.visualization import create_map

# --- Cached Functions for Performance ---

@st.cache_data
def get_boundaries(file_path):
    """Caches the loading of the GeoJSON boundary file."""
    return load_city_boundaries(file_path)

@st.cache_data
def get_facilities(city_name):
    """Caches the OSMnx API call to fetch hospitals and schools."""
    return fetch_facilities(city_name)

@st.cache_data
def run_analysis(_zones_gdf, _hospitals_gdf, _schools_gdf):
    """Caches the heavy geometric calculations for distances and scores."""
    zones_with_distances = calculate_nearest_distances(_zones_gdf, _hospitals_gdf, _schools_gdf)
    return calculate_gap_score(zones_with_distances)

# ----------------------------------------

def inject_custom_css():
    """Injects custom CSS to style the app as a premium dark civic-tech dashboard."""
    st.markdown("""
        <style>
        /* Main background and text */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* Sidebar styling overrides */
        [data-testid="stSidebar"] {
            background-color: #161B22;
            border-right: 1px solid #2D3748;
        }
        
        /* Hide Streamlit branding for a cleaner app feel */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Ensure the native Streamlit header stays visible but integrates seamlessly with our dark theme */
        header {
            background-color: #0E1117 !important;
        }
        
        /* Hide the top-right toolbar (Deploy/GitHub icons) to maintain the clean look */
        [data-testid="stToolbar"] {
            visibility: hidden !important;
        }
        
        /* Custom Header Styling */
        .hero-title {
            font-size: 2.75rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            color: #FFFFFF;
            font-family: 'Inter', sans-serif;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            font-size: 1.1rem;
            color: #A0AEC0;
            margin-bottom: 2rem;
            font-family: 'Inter', sans-serif;
            max-width: 800px;
        }
        .status-badge {
            background-color: rgba(72, 187, 120, 0.15);
            color: #48BB78;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 700;
            display: inline-block;
            margin-bottom: 1rem;
            border: 1px solid rgba(72, 187, 120, 0.3);
            letter-spacing: 0.05em;
        }
        
        /* Metric Card Styling overrides */
        div[data-testid="stMetric"] {
            background-color: #1A202C;
            border: 1px solid #2D3748;
            padding: 1.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
        }
        div[data-testid="stMetricValue"] {
            font-size: 2.2rem;
            font-weight: 700;
            color: #FFFFFF;
        }
        div[data-testid="stMetricLabel"] {
            color: #A0AEC0;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        /* Map Container tweaks */
        .map-section-header {
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 3rem;
            margin-bottom: 1.5rem;
            color: #E2E8F0;
            border-bottom: 1px solid #2D3748;
            padding-bottom: 0.75rem;
        }
        
        /* Spinner styling */
        .stSpinner > div > div {
            border-top-color: #48BB78 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    # 1. Set the page layout to wide and expand sidebar by default
    st.set_page_config(page_title="Accessibility Gap Analyzer", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
    
    # Inject Custom CSS
    inject_custom_css()
    
    # --- Sidebar Controls ---
    with st.sidebar:
        st.markdown('<div class="hero-title" style="font-size: 1.8rem; margin-bottom: 1rem;">Controls</div>', unsafe_allow_html=True)
        
        st.subheader("Map Layers")
        show_hospitals = st.checkbox("Show Hospitals", value=True)
        show_schools = st.checkbox("Show Schools", value=True)
        
        st.markdown("---")
        st.subheader("Analytics Filter")
        min_gap_score = st.slider("Minimum Gap Score", min_value=0, max_value=100, value=0, step=5, 
                                  help="Hide zones with a score below this threshold.")
        
        st.markdown("---")
        st.subheader("Search")
        search_ward = st.text_input("Search ward by name", placeholder="e.g. Khairatabad", 
                                    help="Typing a name will isolate and focus the map on matching wards.")

    # --- Hero Section ---
    st.markdown('<div class="status-badge">● LIVE OSM DATA</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Accessibility Gap Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Identifying urban areas with poor access to essential healthcare and educational facilities using geospatial analysis.</div>', unsafe_allow_html=True)

    # 2. Load Data
    boundary_file = "data/boundaries/ghmc-wards.geojson"
    city_name = "Hyderabad, India"
    
    try:
        with st.spinner("Loading city boundaries..."):
            zones_gdf = get_boundaries(boundary_file)
        st.toast("✅ Boundaries loaded successfully!", icon="🌍")
    except Exception as e:
        st.error(f"Could not load boundary file. Please ensure '{boundary_file}' exists. Error: {e}")
        st.stop()

    try:
        with st.spinner(f"Fetching live facility data for {city_name}..."):
            hospitals_gdf, schools_gdf = get_facilities(city_name)
        st.toast("✅ Live facility data fetched successfully!", icon="📡")
    except Exception as e:
        st.error(f"Could not fetch facility data. Error: {e}")
        st.stop()

    # 3. Run Analysis Engine
    with st.spinner("Computing spatial accessibility scores..."):
        scored_zones = run_analysis(zones_gdf, hospitals_gdf, schools_gdf)
    st.toast("✅ Accessibility calculations complete!", icon="🧮")

    # --- Apply Dynamic Filters ---
    # We do this AFTER the cached analysis to ensure high performance
    filtered_zones = scored_zones.copy()
    
    # Apply Gap Score Filter
    if min_gap_score > 0:
        filtered_zones = filtered_zones[filtered_zones['gap_score'] >= min_gap_score]
        
    # Apply Ward Search Filter
    if search_ward.strip():
        if 'name' in filtered_zones.columns:
            # Case-insensitive search
            filtered_zones = filtered_zones[filtered_zones['name'].str.contains(search_ward.strip(), case=False, na=False)]
        else:
            st.sidebar.warning("Ward name search is not supported by the current boundary data.")

    # Apply Facility Marker Toggles
    # We pass empty DataFrames to the map engine if unchecked
    display_hospitals = hospitals_gdf if show_hospitals else hospitals_gdf.iloc[0:0]
    display_schools = schools_gdf if show_schools else schools_gdf.iloc[0:0]

    # --- Metrics Section ---
    total_wards = len(filtered_zones)
    critical_zones = len(filtered_zones[filtered_zones['gap_category'] == 'Critical']) if total_wards > 0 else 0
    total_hospitals = len(display_hospitals)
    total_schools = len(display_schools)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Visible Wards", value=f"{total_wards:,}")
    with col2:
        st.metric(label="Critical Zones", value=f"{critical_zones:,}")
    with col3:
        st.metric(label="Hospitals Displayed", value=f"{total_hospitals:,}")
    with col4:
        st.metric(label="Schools Displayed", value=f"{total_schools:,}")

    # --- Map Section ---
    st.markdown('<div class="map-section-header">Spatial Analysis View</div>', unsafe_allow_html=True)
    
    if filtered_zones.empty:
        st.warning("No zones match the current filter criteria. Please clear the search or lower the gap score filter.")
    else:
        with st.spinner("Rendering interactive map..."):
            m = create_map(filtered_zones, display_hospitals, display_schools)
            st_folium(m, use_container_width=True, height=700, returned_objects=[])
        st.toast("✅ Map rendered successfully!", icon="🗺️")

if __name__ == "__main__":
    main()
