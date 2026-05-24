import geopandas as gpd
import pandas as pd

def calculate_nearest_distances(zones_gdf, hospitals_gdf, schools_gdf):
    """
    Calculates straight-line (Euclidean) distance from zone centroids to nearest facilities.
    
    Args:
        zones_gdf (GeoDataFrame): Polygon geometries of city zones
        hospitals_gdf (GeoDataFrame): Point geometries of hospitals
        schools_gdf (GeoDataFrame): Point geometries of schools
        
    Returns:
        GeoDataFrame: Zones updated with distance columns.
    """
    # We must operate on a projected coordinate system (meters) for accurate geometric calculations
    # and to avoid GeoPandas "Geometry is in a geographic CRS" warnings. EPSG:3857 is standard.
    zones_proj = zones_gdf.to_crs(epsg=3857)
    
    # Safely project facilities if they exist
    hosp_proj = hospitals_gdf.to_crs(epsg=3857) if not hospitals_gdf.empty else hospitals_gdf.copy()
    school_proj = schools_gdf.to_crs(epsg=3857) if not schools_gdf.empty else schools_gdf.copy()
    
    # 1. Compute centroid for each zone in the projected CRS
    centroids = zones_proj.geometry.centroid
    
    hospital_distances = []
    school_distances = []
    
    # 2. For each zone, calculate distance to nearest facilities (in meters)
    for centroid in centroids:
        # Calculate distance to nearest hospital
        if not hosp_proj.empty:
            min_hosp = hosp_proj.geometry.distance(centroid).min()
        else:
            min_hosp = None
        hospital_distances.append(min_hosp)
            
        # Calculate distance to nearest school
        if not school_proj.empty:
            min_school = school_proj.geometry.distance(centroid).min()
        else:
            min_school = None
        school_distances.append(min_school)
        
    # 3. Store results in new columns on the ORIGINAL unprojected dataframe
    # This guarantees we return EPSG:4326 for Folium compatibility while keeping the math safe.
    zones = zones_gdf.copy()
    zones['nearest_hospital_distance'] = hospital_distances
    zones['nearest_school_distance'] = school_distances
    
    # 4. Return updated GeoDataFrame
    return zones

def calculate_gap_score(zones_gdf):
    """
    Computes accessibility gap scores based on distances and classifies them.
    
    Args:
        zones_gdf (GeoDataFrame): Zones with distance metrics
        
    Returns:
        GeoDataFrame: Zones updated with 'gap_score' and 'gap_category' columns.
    """
    zones = zones_gdf.copy()
    
    # 1. Combine into a single distance metric (Average)
    zones['combined_distance'] = (zones['nearest_hospital_distance'] + zones['nearest_school_distance']) / 2
    
    # 2. Normalize the values to a 0-100 scale (Min-Max scaling)
    min_dist = zones['combined_distance'].min()
    max_dist = zones['combined_distance'].max()
    
    # Avoid division by zero if all distances are exactly the same
    if max_dist > min_dist:
        zones['gap_score'] = ((zones['combined_distance'] - min_dist) / (max_dist - min_dist)) * 100
    else:
        zones['gap_score'] = 0.0
        
    # 3. Classify into categories based on the gap score
    def classify_score(score):
        if score <= 30:
            return 'Low'
        elif score <= 60:
            return 'Moderate'
        elif score <= 80:
            return 'High'
        else:
            return 'Critical'
            
    zones['gap_category'] = zones['gap_score'].apply(classify_score)
    
    return zones
