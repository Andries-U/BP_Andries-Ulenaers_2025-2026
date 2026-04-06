from pvgis_client import fetch_pvgis_monthly_production_json
from pvgis_parser import parse_pvgis_json_response

# 1. Ophalen (Geeft direct een dict terug)
ruwe_json_dict = fetch_pvgis_monthly_production_json(lat=50.937024, lon=5.391518, peakpower=0.24, slope=15)


print(ruwe_json_dict)
print("*"*50)
# 2. Parsen (Extract alleen wat jij nodig hebt)
schone_data = parse_pvgis_json_response(ruwe_json_dict)
print(schone_data)
print("*"*50)

print(f"Totale opbrengst: {schone_data['jaar_totalen']['totaal_jaar_prod_kwh']} kWh")
print(schone_data['maand_data'])