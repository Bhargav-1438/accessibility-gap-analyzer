import folium

def create_map(zones_gdf, hospitals_gdf, schools_gdf, cluster_hulls_gdf=None, simulation_mode=False, sim_facility_gdf=None, recommendations=None, isochrones_gdf=None):
    """
    Creates a Folium map with satellite tiles, choropleth for gap scores, and facility markers.
    
    Args:
        zones_gdf (GeoDataFrame): City zones with 'gap_score' column (and simulation delta columns if active).
        hospitals_gdf (GeoDataFrame): Point geometries for hospitals.
        schools_gdf (GeoDataFrame): Point geometries for schools.
        cluster_hulls_gdf (GeoDataFrame): DBSCAN infrastructure desert polygons.
        simulation_mode (bool): If True, renders the delta impact overlay.
        sim_facility_gdf (GeoDataFrame): Hypothetical injected facility.
        
    Returns:
        folium.Map: The generated map object.
    """
    # 1. Calculate map center safely
    centroids_geo = zones_gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
    center_lat = centroids_geo.y.mean()
    center_lon = centroids_geo.x.mean()
    
    # 2. Create the base Folium map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite'
    )
    
    zones = zones_gdf.copy()
    zones['zone_id'] = zones.index.astype(str)
    
    # --- Prepare Formatted Columns for the Interactive Popup ---
    zones['ward_name'] = zones.get('name', 'Unknown Ward')
    zones['score_fmt'] = zones['gap_score'].apply(lambda x: f"{x:.2f}")
    
    def get_badge(cat):
        if cat == 'Low': return '🟢 Low'
        if cat == 'Moderate': return '🟡 Moderate'
        if cat == 'High': return '🟠 High'
        if cat == 'Critical': return '🔴 Critical'
        return '⚪ Unknown'
        
    zones['severity'] = zones.get('gap_category', 'Unknown').apply(get_badge)
    zones['hosp_dist'] = zones.get('nearest_hospital_distance', 0).apply(lambda x: f"{x:.0f} m")
    zones['school_dist'] = zones.get('nearest_school_distance', 0).apply(lambda x: f"{x:.0f} m")
    
    cols_to_keep = ['zone_id', 'gap_score', 'geometry', 'ward_name', 'score_fmt', 'severity', 'hosp_dist', 'school_dist']
    
    # Inject simulation formatting if active
    if simulation_mode:
        zones['delta_raw'] = zones.get('delta', 0)
        zones['score_after_raw'] = zones.get('score_after', 0)
        zones['score_before_fmt'] = zones.get('score_before', 0).apply(lambda x: f"{x:.1f}")
        zones['score_after_fmt'] = zones.get('score_after', 0).apply(lambda x: f"{x:.1f}")
        zones['delta_fmt'] = zones.get('delta', 0).apply(lambda x: f"{x:.1f}")
        zones['pct_change_fmt'] = zones.get('pct_change', 0).apply(lambda x: f"{x:.1f}%")
        zones['severity_before'] = zones.get('severity_before', 'Unknown').apply(get_badge)
        zones['severity_after'] = zones.get('severity_after', 'Unknown').apply(get_badge)
        
        cols_to_keep.extend(['delta_raw', 'score_after_raw', 'score_before_fmt', 'score_after_fmt', 
                             'delta_fmt', 'pct_change_fmt', 'severity_before', 'severity_after'])

    # Strip down the GeoDataFrame for performance
    zones_clean = zones[[c for c in cols_to_keep if c in zones.columns]].copy()
    
    # 3. Add the Base Choropleth layer
    choro = folium.Choropleth(
        geo_data=zones_clean,
        data=zones_clean,
        columns=['zone_id', 'gap_score'],
        key_on='feature.properties.zone_id',
        fill_color='RdYlGn_r',
        fill_opacity=0.4 if simulation_mode else 0.6, # Dim base layer if simulating
        line_weight=1,
        line_opacity=0.3,
        name='Base Gap Score'
    )
    
    if not simulation_mode:
        # Standard Tooltip
        tooltip = folium.GeoJsonTooltip(
            fields=['ward_name', 'score_fmt', 'severity', 'hosp_dist', 'school_dist'],
            aliases=['Ward Name:', 'Gap Score:', 'Severity:', 'Nearest Hospital:', 'Nearest School:'],
            style=("background-color: #1A202C; color: #FAFAFA; font-family: 'Inter', sans-serif; "
                   "font-size: 13px; padding: 12px; border-radius: 8px; border: 1px solid #2D3748;")
        )
        tooltip.add_to(choro.geojson)
    
    choro.add_to(m)
    
    # 3.a Add Delta Visualization Overlay
    if simulation_mode:
        def delta_style(feature):
            delta = feature['properties'].get('delta_raw', 0)
            score_after = feature['properties'].get('score_after_raw', 0)
            
            if delta <= -15:
                color = '#48BB78' # Green - strongly improved
                opacity = 0.75
            elif delta < -2:
                color = '#ECC94B' # Yellow - partially improved
                opacity = 0.65
            elif score_after >= 60:
                color = '#E53E3E' # Red - unresolved and severe
                opacity = 0.55
            else:
                color = '#A0AEC0' # Transparent - unresolved but not severe
                opacity = 0.1
                
            return {
                'fillColor': color,
                'color': color,
                'weight': 2 if delta < -2 else 1,
                'fillOpacity': opacity,
            }
            
        sim_tooltip = folium.GeoJsonTooltip(
            fields=['ward_name', 'score_before_fmt', 'score_after_fmt', 'delta_fmt', 'pct_change_fmt', 'severity_before', 'severity_after'],
            aliases=['Ward:', 'Before Score:', 'After Score:', 'Delta (Impact):', 'Improvement:', 'Severity Before:', 'Severity After:'],
            style=("background-color: #1A202C; color: #FAFAFA; font-family: 'Inter', sans-serif; "
                   "font-size: 13px; padding: 12px; border-radius: 8px; border: 1px solid #48BB78; "
                   "box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);")
        )
        
        folium.GeoJson(
            zones_clean,
            name="Simulation Delta Impact",
            style_function=delta_style,
            tooltip=sim_tooltip
        ).add_to(m)
    
    # 3.c Add Cluster Convex Hulls (Phase 2.5 Intelligence)
    if cluster_hulls_gdf is not None and not cluster_hulls_gdf.empty:
        style_function = lambda x: {
            'fillColor': '#800080', 
            'color': '#800080',
            'weight': 3,
            'fillOpacity': 0.15,
            'dashArray': '6, 6'
        }
        
        hull_tooltip = folium.GeoJsonTooltip(
            fields=['cluster_name', 'ward_count', 'avg_gap_score', 'dominant_severity'],
            aliases=['Intervention Region:', 'Wards Affected:', 'Avg Gap Score:', 'Peak Severity:'],
            style=("background-color: #2D3748; color: #E2E8F0; font-family: 'Inter', sans-serif; "
                   "font-size: 13px; padding: 12px; border-radius: 8px; border: 1px solid #4A5568;")
        )
        
        folium.GeoJson(
            cluster_hulls_gdf,
            name="Infrastructure Deserts (DBSCAN)",
            style_function=style_function,
            tooltip=hull_tooltip
        ).add_to(m)
    
    # 4. Add Hospital markers (Red)
    if not hospitals_gdf.empty:
        hosp_centroids = hospitals_gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
        for geom in hosp_centroids:
            folium.Marker(
                location=[geom.y, geom.x],
                icon=folium.Icon(color='red', icon='plus')
            ).add_to(m)
            
    # 5. Add School markers (Blue)
    if not schools_gdf.empty:
        school_centroids = schools_gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
        for geom in school_centroids:
            folium.Marker(
                location=[geom.y, geom.x],
                icon=folium.Icon(color='blue', icon='book')
            ).add_to(m)
            
    # 6. Add Simulated Facility (Glowing effect)
    if sim_facility_gdf is not None and not sim_facility_gdf.empty:
        sim_centroids = sim_facility_gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
        for geom in sim_centroids:
            folium.Marker(
                location=[geom.y, geom.x],
                icon=folium.Icon(color='lightgray', icon_color='#00FFFF', icon='star', prefix='fa'),
                tooltip="Hypothetical Simulated Facility"
            ).add_to(m)
            
    # 7. Add Auto-Suggest Recommendations (Phase 3B Intelligence)
    if recommendations:
        for rec in recommendations:
            rank = rec['rank']
            
            # Color code based on rank
            if rank == 1:
                color = 'orange'
            elif rank == 2:
                color = 'lightred'
            elif rank == 3:
                color = 'purple'
            else:
                color = 'darkblue'
                
            popup_html = f"""
            <div style="font-family: 'Inter', sans-serif; font-size: 13px; width: 250px;">
                <h4 style="margin-top: 0; color: #2D3748;">Intervention #{rank}</h4>
                <b>Projected Gap Reduction:</b> {rec['projected_gap_reduction_pts']} pts<br>
                <b>Affected Population:</b> {rec['affected_population']:,}<br>
                <b>Wards Improved:</b> {rec['wards_improved']}<br>
                <b>Severity Shift:</b> {rec['severity_shift']} wards<br>
                <hr style="margin: 8px 0;">
                <i style="color: #4A5568;">{rec['reasoning']}</i>
            </div>
            """
            
            folium.Marker(
                location=[rec['lat'], rec['lon']],
                icon=folium.Icon(color=color, icon='star', prefix='fa'),
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"AI Recommendation #{rank}"
            ).add_to(m)
            
    # 8. Add Isochrone Coverage Layers (Phase 3C Intelligence)
    if isochrones_gdf is not None and not isochrones_gdf.empty:
        def iso_style(feature):
            mins = feature['properties'].get('walk_time_mins', 30)
            
            # Color hierarchy: Dark Green (5) -> Light Green (10) -> Orange (15) -> Red (30)
            if mins <= 5:
                color = '#276749' # Dark Green
                opacity = 0.5
            elif mins <= 10:
                color = '#48BB78' # Light Green
                opacity = 0.4
            elif mins <= 15:
                color = '#ED8936' # Orange
                opacity = 0.3
            else:
                color = '#E53E3E' # Red
                opacity = 0.2
                
            return {
                'fillColor': color,
                'color': color,
                'weight': 1,
                'fillOpacity': opacity,
            }
            
        iso_tooltip = folium.GeoJsonTooltip(
            fields=['walk_time_mins', 'area_sq_km', 'simulated_pop'],
            aliases=['Walk Coverage (mins):', 'Est. Coverage Area (sq.km):', 'Est. Served Population:'],
            style=("background-color: #2D3748; color: #E2E8F0; font-family: 'Inter', sans-serif; "
                   "font-size: 13px; padding: 12px; border-radius: 8px; border: 1px solid #4A5568;")
        )
        
        folium.GeoJson(
            isochrones_gdf,
            name="Isochrone Coverage",
            style_function=iso_style,
            tooltip=iso_tooltip
        ).add_to(m)
            
    # Add Layer Control
    folium.LayerControl().add_to(m)
            
    return m
