from qgis.core import QgsMapLayer, QgsField, QgsWkbTypes, QgsVectorLayer, edit
from qgis.PyQt.QtCore import QVariant
import processing

def determine_low_cardinality_fields(layer: QgsMapLayer, uniqueness_threshold=0.1, max_unique_values=None, min_data_points=10):
    """
    Determines which fields in the given layer have a number of unique values below the specified threshold.
    
    Parameters:
    - layer: The QgsVectorLayer to analyze.
    - uniqueness_threshold: A float between 0 and 1 representing the maximum allowed ratio of unique values to total features for a field to be considered low-cardinality.
    
    Returns:
    - A list of field names that are considered low-cardinality based on the given threshold.
    """
    total_count = layer.featureCount()

    if total_count == 0:
        raise ValueError("Layer has no features.")
    
    low_cardinality_fields = []

    for field in layer.fields():
        
        column_index = layer.fields().indexFromName(field.name())
        unique_values = layer.uniqueValues(column_index) if column_index != -1 else []

        unique_count = len(unique_values)
        uniqueness_ratio = unique_count / total_count if total_count > 0 else 0
        if uniqueness_ratio <= uniqueness_threshold and unique_count <= max_unique_values and unique_count >= min_data_points:
            low_cardinality_fields.append(field.name())

    return low_cardinality_fields

def add_area_field_crs_aware(layer: QgsVectorLayer, field_name: str = "area_m2", target_crs: str = "EPSG:31370") -> QgsVectorLayer:
    """
    Adds an area field using a CRS-aware QGIS expression.

    Parameters:
    - layer: QgsVectorLayer
    - field_name: name of the output field
    - target_crs: projected CRS used for area calculation (default = EPSG:31370, Belgium)

    Returns:
    - result layer (same as input if in-place)
    """

    if layer.geometryType() == QgsWkbTypes.PointGeometry:
        print("Warning: Layer contains point geometries. Area calculation may not be meaningful.")
        raise ValueError("Cannot calculate area for point geometries.")

    # Bereken oppervlakte
    params = {
        'INPUT': layer,
        'OUTPUT': 'memory:',
        'IGNORE_INVALID': True
    }
    result = processing.run("qgis:exportaddgeometrycolumns", params)['OUTPUT']

    # Hernoem veld naar gewenste naam
    if field_name != 'area':
        result.startEditing()
        idx = result.fields().indexFromName('area')
        if idx != -1:
            result.renameAttribute(idx, field_name)
        result.commitChanges()

    return result


def add_column_to_layer(layer: QgsVectorLayer, column_name: str, data_type: QVariant.Type, length: int = 255, precision: int = 0)-> tuple[QgsField, int]:
    """
    Adds a new column (field) to the given vector layer.

    Args:
        layer (QgsVectorLayer): The vector layer to add the column to.
        column_name (str): The name of the new column.
        data_type (QVariant.Type): The data type of the new column (e.g., QVariant.String, QVariant.Int).
        length (int, optional): The length of the field (for string types). Defaults to 255.
        precision (int, optional): The precision of the field (for numeric types). Defaults to 0.

    Returns:
        QgsField: The field that was added to the layer.
        
    Raises:
        ValueError: If the layer is not a vector layer.
        Exception: If adding the attribute fails.
    """
    if not isinstance(layer, QgsVectorLayer):
        raise ValueError("Layer must be a vector layer to add a column.")
    
    if not layer.isEditable():
        layer.startEditing()
    
    field = QgsField(column_name, data_type, len=length, prec=precision)
    success = layer.dataProvider().addAttributes([field])
    
    if not success:
        error_msg = layer.dataProvider().lastError()
        if error_msg:
            print(f"Data provider error: {error_msg}")
        raise RuntimeError(f"Failed to add column '{column_name}' to layer '{layer.name()}'.")
    
    layer.updateFields()
    field_index = layer.fields().indexFromName(column_name)
    if field_index == -1:
        raise RuntimeError(f"Column '{column_name}' added but index could not be resolved.")
    
    layer.commitChanges()
    return field, field_index