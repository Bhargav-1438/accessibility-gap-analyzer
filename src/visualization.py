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
    # 1. Calculate map center
    # Reproject to EPSG:3857 to calculate accurate centroids without GeoPandas geographic CRS warnings,
    # then immediately reproject the centroids back to EPSG:4326 (lat/lon) for Folium mapping.
    centroids_geo = zones_gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
    center_lat = centroids_geo.y.mean()
    center_lon = centroids_geo.x.mean()
    
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
    
    # --- Prepare Formatted Columns for the Interactive Popup ---
    # We safely extract and format the data required for the tooltip display
    zones['ward_name'] = zones.get('name', 'Unknown Ward')
    zones['score_fmt'] = zones['gap_score'].apply(lambda x: f"{x:.2f}")
    
    # Create a visual severity badge using universally supported colored emojis
    def get_badge(cat):
        if cat == 'Low': return '🟢 Low'
        if cat == 'Moderate': return '🟡 Moderate'
        if cat == 'High': return '🟠 High'
        if cat == 'Critical': return '🔴 Critical'
        return '⚪ Unknown'
        
    zones['severity'] = zones.get('gap_category', 'Unknown').apply(get_badge)
    zones['hosp_dist'] = zones.get('nearest_hospital_distance', 0).apply(lambda x: f"{x:.0f} m")
    zones['school_dist'] = zones.get('nearest_school_distance', 0).apply(lambda x: f"{x:.0f} m")
    
    # Create a cleaned GeoDataFrame with only the strictly necessary columns
    # This keeps the GeoJSON payload small and ensures high frontend performance
    cols_to_keep = ['zone_id', 'gap_score', 'geometry', 'ward_name', 'score_fmt', 'severity', 'hosp_dist', 'school_dist']
    zones_clean = zones[[c for c in cols_to_keep if c in zones.columns]].copy()
    
    # 3. Add the Choropleth layer
    choro = folium.Choropleth(
        geo_data=zones_clean,
        data=zones_clean,
        columns=['zone_id', 'gap_score'],
        key_on='feature.properties.zone_id',
        fill_color='RdYlGn_r', # RdYlGn_r: Low score = Green, High score = Red
        fill_opacity=0.6,
        line_weight=2,
        line_opacity=0.5,
        highlight=True,  # Bonus: Enables dynamic hover highlighting!
        legend_name='Accessibility Gap Score (Higher is Worse)'
    )
    
    # 3.b Add the dark-themed interactive tooltip
    tooltip = folium.GeoJsonTooltip(
        fields=['ward_name', 'score_fmt', 'severity', 'hosp_dist', 'school_dist'],
        aliases=['Ward Name:', 'Gap Score:', 'Severity:', 'Nearest Hospital:', 'Nearest School:'],
        style=("background-color: #1A202C; color: #FAFAFA; font-family: 'Inter', sans-serif; "
               "font-size: 13px; padding: 12px; border-radius: 8px; border: 1px solid #2D3748; "
               "box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);")
    )
    tooltip.add_to(choro.geojson)
    choro.add_to(m)
    
    # 4. Add Hospital markers (Red)
    if not hospitals_gdf.empty:
        # Reproject to calculate centroids safely without warnings, then back to EPSG:4326 for Folium
        hosp_centroids = hospitals_gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
        for geom in hosp_centroids:
            folium.Marker(
                location=[geom.y, geom.x],
                icon=folium.Icon(color='red', icon='plus')
            ).add_to(m)
            
    # 5. Add School markers (Blue)
    if not schools_gdf.empty:
        # Reproject to calculate centroids safely without warnings, then back to EPSG:4326 for Folium
        school_centroids = schools_gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
        for geom in school_centroids:
            folium.Marker(
                location=[geom.y, geom.x],
                icon=folium.Icon(color='blue', icon='book')
            ).add_to(m)
            
    # Return the fully constructed map
    return m
