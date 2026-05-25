import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
import warnings

# Suppress geometry warnings during projection inside the engine
warnings.filterwarnings('ignore', message='.*Geometry is in a geographic CRS.*')

def cluster_underserved_zones(zones_gdf, score_threshold=60.0, eps_m=2000, min_samples=2):
    """
    Identifies infrastructure deserts using DBSCAN clustering on high-gap zones.
    
    Args:
        zones_gdf (GeoDataFrame): Zones with 'gap_score' column.
        score_threshold (float): Minimum gap score to be considered for clustering (default: 60 - High/Critical).
        eps_m (float): DBSCAN epsilon parameter in meters (default: 2000m).
        min_samples (int): DBSCAN min_samples parameter (default: 2).
        
    Returns:
        GeoDataFrame: Zones with a new 'cluster_id' column (-1 means outlier/unclustered).
    """
    zones = zones_gdf.copy()
    zones['cluster_id'] = -1
    
    # Filter for underserved zones based on threshold
    underserved = zones[zones['gap_score'] >= score_threshold].copy()
    
    if underserved.empty or len(underserved) < min_samples:
        return zones
        
    # Project to metric CRS (EPSG:3857) for accurate Euclidean distance search within DBSCAN
    underserved_proj = underserved.to_crs(epsg=3857)
    
    # Extract coordinates from centroids
    centroids = underserved_proj.geometry.centroid
    coords = np.column_stack((centroids.x, centroids.y))
    
    # Run DBSCAN
    db = DBSCAN(eps=eps_m, min_samples=min_samples)
    labels = db.fit_predict(coords)
    
    # Map labels back to the original dataframe
    underserved['cluster_id'] = labels
    
    # Update the main zones dataframe
    zones.update(underserved[['cluster_id']])
    zones['cluster_id'] = zones['cluster_id'].astype(int)
    
    return zones

def generate_cluster_hulls(zones_gdf):
    """
    Generates convex hull polygons and computes intelligence statistics for each identified cluster.
    
    Args:
        zones_gdf (GeoDataFrame): Zones with 'cluster_id' and 'gap_score' columns.
        
    Returns:
        GeoDataFrame: A GeoDataFrame containing the convex hulls of valid clusters and enriched metrics.
    """
    # Filter out unclustered zones
    clustered = zones_gdf[zones_gdf['cluster_id'] != -1].copy()
    
    if clustered.empty:
        return gpd.GeoDataFrame(columns=['cluster_id', 'geometry'], geometry='geometry', crs=zones_gdf.crs)
        
    # Dissolve geometries by cluster_id to merge them, then wrap in a convex hull
    hulls = clustered.dissolve(by='cluster_id')
    hulls['geometry'] = hulls['geometry'].convex_hull
    
    hulls = hulls.reset_index()
    
    # Calculate statistics for each cluster
    stats = []
    for cluster_id in hulls['cluster_id']:
        cluster_zones = clustered[clustered['cluster_id'] == cluster_id]
        
        # Determine a human-readable cluster name based on the highest severity present
        highest_severity = "Critical" if "Critical" in cluster_zones['gap_category'].values else "High"
        
        stats.append({
            'cluster_id': cluster_id,
            'ward_count': len(cluster_zones),
            'avg_gap_score': round(cluster_zones['gap_score'].mean(), 1),
            'dominant_severity': highest_severity,
            'cluster_name': f"Zone {cluster_id} Infrastructure Desert"
        })
        
    stats_df = pd.DataFrame(stats)
    
    # Merge stats back to hulls, keeping only essential columns
    hulls = hulls[['cluster_id', 'geometry']].merge(stats_df, on='cluster_id')
    
    # Ensure correct return type
    return gpd.GeoDataFrame(hulls, geometry='geometry', crs=zones_gdf.crs)
