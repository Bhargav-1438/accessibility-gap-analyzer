import geopandas as gpd
import pandas as pd
from src.routing import load_or_create_graph, map_points_to_nodes, compute_network_metrics

def calculate_network_distances(city_name, zones_gdf, hospitals_gdf, schools_gdf, graph=None):
    """
    Calculates walking-network distance and estimated travel time from zone centroids to nearest facilities.
    
    Args:
        city_name (str): Name of the city to load the graph.
        zones_gdf (GeoDataFrame): Polygon geometries of city zones
        hospitals_gdf (GeoDataFrame): Point geometries of hospitals
        schools_gdf (GeoDataFrame): Point geometries of schools
        
    Returns:
        GeoDataFrame: Zones updated with network distance and time columns.
    """
    zones = zones_gdf.copy()
    
    # 1. Load the routing graph if not provided
    if graph is None:
        graph = load_or_create_graph(city_name)
    
    # 2. Map geometries to graph nodes
    # For zones, we map the centroid to the nearest street node
    zone_nodes = map_points_to_nodes(graph, zones)
    hosp_nodes = map_points_to_nodes(graph, hospitals_gdf)
    school_nodes = map_points_to_nodes(graph, schools_gdf)
    
    # 3. Compute network metrics (Distance and Time)
    # Hospitals
    print("Computing network distances to nearest hospitals...")
    hosp_metrics = compute_network_metrics(graph, zone_nodes, hosp_nodes)
    zones['nearest_hospital_distance'] = [m['distance_m'] for m in hosp_metrics]
    zones['nearest_hospital_time_min'] = [m['time_min'] for m in hosp_metrics]
    
    # Schools
    print("Computing network distances to nearest schools...")
    school_metrics = compute_network_metrics(graph, zone_nodes, school_nodes)
    zones['nearest_school_distance'] = [m['distance_m'] for m in school_metrics]
    zones['nearest_school_time_min'] = [m['time_min'] for m in school_metrics]
    
    return zones

def calculate_gap_score(zones_gdf):
    """
    Computes accessibility gap scores based strictly on NETWORK distances and classifies them.
    
    Args:
        zones_gdf (GeoDataFrame): Zones with network distance metrics
        
    Returns:
        GeoDataFrame: Zones updated with 'gap_score' and 'gap_category' columns.
    """
    zones = zones_gdf.copy()
    
    # 1. Combine into a single primary score based on walking distance
    zones['combined_distance'] = (zones['nearest_hospital_distance'] + zones['nearest_school_distance']) / 2
    
    # Handle infinite values (unreachable nodes)
    # We cap infinity at the maximum valid distance in the dataset, plus a small penalty (10%)
    valid_dists = zones.loc[zones['combined_distance'] != float('inf'), 'combined_distance']
    max_valid = valid_dists.max() if not valid_dists.empty else 0
    penalty_max = max_valid * 1.1 # 10% penalty for being totally unreachable
    
    # Replace inf with the penalized max distance
    zones['combined_distance'] = zones['combined_distance'].replace(float('inf'), penalty_max)
    
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
