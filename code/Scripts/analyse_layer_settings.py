from dataclasses import dataclass, field
from typing import List, Optional
from qgis.core import QgsVectorLayer

@dataclass
class AnalyseLayerSettings:
    """Container for all user‑selected analysis options."""
    analyze_layer: QgsVectorLayer
    search_area_layer: QgsVectorLayer
    search_radius: Optional[int] = None
    column_name: Optional[str] = None
    distinct_values: List[str] = field(default_factory=list)
    export_csv: bool = False
    export_pdf: bool = False
    output_folder: str = ""
    full_analysis: bool = True

    def __post_init__(self):
        # Optional sanity checks
        if self.search_radius is not None and self.search_radius <= 0:
            raise ValueError("search_radius must be positive")
        if self.analyze_layer is None or self.search_area_layer is None:
            raise ValueError("Both analyze_layer and search_area_layer must be provided")