import os
import osmnx as ox
import geopandas as gpd
from shapely.ops import unary_union

print("Loading GHMC wards...")

gdf = gpd.read_file("data/boundaries/ghmc-wards.geojson")

# Match the exact same 8 pilot wards used in city_manager.py
pilot_gdf = gdf.head(8)

print(f"Selected {len(pilot_gdf)} pilot wards.")

pilot_polygon = unary_union(pilot_gdf.geometry)

print("Downloading pilot-zone walking graph...")

G = ox.graph_from_polygon(
    pilot_polygon,
    network_type="walk"
)

os.makedirs("data/graphs", exist_ok=True)

output_path = "data/graphs/hyderabad_pilot.graphml"

ox.save_graphml(G, output_path)

size_mb = os.path.getsize(output_path) / 1e6

print(f"Saved graph to: {output_path}")
print(f"Graph size: {size_mb:.2f} MB")
