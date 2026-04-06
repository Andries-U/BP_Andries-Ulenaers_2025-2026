import pandas as pd
from typing import Dict, Any, List

def parse_pvgis_json_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses the specific nested JSON structure from PVGIS API v5.2+.
    
    Structure expected:
    {
      "inputs": { "location": {...}, "pv_module": {...}, ... },
      "outputs": {
         "monthly": { "fixed": [ {month:1, E_m:...}, ... ] },
         "totals": { "fixed": { E_y: ..., l_total: ... } }
      },
      "meta": { ... }
    }
    """
    
    # Safe navigation to avoid crashes if keys are missing
    outputs = data.get('outputs', {})
    inputs = data.get('inputs', {})
    meta = data.get('meta', {})
    
    # --- 1. Parse Monthly Data ---
    # Path: outputs -> monthly -> fixed (List of dicts)
    monthly_data_list = outputs.get('monthly', {}).get('fixed', [])
    
    if not monthly_data_list:
        raise ValueError("No monthly data found in 'outputs.monthly.fixed'")
    
    # Convert list of dicts to DataFrame
    df_maanden = pd.DataFrame(monthly_data_list)
    
    # Optional: Ensure 'month' is integer and sort just in case
    if 'month' in df_maanden.columns:
        df_maanden['month'] = df_maanden['month'].astype(int)
        df_maanden = df_maanden.sort_values('month')

    # --- 2. Parse Yearly Totals ---
    # Path: outputs -> totals -> fixed (Single dict)
    totals_data = outputs.get('totals', {}).get('fixed', {})
    
    jaar_totalen = {
        'totaal_jaar_prod_kwh': totals_data.get('E_y'),          # Yearly energy production
        'gem_dag_prod_kwh': totals_data.get('E_d'),              # Average daily energy
        'totaal_jaar_irradiatie_kwh_m2': totals_data.get('H(i)_y'), # Yearly irradiation
        'gem_dag_irradiatie_kwh_m2': totals_data.get('H(i)_d'),
        'verlies_aoi_pct': totals_data.get('l_aoi'),
        'verlies_spectrum_pct': totals_data.get('l_spec'),
        'verlies_temp_pct': totals_data.get('l_tg'),
        'verlies_totaal_pct': totals_data.get('l_total')
    }

    # --- 3. Parse Metadata ---
    location = inputs.get('location', {})
    pv_module = inputs.get('pv_module', {})
    meteo = inputs.get('meteo_data', {})
    
    metadata = {
        'latitude': location.get('latitude'),
        'longitude': location.get('longitude'),
        'elevation_m': location.get('elevation'),
        'database_radiation': meteo.get('radiation_db'),
        'database_meteo': meteo.get('meteo_db'),
        'peakpower_kwp': pv_module.get('peak_power'),
        'system_loss_pct': pv_module.get('system_loss'),
        'technology': pv_module.get('technology')
    }

    # --- 4. Assemble Final Result ---
    return {
        'bron': 'PVGIS',
        'metadata': metadata,
        'jaar_totalen': jaar_totalen,
        'maand_data': df_maanden,
        'ruwe_outputs': outputs # Keep raw outputs if you need deeper access later
    }