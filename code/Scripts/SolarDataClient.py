from abc import ABC, abstractmethod
from typing import Dict, Any
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsProject,
)

class SolarDataClient(ABC):
    """Abstract base class for solar data providers."""

    def __init__(self, crs: QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem("EPSG:4326")):
        """
        Args:
            crs: Coordinate reference system of input coordinates (default WGS84).
        """
        print("Setting CRS to:", crs)
        self._crs = crs  # Directly set the private attribute

    @property
    def crs(self) -> QgsCoordinateReferenceSystem:
        return self._crs  # Return the private attribute

    @crs.setter
    def crs(self, value: QgsCoordinateReferenceSystem):
        self._crs = value  # Set the private attribute

    @abstractmethod
    def fetch(self, lat: float, lon: float, src_crs: QgsCoordinateReferenceSystem) -> Dict[str, Any]:
        """Fetch raw solar data for location."""
        pass

    def normalize_coords(self, lat: float, lon: float, src_crs: QgsCoordinateReferenceSystem) -> tuple[float, float]:
        """
        Normalize input coordinates to the instance's CRS if necessary.
        """
        if src_crs == self._crs:  # Use the private attribute
            return lat, lon
        transform = QgsCoordinateTransform(src_crs, self._crs, QgsProject.instance())
        pt = transform.transform(QgsPointXY(lon, lat))
        return pt.y(), pt.x()

    @abstractmethod
    def get_yearly_total_solar_potential(self, lat: float, lon: float, src_crs: QgsCoordinateReferenceSystem) -> float:
        """Get yearly total solar potential."""
        pass

    @abstractmethod
    def get_average_daily_solar_potential(self, lat: float, lon: float, src_crs: QgsCoordinateReferenceSystem) -> float:
        """Get average daily solar potential."""
        pass