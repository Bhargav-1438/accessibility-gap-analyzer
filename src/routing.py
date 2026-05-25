import os
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Configurable parameter, hardcoded for foundational layer stability
DEFAULT_WALKING_SPEED_KMH = 5.0

def load_or_create_graph(city_name: str, network_type: str = "walk") -> nx.MultiDiGraph:
    """
    Loads a walkable street network graph for the given city.
    Checks local cache first; if not found, downloads from OSM and caches it.
    
    Args:
        city_name (str): The name of the city to retrieve the graph for.
        network_type (str): Type of street network (default: 'walk').
        
    Returns:
        nx.MultiDiGraph: The loaded street network graph.
    """
    # Define cache path
    cache_dir = os.path.join("data", "graphs")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Safe filename for caching
    safe_city_name = city_name.replace(" ", "_").replace(",", "").lower()
    cache_path = os.path.join(cache_dir, f"{safe_city_name}_{network_type}.graphml")
    
    if os.path.exists(cache_path):
        print(f"Loading cached graph from {cache_path}...")
        graph = ox.load_graphml(cache_path)
    else:
        print(f"Downloading {network_type} graph for {city_name} from OSM...")
        if "Pilot Zone" in city_name:
            from src.city_manager import get_city_boundary
            boundary_gdf = get_city_boundary(city_name)
            # Use unary_union to get a single bounding polygon for the pilot zone wards
            polygon = boundary_gdf.geometry.unary_union
            graph = ox.graph_from_polygon(polygon, network_type=network_type, simplify=True)
        else:
            graph = ox.graph_from_place(city_name, network_type=network_type, simplify=True)
            
        print(f"Caching graph to {cache_path}...")
        ox.save_graphml(graph, cache_path)
        
    return graph

def map_points_to_nodes(graph: nx.MultiDiGraph, gdf: gpd.GeoDataFrame) -> pd.Series:
    """
    Maps points in a GeoDataFrame to the nearest node IDs in the street graph.
    
    Args:
        graph (nx.MultiDiGraph): The street network graph.
        gdf (gpd.GeoDataFrame): GeoDataFrame containing point geometries (or polygons to centroid).
        
    Returns:
        pd.Series: Nearest node IDs corresponding to each row in the GeoDataFrame.
    """
    if gdf.empty:
        return pd.Series(dtype=int)
        
    # Ensure we use centroids if polygons are passed (like wards/zones)
    points = gdf.geometry.centroid
    
    # Extract coordinates (OSMnx expects unprojected lat/lon by default for graph nearest_nodes)
    X = points.x
    Y = points.y
    
    # Find nearest nodes using OSMnx
    nearest_nodes = ox.nearest_nodes(graph, X, Y)
    
    return pd.Series(nearest_nodes, index=gdf.index)

def compute_network_metrics(graph: nx.MultiDiGraph, origin_nodes: pd.Series, dest_nodes: pd.Series):
    """
    Computes the shortest walking distance and estimated travel time from origin nodes to nearest destination nodes.
    
    Args:
        graph (nx.MultiDiGraph): The street network graph.
        origin_nodes (pd.Series): Graph node IDs for origins (e.g., zones).
        dest_nodes (pd.Series): Graph node IDs for destinations (e.g., facilities).
        
    Returns:
        list of dict: Distance (meters) and Time (minutes) for each origin node.
    """
    metrics = []
    
    # Pre-calculate walking speed in meters per minute
    # 5 km/h = 5000 m / 60 mins = 83.33 m/min
    speed_m_per_min = (DEFAULT_WALKING_SPEED_KMH * 1000) / 60.0
    
    dest_list = dest_nodes.dropna().tolist()
    
    if not dest_list:
        # If no destinations, return infinity for everything
        return [{'distance_m': float('inf'), 'time_min': float('inf')} for _ in range(len(origin_nodes))]

    for o_node in origin_nodes:
        if pd.isna(o_node):
            metrics.append({'distance_m': float('inf'), 'time_min': float('inf')})
            continue
            
        try:
            # NetworkX shortest_path_length from single source to all reachable nodes
            # 'length' is an attribute populated by osmnx with physical edge distance in meters.
            paths = nx.shortest_path_length(graph, source=o_node, weight='length')
            
            # Filter reachable destination nodes and find the minimum distance
            valid_dists = [paths[d] for d in dest_list if d in paths]
            
            if valid_dists:
                min_dist = min(valid_dists)
                est_time = min_dist / speed_m_per_min
                metrics.append({'distance_m': min_dist, 'time_min': est_time})
            else:
                # Origin node cannot reach any destination nodes
                metrics.append({'distance_m': float('inf'), 'time_min': float('inf')})
                
        except nx.NetworkXNoPath:
            # Absolute fallback if node is completely isolated
            metrics.append({'distance_m': float('inf'), 'time_min': float('inf')})
            
    return metrics
