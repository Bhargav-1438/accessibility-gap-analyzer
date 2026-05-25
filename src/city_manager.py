import os
import geopandas as gpd
import osmnx as ox

# Ensure necessary directories exist
os.makedirs("data/boundaries", exist_ok=True)
os.makedirs("data/graphs", exist_ok=True)

# Temporarily restricted to Pilot Zone for Railway free-tier runtime stability
SUPPORTED_CITIES = [
    "Hyderabad Pilot Zone"
]

def get_city_slug(city_name: str) -> str:
    return city_name.lower().replace(", ", "_").replace(" ", "_")

def get_city_boundary(city_name: str) -> gpd.GeoDataFrame:
    """
    Retrieves city boundaries.
    1. Checks local cache (data/boundaries/{city_slug}.geojson)
    2. If missing, dynamically downloads via OSMnx and caches it.
    """
    city_slug = get_city_slug(city_name)
    filepath = f"data/boundaries/{city_slug}.geojson"
    
    # Generate Pilot Zone from legacy ghmc-wards to strictly limit execution size
    if city_name == "Hyderabad Pilot Zone" and not os.path.exists(filepath):
        legacy_hyd_file = "data/boundaries/ghmc-wards.geojson"
        if os.path.exists(legacy_hyd_file):
            print("Slicing GHMC wards to create lightweight Pilot Zone...")
            gdf = gpd.read_file(legacy_hyd_file)
            # Take a small central contiguous slice (e.g., 8 wards) for stable Railway execution
            pilot_gdf = gdf.head(8).copy()
            pilot_gdf.to_file(filepath, driver="GeoJSON")
            return pilot_gdf
    
    if os.path.exists(filepath):
        try:
            return gpd.read_file(filepath)
        except Exception:
            pass # Fallback to download if file is corrupted
            
    # Dynamic Fallback: Download boundary
    print(f"Downloading dynamic boundaries for {city_name}...")
    try:
        # We use geocode_to_gdf as the safest fallback. 
        # Note: Depending on the city, this may return a single polygon or multipolygon.
        gdf = ox.geocode_to_gdf(city_name)
        
        # Ensure it has a 'name' column for the dashboard tooltips
        if 'display_name' in gdf.columns and 'name' not in gdf.columns:
            gdf['name'] = gdf['display_name']
        elif 'name' not in gdf.columns:
            gdf['name'] = city_name
            
        # Clean up column types for GeoJSON serialization (drop lists/dicts returned by OSMnx)
        for col in gdf.columns:
            if gdf[col].apply(lambda x: isinstance(x, (list, dict))).any():
                gdf[col] = gdf[col].astype(str)
                
        gdf.to_file(filepath, driver="GeoJSON")
        return gdf
    except Exception as e:
        raise ValueError(f"Could not download boundaries for {city_name}. Error: {e}")
