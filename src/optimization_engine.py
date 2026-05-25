import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from src.simulation_engine import compute_delta_scores
from src.routing import load_or_create_graph
from src.analysis_engine import calculate_network_distances, calculate_gap_score

DEFAULT_WARD_POPULATION = 10000

def find_optimal_locations(city_name: str, zones_gdf: gpd.GeoDataFrame, hospitals_gdf: gpd.GeoDataFrame, 
                           schools_gdf: gpd.GeoDataFrame, n: int = 3, facility_type: str = "hospital") -> list:
    """
    Identifies the top N most impactful facility placements using a True Greedy algorithm.
    It evaluates the impact of hypothetical facilities, places the best one, updates the city state, 
    and then evaluates for the next placement.
    """
    zones = zones_gdf.copy()
    
    # 1. Ensure population data exists for impact metrics (Synthetic placeholder if missing)
    if "population" not in zones.columns:
        zones["population"] = DEFAULT_WARD_POPULATION
        zones["population_estimated"] = True
        
    # We mutate these during the greedy loop to reflect the newly improved city state
    current_hospitals = hospitals_gdf.copy()
    current_schools = schools_gdf.copy()
    current_zones = zones.copy()
    
    recommendations = []
    
    for iteration in range(1, n + 1):
        # Candidate Selection: Only test centroids of Critical and High severity wards to optimize performance
        candidates = current_zones[current_zones['gap_category'].isin(['Critical', 'High'])]
        
        if candidates.empty:
            break # No more critical/high regions left to fix
            
        best_candidate = None
        best_impact = -1
        best_sim_gdf = None
        best_metrics = {}
        
        # Test each candidate location
        for idx, row in candidates.iterrows():
            centroid = row.geometry.centroid
            lat, lon = centroid.y, centroid.x
            
            try:
                # compute_delta_scores handles injecting the node and routing the before/after deltas
                sim_zones, sim_facility, sim_hulls = compute_delta_scores(
                    city_name, current_zones, current_hospitals, current_schools, lat, lon, facility_type
                )
                
                # Evaluate Impact
                # Delta is negative for improvements, so we sum the absolute values of improved zones
                total_gap_reduction = abs(sim_zones[sim_zones['delta'] < 0]['delta'].sum())
                
                improved_wards = sim_zones[sim_zones['delta'] < -2]
                affected_population = improved_wards['population'].sum()
                wards_improved_count = len(improved_wards)
                
                # Severity shift: How many wards dropped out of Critical/High
                severe_before = len(sim_zones[sim_zones['severity_before'].isin(['Critical', 'High'])])
                severe_after = len(sim_zones[sim_zones['gap_category'].isin(['Critical', 'High'])])
                severity_shift = severe_before - severe_after
                
                # Optimization Metric: Maximize total gap score reduction
                impact_score = total_gap_reduction
                
                if impact_score > best_impact:
                    best_impact = impact_score
                    best_candidate = (lat, lon)
                    best_sim_gdf = sim_facility
                    best_metrics = {
                        'lat': lat,
                        'lon': lon,
                        'total_gap_reduction': total_gap_reduction,
                        'affected_population': affected_population,
                        'wards_improved': wards_improved_count,
                        'severity_shift': severity_shift,
                        'ward_name': row.get('name', 'Unknown Ward')
                    }
                    
            except Exception as e:
                # If routing fails for an isolated node candidate, skip it
                continue
                
        if best_candidate is not None:
            # 1. Construct the human-readable reasoning engine output
            pop_fmt = f"{int(best_metrics['affected_population']):,}"
            reasoning = (f"This placement targets the {best_metrics['ward_name']} region, "
                         f"improving accessibility for an estimated {pop_fmt} residents across "
                         f"{best_metrics['wards_improved']} wards. "
                         f"It removes {best_metrics['severity_shift']} wards from Critical/High severity.")
            
            # 2. Save the recommendation
            rec = {
                "rank": iteration,
                "lat": best_metrics['lat'],
                "lon": best_metrics['lon'],
                "facility_type": facility_type,
                "projected_gap_reduction_pts": round(best_metrics['total_gap_reduction'], 1),
                "affected_population": int(best_metrics['affected_population']),
                "wards_improved": best_metrics['wards_improved'],
                "severity_shift": best_metrics['severity_shift'],
                "reasoning": reasoning
            }
            recommendations.append(rec)
            
            # 3. Update the "Current State" for the next Greedy Iteration
            if facility_type.lower() == 'hospital':
                current_hospitals = pd.concat([current_hospitals, best_sim_gdf], ignore_index=True)
            else:
                current_schools = pd.concat([current_schools, best_sim_gdf], ignore_index=True)
                
            # Re-evaluate the baseline gap scores so the next iteration uses the improved city state
            G_base = load_or_create_graph(city_name)
            new_dists = calculate_network_distances(city_name, current_zones, current_hospitals, current_schools, graph=G_base)
            current_zones = calculate_gap_score(new_dists)
            
            # Ensure population is preserved for the next loop
            current_zones["population"] = zones["population"]
            
        else:
            break # No valid candidates found that improve the score
            
    return recommendations
