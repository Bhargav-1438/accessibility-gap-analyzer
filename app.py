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
def run_analysis(zones_gdf, hospitals_gdf, schools_gdf):
    """Caches the heavy geometric calculations for distances and scores."""
    zones_with_distances = calculate_nearest_distances(zones_gdf, hospitals_gdf, schools_gdf)
    return calculate_gap_score(zones_with_distances)

# ----------------------------------------

def main():
    # 1. Set the page title and basic configuration
    st.set_page_config(page_title="Accessibility Gap Analyzer", layout="wide")
    st.title("Accessibility Gap Analyzer")
    
    st.info("Loading geospatial data and calculating accessibility scores...")

    # 2. Load city boundary file (using a temporary sample path)
    boundary_file = "data/boundaries/ghmc-wards.geojson"
    try:
        zones_gdf = get_boundaries(boundary_file)
    except Exception as e:
        st.error(f"Could not load boundary file. Please ensure '{boundary_file}' exists. Error: {e}")
        st.stop()

    # 3. Fetch hospitals and schools from OpenStreetMap
    city_name = "Hyderabad, India"
    hospitals_gdf, schools_gdf = get_facilities(city_name)

    # 4. Run the Analysis Engine (now heavily cached)
    scored_zones = run_analysis(zones_gdf, hospitals_gdf, schools_gdf)

    # 5. Generate the visual Map
    m = create_map(scored_zones, hospitals_gdf, schools_gdf)

    # 6. Render the Map in Streamlit
    st.subheader(f"Accessibility Map: {city_name}")
    # st_folium renders the folium map object directly into the Streamlit web interface
    st_folium(m, width=1200, height=700)

if __name__ == "__main__":
    main()
