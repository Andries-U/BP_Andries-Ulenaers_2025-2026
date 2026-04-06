import requests
from typing import Dict, Any
from SolarDataClient import SolarDataClient
from qgis.core import QgsCoordinateReferenceSystem

class PVGISClient(SolarDataClient):
    """PVGIS API solar data provider with configurable parameters."""
    
    BASE_URL = "https://re.jrc.ec.europa.eu/api/v5_3/"
    
    def __init__(
        self,
        peakpower: float = 1.0,
        slope: float = 0.0,
        aspect: float = 0.0,
        losses: float = 14.0,
        dataset: str = "PVGIS-SARAH3",
        crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:4326"),
    ):
        """
        Initialize PVGIS client with default parameters.
        
        Args:
            peakpower: System peak power (kW).
            slope: Array tilt angle (degrees).
            aspect: Array orientation (degrees).
            losses: System losses (%).
            dataset: PVGIS dataset version.
            crs: Coordinate reference system for input coordinates (default WGS84).
        """
        super().__init__(crs)  
        self.peakpower = peakpower
        self.slope = slope
        self.aspect = aspect
        self.losses = losses
        self.dataset = dataset

    def fetch(
        self,
        lat: float, 
        lon: float, 
        peakpower: float = None, 
        slope: float = None, 
        aspect: float = None,
        losses: float = None,
        dataset: str = None
    ) -> Dict[str, Any]:
        """
        Get the solar production data from the PVGIS API for a given location and parameters.

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            peakpower (float, optional): System peak power (kW). Defaults to instance value
            slope (float, optional): Array tilt angle (degrees). Defaults to instance value.
            aspect (float, optional): Array orientation (degrees). Defaults to instance value.
            losses (float, optional): System losses (%). Defaults to instance value.
            dataset (str, optional): PVGIS dataset version. Defaults to instance value.
        Returns:
            Dict[str, Any]: Parsed JSON response from the PVGIS API.
        """
        # Use instance defaults if parameters not provided
        if peakpower is None:
            peakpower = self.peakpower
        if slope is None:
            slope = self.slope
        if aspect is None:
            aspect = self.aspect
        if losses is None:
            losses = self.losses
        if dataset is None:
            dataset = self.dataset
        
        endpoint = f"{self.BASE_URL}PVcalc?"
        
        params = {
            'lat': lat,
            'lon': lon,
            'peakpower': peakpower,
            'angle': slope,
            'aspect': aspect,
            'loss': losses,
            'dataset': dataset,
            'outputformat': 'json'
        }
        
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        
        # .json() parse de string automatisch naar een Python dict
        return response.json()
 
    def get_yearly_total_solar_potential(self, lat: float, lon: float, src_crs: QgsCoordinateReferenceSystem) -> float:
        """
        Get the yearly total solar potential (E_y) for a given latitude and longitude.

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            src_crs (QgsCoordinateReferenceSystem): The source coordinate reference system.
        Returns:
            float: Yearly total solar potential in kWh.
        """
        lat, lon = self.normalize_coords(lat, lon, src_crs)
        data = self.fetch(lat, lon)
        
        # Controleer of de verwachte data aanwezig is
        if 'outputs' in data and 'totals' in data['outputs'] and 'fixed' in data['outputs']['totals'] and 'E_y' in data['outputs']['totals']['fixed']:
            return data['outputs']['totals']['fixed']['E_y']
        else:
            raise ValueError("Ongeldige API-respons: verwachte data ontbreekt.")
        
    def get_average_daily_solar_potential(self, lat: float, lon: float, src_crs: QgsCoordinateReferenceSystem) -> float:
        """
        Get the average daily solar potential (E_d) for a given latitude and longitude.
        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            src_crs (QgsCoordinateReferenceSystem): The source coordinate reference system.
        Returns:
            float: Average daily solar potential in kWh.
        """
        lat, lon = self.normalize_coords(lat, lon, src_crs)
        data = self.fetch(lat, lon)
        
        if 'outputs' in data and 'totals' in data['outputs'] and 'fixed' in data['outputs']['totals'] and 'E_d' in data['outputs']['totals']['fixed']:
            return data['outputs']['totals']['fixed']['E_d']
        else:
            raise ValueError("Ongeldige API-respons: verwachte data ontbreekt.")