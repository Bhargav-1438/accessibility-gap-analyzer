import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.city_manager import get_city_boundary, SUPPORTED_CITIES
from src.data_ingestion import fetch_facilities
from src.analysis_engine import calculate_network_distances, calculate_gap_score
from src.optimization_engine import find_optimal_locations
from src.coverage_engine import generate_isochrones
import json

app = FastAPI(title="Accessibility Gap Analyzer API", version="3.D")

class OptimizeRequest(BaseModel):
    city_name: str = "Hyderabad, India"
    facility_type: str = "hospital"
    n_interventions: int = 3

class IsochroneRequest(BaseModel):
    city_name: str = "Hyderabad, India"
    lat: float
    lon: float

@app.get("/health")
def health_check():
    """Health check for deployment monitoring."""
    return {"status": "operational", "platform": "Accessibility Gap Analyzer"}
    
@app.get("/cities")
def list_cities():
    """Returns dynamically supported cities."""
    return {"supported_cities": SUPPORTED_CITIES}

@app.post("/optimize")
def optimize_interventions(req: OptimizeRequest):
    """Headless API endpoint for automated intervention intelligence."""
    try:
        zones_gdf = get_city_boundary(req.city_name)
        hospitals_gdf, schools_gdf = fetch_facilities(req.city_name)
        
        dists = calculate_network_distances(req.city_name, zones_gdf, hospitals_gdf, schools_gdf)
        scored = calculate_gap_score(dists)
        
        recs = find_optimal_locations(req.city_name, scored, hospitals_gdf, schools_gdf, 
                                      n=req.n_interventions, facility_type=req.facility_type)
        return {"city": req.city_name, "recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/isochrones")
def get_isochrones(req: IsochroneRequest):
    """API endpoint for fetching coverage intelligence."""
    try:
        iso_gdf = generate_isochrones(req.city_name, req.lat, req.lon)
        if iso_gdf.empty:
            return {"city": req.city_name, "isochrones": {}}
        iso_json = iso_gdf.to_json()
        return {"city": req.city_name, "isochrones": json.loads(iso_json)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
