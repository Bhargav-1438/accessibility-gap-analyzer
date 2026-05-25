import networkx as nx
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, MultiPoint
import pandas as pd
from src.routing import load_or_create_graph

def generate_isochrones(city_name: str, lat: float, lon: float, walk_mins: list = [5, 10, 15, 30], speed_kmh: float = 5.0) -> gpd.GeoDataFrame:
    """
    Generates network-constrained walkable service areas (isochrones) for a given facility location.
    
    Args:
        city_name (str): City to load the base graph for.
        lat (float): Latitude of the facility.
        lon (float): Longitude of the facility.
        walk_mins (list): List of minute thresholds for the walksheds.
        speed_kmh (float): Walking speed in km/h.
        
    Returns:
        gpd.GeoDataFrame: Multi-layered polygons representing walkshed coverage.
    """
    # 1. Load base graph
    G = load_or_create_graph(city_name)
    
    # 2. Find nearest node to the hypothetical facility
    center_node = ox.nearest_nodes(G, X=lon, Y=lat)
    
    # Pre-calculate meters per minute (e.g., 5 km/h = 83.33 m/min)
    meters_per_min = (speed_kmh * 1000) / 60.0
    
    isochrone_polys = []
    
    # Ensure walk_mins is sorted descending so largest polygon is drawn first (bottom layer)
    walk_mins = sorted(walk_mins, reverse=True)
    
    for minutes in walk_mins:
        max_dist_meters = minutes * meters_per_min
        
        # 3. Extract subgraph of all reachable nodes within the time threshold
        # 'length' is the physical street edge distance in meters
        subgraph = nx.ego_graph(G, center_node, radius=max_dist_meters, distance='length')
        
        # 4. Extract node coordinate geometries
        node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
        
        # Need at least 3 points to form a valid polygon
        if len(node_points) < 3:
            continue
            
        # 5. Generate Convex Hull and Simplify
        cloud = MultiPoint(node_points)
        hull = cloud.convex_hull
        
        # Aggressive simplification for Folium rendering performance and stable UX
        # 0.0005 degrees is roughly 50 meters, eliminating jagged artifacts while preserving coverage shape
        hull_simplified = hull.simplify(tolerance=0.0005, preserve_topology=True)
        
        # Calculate coverage area in sq km
        # Temporarily project to a metric CRS (EPSG:3857) to ensure accurate area calculation
        hull_metric = gpd.GeoSeries([hull_simplified], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
        area_sq_km = hull_metric.area / 1e6
        
        isochrone_polys.append({
            'walk_time_mins': minutes,
            'area_sq_km': round(area_sq_km, 2),
            'geometry': hull_simplified,
            'simulated_pop': int((area_sq_km / 2.0) * 15000) # Simple synthetic population estimation based on area
        })
        
    if not isochrone_polys:
        return gpd.GeoDataFrame(columns=['walk_time_mins', 'area_sq_km', 'simulated_pop', 'geometry'], geometry='geometry', crs="EPSG:4326")
        
    return gpd.GeoDataFrame(isochrone_polys, crs="EPSG:4326")
