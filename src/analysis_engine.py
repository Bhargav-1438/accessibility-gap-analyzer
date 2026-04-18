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
    # Create a copy to avoid modifying the original data
    zones = zones_gdf.copy()
    
    # 1. Compute centroid for each zone
    centroids = zones.geometry.centroid
    
    hospital_distances = []
    school_distances = []
    
    # 2. For each zone, calculate distance to nearest facilities
    for centroid in centroids:
        # Calculate distance to nearest hospital
        if not hospitals_gdf.empty:
            # .distance() calculates distance to all points, .min() finds the nearest
            min_hosp = hospitals_gdf.geometry.distance(centroid).min()
        else:
            min_hosp = None
        hospital_distances.append(min_hosp)
            
        # Calculate distance to nearest school
        if not schools_gdf.empty:
            min_school = schools_gdf.geometry.distance(centroid).min()
        else:
            min_school = None
        school_distances.append(min_school)
        
    # 3. Store results in new columns
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
