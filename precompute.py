from src.city_manager import SUPPORTED_CITIES, get_city_boundary
from src.routing import load_or_create_graph
from src.data_ingestion import fetch_facilities

def run_precomputation():
    """
    Pre-downloads and caches routing graphs and city boundaries for all supported cities.
    This guarantees zero cold-start latency when the API/Dashboard boots up in production Docker environments.
    """
    print("Starting deployment graph precomputation...")
    for city in SUPPORTED_CITIES:
        try:
            print(f"Precomputing boundaries and routing graph for {city}...")
            # 1. Cache Boundaries
            get_city_boundary(city)
            # 2. Cache Routing Graph
            load_or_create_graph(city)
            # 3. Cache OSM Facilities
            fetch_facilities(city)
            print(f"Successfully cached {city}.")
        except Exception as e:
            print(f"Warning: Failed to precompute {city}: {e}")
            
if __name__ == "__main__":
    run_precomputation()
