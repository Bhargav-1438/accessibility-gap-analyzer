import networkx as nx
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from src.routing import load_or_create_graph
from src.analysis_engine import calculate_network_distances, calculate_gap_score
from src.ml_engine import cluster_underserved_zones

def inject_facility(G_cached: nx.MultiDiGraph, lat: float, lon: float, facility_type: str) -> nx.MultiDiGraph:
    """
    Creates an in-memory copy of the routing graph and injects a temporary hypothetical facility node.
    """
    # 1. Create a safe, in-memory copy of the network graph (do not mutate the cached version)
    G_sim = G_cached.copy()
    
    # 2. Generate a unique ID for the simulated node (higher than any existing OSM node ID)
    sim_node_id = max(G_sim.nodes()) + 1
    
    # 3. Add the simulated node with appropriate metadata
    G_sim.add_node(sim_node_id, 
                   y=lat, 
                   x=lon, 
                   facility_type=facility_type, 
                   simulated=True,
                   osmid=sim_node_id)
                   
    # 4. Find the nearest valid walkable node on the street network
    nearest_node = ox.nearest_nodes(G_sim, X=lon, Y=lat)
    
    # 5. Bind the hypothetical facility to the network with a 0-distance edge
    # This allows shortest-path routing from this node into the real network.
    G_sim.add_edge(sim_node_id, nearest_node, key=0, length=0.0, simulated=True)
    G_sim.add_edge(nearest_node, sim_node_id, key=0, length=0.0, simulated=True)
    
    return G_sim

def compute_delta_scores(city_name: str, zones_gdf: gpd.GeoDataFrame, hospitals_gdf: gpd.GeoDataFrame, 
                         schools_gdf: gpd.GeoDataFrame, lat: float, lon: float, facility_type: str):
    """
    Runs the scoring pipeline twice (before/after) and computes the intervention delta.
    
    Returns:
        tuple: (delta_zones_gdf, sim_facility_gdf, new_cluster_hulls)
    """
    # 1. Base Score (Before)
    G_original = load_or_create_graph(city_name)
    base_distances = calculate_network_distances(city_name, zones_gdf, hospitals_gdf, schools_gdf, graph=G_original)
    base_scored = calculate_gap_score(base_distances)
    
    # 2. Inject Hypothetical Facility
    G_modified = inject_facility(G_original, lat, lon, facility_type)
    
    # Create the simulated facility GeoDataFrame entry
    sim_point = Point(lon, lat)
    # Ensure columns match original GDFs to avoid concat warnings
    sim_data = {'simulated': [True], 'name': [f"Simulated {facility_type.title()}"]}
    sim_gdf = gpd.GeoDataFrame(sim_data, geometry=[sim_point], crs=zones_gdf.crs)
    
    # Merge into the appropriate dataset for the second calculation
    if facility_type.lower() == 'hospital':
        mod_hospitals = pd.concat([hospitals_gdf, sim_gdf], ignore_index=True)
        mod_schools = schools_gdf
    else:
        mod_hospitals = hospitals_gdf
        mod_schools = pd.concat([schools_gdf, sim_gdf], ignore_index=True)
        
    # 3. Simulated Score (After)
    sim_distances = calculate_network_distances(city_name, zones_gdf, mod_hospitals, mod_schools, graph=G_modified)
    sim_scored = calculate_gap_score(sim_distances)
    
    # 4. Compute Delta Metrics
    delta_gdf = sim_scored.copy()
    delta_gdf['score_before'] = base_scored['gap_score']
    delta_gdf['score_after'] = sim_scored['gap_score']
    
    # Delta: Negative represents improvement (lower gap score is better)
    delta_gdf['delta'] = delta_gdf['score_after'] - delta_gdf['score_before']
    
    # Percent improvement
    def calc_pct(row):
        if row['score_before'] > 0:
            return (abs(row['delta']) / row['score_before']) * 100
        return 0.0
        
    delta_gdf['pct_change'] = delta_gdf.apply(calc_pct, axis=1)
    
    delta_gdf['severity_before'] = base_scored['gap_category']
    delta_gdf['severity_after'] = sim_scored['gap_category']
    
    # Recompute DBSCAN clusters on the AFTER data to map desert shrinkage
    clustered_sim = cluster_underserved_zones(delta_gdf, score_threshold=60.0)
    from src.ml_engine import generate_cluster_hulls
    new_hulls = generate_cluster_hulls(clustered_sim)
    
    return clustered_sim, sim_gdf, new_hulls
