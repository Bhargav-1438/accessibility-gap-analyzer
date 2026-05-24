import geopandas as gpd
import osmnx as ox

def load_city_boundaries(file_path: str):
    """
    Loads zone boundaries (GeoJSON/Shapefile) from a file.
    
    Args:
        file_path (str): Path to the GeoJSON or Shapefile.
        
    Returns:
        GeoDataFrame containing the city zones.
    """
    # Read the spatial file using GeoPandas
    gdf = gpd.read_file(file_path)
    
    # Print basic information as requested
    print(f"Loaded {len(gdf)} zones from {file_path}")
    print(f"Column names: {list(gdf.columns)}")
    
    return gdf

def fetch_facilities(city_name: str):
    """
    Fetches hospital and school data from OpenStreetMap.
    
    Args:
        city_name (str): Name of the city (e.g., 'Hyderabad, India')
        
    Returns:
        tuple: (hospitals_gdf, schools_gdf)
    """
    print(f"Fetching facilities for {city_name} from OpenStreetMap...")
    
    # Define OSM tags to search for
    hospital_tags = {'amenity': 'hospital'}
    school_tags = {'amenity': 'school'}
    
    # Fetch spatial data using OSMnx
    hospitals_gdf = ox.features_from_place(city_name, tags=hospital_tags)
    schools_gdf = ox.features_from_place(city_name, tags=school_tags)
    
    # Print the counts as requested
    print(f"Successfully fetched {len(hospitals_gdf)} hospitals.")
    print(f"Successfully fetched {len(schools_gdf)} schools.")
    
    return hospitals_gdf, schools_gdf
