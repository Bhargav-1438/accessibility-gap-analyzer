import pandas as pd
import geopandas as gpd
import json
import datetime

def generate_session_report(city_name, zones_gdf, recommendations, isochrones_gdf=None):
    """
    Generates a structured dictionary containing session intelligence, which can be easily exported as JSON.
    """
    report = {
        "metadata": {
            "city": city_name,
            "export_time": datetime.datetime.now().isoformat(),
            "platform_version": "3.D (Civic Infrastructure)"
        },
        "accessibility_summary": {},
        "interventions": [],
        "coverage_summary": {}
    }
    
    # 1. Accessibility Summary
    if zones_gdf is not None and not zones_gdf.empty:
        total_wards = len(zones_gdf)
        if 'gap_category' in zones_gdf.columns:
            critical_count = len(zones_gdf[zones_gdf['gap_category'] == 'Critical'])
            high_count = len(zones_gdf[zones_gdf['gap_category'] == 'High'])
        else:
            critical_count = 0
            high_count = 0
            
        report["accessibility_summary"] = {
            "total_zones_analyzed": total_wards,
            "critical_infrastructure_deserts": critical_count,
            "high_severity_zones": high_count,
            "overall_health": "Critical" if critical_count > (total_wards * 0.1) else "Stable"
        }
        
    # 2. Recommendations
    if recommendations:
        for rec in recommendations:
            report["interventions"].append({
                "rank": rec['rank'],
                "type": rec['facility_type'],
                "coordinates": {"lat": rec['lat'], "lon": rec['lon']},
                "projected_gap_reduction": rec['projected_gap_reduction_pts'],
                "wards_improved": rec['wards_improved'],
                "severity_shift": rec['severity_shift'],
                "estimated_population_reached": rec['affected_population'],
                "strategic_reasoning": rec['reasoning']
            })
            
    # 3. Coverage Summary
    if isochrones_gdf is not None and not isochrones_gdf.empty:
        # Get the largest walkshed threshold
        max_iso = isochrones_gdf[isochrones_gdf['walk_time_mins'] == isochrones_gdf['walk_time_mins'].max()]
        if not max_iso.empty:
            report["coverage_summary"] = {
                "max_walk_time_mins": int(max_iso.iloc[0]['walk_time_mins']),
                "total_coverage_area_sqkm": float(max_iso['area_sq_km'].sum()),
                "estimated_population_covered_new": int(max_iso['simulated_pop'].sum()) if 'simulated_pop' in max_iso.columns else 0
            }
            
    return report

def export_to_markdown(report: dict) -> str:
    """Converts the JSON report into a formatted Markdown string suitable for Github, printing, or Pandoc PDF conversion."""
    md = f"# Accessibility Gap Analyzer — Operational Report\n\n"
    md += f"**City:** {report['metadata']['city']}  \n"
    md += f"**Export Date:** {report['metadata']['export_time']}  \n\n"
    
    md += "## 1. Systemic Accessibility Summary\n"
    summ = report['accessibility_summary']
    md += f"- **Total Zones Analyzed:** {summ.get('total_zones_analyzed', 0)}\n"
    md += f"- **Critical Infrastructure Deserts:** {summ.get('critical_infrastructure_deserts', 0)}\n"
    md += f"- **High Severity Zones:** {summ.get('high_severity_zones', 0)}\n"
    md += f"- **Overall Regional Health:** {summ.get('overall_health', 'Unknown')}\n\n"
    
    if report['interventions']:
        md += "## 2. Strategic Intervention Recommendations (AI Optimized)\n"
        for rec in report['interventions']:
            md += f"### Rank {rec['rank']}: New {rec['type'].title()} Placement\n"
            md += f"- **Coordinates:** {rec['coordinates']['lat']:.5f}, {rec['coordinates']['lon']:.5f}\n"
            md += f"- **Projected Gap Reduction:** {rec['projected_gap_reduction']} pts\n"
            md += f"- **Wards Improved:** {rec['wards_improved']}\n"
            md += f"- **Severity Shift:** {rec['severity_shift']} wards removed from Critical/High\n"
            md += f"- **Estimated Population Reached:** {rec['estimated_population_reached']:,}\n"
            md += f"- **Strategic Reasoning:** *{rec['strategic_reasoning']}*\n\n"
            
    if report.get('coverage_summary'):
        cov = report['coverage_summary']
        md += "## 3. Isochrone Coverage Intelligence\n"
        md += f"- **Max Modeled Walk Time:** {cov.get('max_walk_time_mins', 0)} mins\n"
        md += f"- **Total New Coverage Area:** {cov.get('total_coverage_area_sqkm', 0):.2f} sq.km\n"
        md += f"- **Estimated Population Covered by New Services:** {cov.get('estimated_population_covered_new', 0):,}\n"
        
    return md
