import folium

def create_map(zones_gdf, hospitals_gdf, schools_gdf):
    """
    Creates a Folium map with satellite tiles, choropleth for gap scores, and facility markers.
    
    Args:
        zones_gdf (GeoDataFrame): City zones with 'gap_score' column.
        hospitals_gdf (GeoDataFrame): Point geometries for hospitals.
        schools_gdf (GeoDataFrame): Point geometries for schools.
        
    Returns:
        folium.Map: The generated map object.
    """
    # 1. Calculate map center based on the average centroid of our zones
    center_lat = zones_gdf.geometry.centroid.y.mean()
    center_lon = zones_gdf.geometry.centroid.x.mean()
    
    # 2. Create the base Folium map
    # We use a custom tile URL for Esri World Imagery to get the satellite view
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite'
    )
    
    # To guarantee Folium maps the data to the geometry perfectly, 
    # we ensure there is a proper unique ID column for zones.
    zones = zones_gdf.copy()
    zones['zone_id'] = zones.index.astype(str)
    
    # Create a cleaned GeoDataFrame with only the strictly necessary columns
    # This prevents Folium from failing when serializing complex, un-needed columns into GeoJSON
    zones_clean = zones[['zone_id', 'gap_score', 'geometry']]
    
    # 3. Add the Choropleth layer
    folium.Choropleth(
        geo_data=zones_clean,
        data=zones_clean,
        columns=['zone_id', 'gap_score'],
        key_on='feature.properties.zone_id',
        fill_color='RdYlGn_r', # RdYlGn_r: Low score = Green, High score = Red
        fill_opacity=0.6,
        line_weight=2,
        line_opacity=0.5,
        legend_name='Accessibility Gap Score (Higher is Worse)'
    ).add_to(m)
    
    # 4. Add Hospital markers (Red)
    if not hospitals_gdf.empty:
        for _, row in hospitals_gdf.iterrows():
            # Facilities from OSMnx can be polygons. We use centroid to safely get x/y coordinates.
            geom = row.geometry.centroid
            folium.Marker(
                location=[geom.y, geom.x],
                icon=folium.Icon(color='red', icon='plus')
            ).add_to(m)
            
    # 5. Add School markers (Blue)
    if not schools_gdf.empty:
        for _, row in schools_gdf.iterrows():
            geom = row.geometry.centroid
            folium.Marker(
                location=[geom.y, geom.x],
                icon=folium.Icon(color='blue', icon='book')
            ).add_to(m)
            
    # Return the fully constructed map
    return m
