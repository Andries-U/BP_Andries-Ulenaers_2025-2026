import requests
from typing import Dict, Any

BASE_URL = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?"

def fetch_pvgis_monthly_production_json(
    lat: float, 
    lon: float, 
    peakpower: float = 1.0, 
    slope: float = 0.0, 
    aspect: float = 0.0,
    losses: float = 14.0,
    dataset: str = "PVGIS-SARAH3"
) -> Dict[str, Any]:
    """
    Haalt data op als JSON en geeft direct een Python dictionary terug.
    """
    endpoint = f"{BASE_URL}seriesdata"
    
    params = {
        'lat': lat,
        'lon': lon,
        'peakpower': peakpower,
        'angle': slope,
        'aspect': aspect,
        'loss': losses,
        'dataset': dataset,
        'outputformat': 'json'  # <--- Cruciaal: vraag JSON aan
    }
    
    response = requests.get(endpoint, params=params, timeout=30)
    response.raise_for_status()
    
    # .json() parse de string automatisch naar een Python dict
    return response.json()