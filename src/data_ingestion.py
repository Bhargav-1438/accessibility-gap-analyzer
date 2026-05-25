import geopandas as gpd
import osmnx as ox
import logging

logger = logging.getLogger(__name__)

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
    Uses polygon-based retrieval to cleanly support custom deployment zones.
    
    Args:
        city_name (str): Name of the city or deployment zone (e.g., 'Hyderabad Pilot Zone')
        
    Returns:
        tuple: (hospitals_gdf, schools_gdf)
    """
    print(f"Fetching facilities for {city_name} from OpenStreetMap...")
    logger.info(f"Initiating facility retrieval for {city_name}")
    
    # 1. Retrieve the single source of truth polygon
    from src.city_manager import get_city_boundary
    boundary_gdf = get_city_boundary(city_name)
    polygon = boundary_gdf.geometry.unary_union
    
    logger.info(f"Polygon bounds established: {polygon.bounds}")
    
    # Define OSM tags to search for
    hospital_tags = {'amenity': 'hospital'}
    school_tags = {'amenity': 'school'}
    
    try:
        # Fetch spatial data strictly within the pilot polygon
        hospitals_gdf = ox.features_from_polygon(polygon, tags=hospital_tags)
    except Exception as e:
        logger.warning(f"No hospitals found or error during retrieval: {e}")
        # Return empty GeoDataFrame if nothing is found
        hospitals_gdf = gpd.GeoDataFrame(columns=['geometry'], geometry='geometry')
        
    try:
        schools_gdf = ox.features_from_polygon(polygon, tags=school_tags)
    except Exception as e:
        logger.warning(f"No schools found or error during retrieval: {e}")
        schools_gdf = gpd.GeoDataFrame(columns=['geometry'], geometry='geometry')
    
    logger.info(f"Successfully fetched {len(hospitals_gdf)} hospitals.")
    logger.info(f"Successfully fetched {len(schools_gdf)} schools.")
    
    print(f"Successfully fetched {len(hospitals_gdf)} hospitals.")
    print(f"Successfully fetched {len(schools_gdf)} schools.")
    
    return hospitals_gdf, schools_gdf
