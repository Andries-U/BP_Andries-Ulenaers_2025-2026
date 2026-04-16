from qgis.utils import iface
from item_selection import ItemSelectionDialog
from qgis.core import (
    QgsVectorLayer, QgsMapLayer, QgsRasterLayer, QgsMeshLayer, QgsFeature, QgsVectorTileLayer, QgsField, QgsGeometry, QgsPointXY, QgsCoordinateReferenceSystem, QgsWkbTypes, QgsVectorFileWriter, QgsCoordinateTransformContext
)
from PyQt5.QtCore import QVariant
from typing import List, Tuple
import processing

def get_centroid_of_polygon(polygon_geom: QgsGeometry) -> QgsPointXY:
    """
    Calculate the geometric center (centroid) of a QGIS polygon geometry.
    
    Args:
        polygon_geom (QgsGeometry): The geometry object of the polygon.
    
    Returns:
        QgsPointXY: The geometric center (X, Y).
                    Returns None if the geometry is invalid or empty.
    
    Example usage:
        # feature = layer.getFeature(1)
        # point = get_centroid_of_polygon(feature.geometry())
        # print(f"X: {point.x()}, Y: {point.y()}")
    """
    
    # Check for null or empty geometry
    if polygon_geom.isNull() or polygon_geom.isEmpty():
        raise ValueError("Given geometry is null or empty. Cannot calculate centroid.")

    # Calculate the centroid
    centroid_geom = polygon_geom.centroid()
    
    # Check if centroid calculation was successful
    if centroid_geom.isEmpty():
        raise ValueError("Kon geen centroïde berekenen voor deze geometrie.")
        
    return centroid_geom.asPoint()

def check_equality_of_layer_crs_to_wanted_crs(layers: List[QgsMapLayer], wanted_crs: QgsCoordinateReferenceSystem) -> bool:
    """
    Check if the CRS of two layers are the same.
    
    Args:
        layers (List[QgsMapLayer]): The layers to check.
        wanted_crs (QgsCoordinateReferenceSystem): The wanted coordinate reference system.
    
    Returns:
        bool: True if the CRS of all layers match the wanted CRS, False otherwise.
    """

    for layer in layers:
        if layer.crs().authid() != wanted_crs.authid():
            print(f"❌ Layer '{layer.name()}' has CRS {layer.crs().authid()} which does not match the wanted CRS {wanted_crs.authid()}")
            return False
    return True

def generate_triangle_from_multiline_string_using_convex_hull(multiline_geom: QgsGeometry) -> List[QgsPointXY]:
    """
    Generate a triangle from a multiline string geometry using the convex hull method.
    Args:        
        multiline_geom (QgsGeometry): The input multiline string geometry.
    Returns:        
        List[QgsPointXY]: A list of three points representing the corners of the triangle.
    """

    if multiline_geom.isNull() or multiline_geom.isEmpty():
        raise ValueError("De aangeleverde geometrie is leeg of null.")
    
    convex_hull = multiline_geom.convexHull()
    
    if convex_hull.isEmpty():
        raise ValueError("Kon geen convex hull berekenen voor deze geometrie.")
    
    # Extract the vertices of the convex hull
    hull_points = convex_hull.asPolygon()[0]
    triangle_corners = [hull_points[0], hull_points[len(hull_points) // 2], hull_points[-1]]

    return triangle_corners

def get_corners_of_polygon(polygon_geom: QgsGeometry) -> List[QgsPointXY]:
    """
    Get the corner points of a polygon geometry.
    
    Args:
        polygon_geom (QgsGeometry): The input polygon geometry.
    
    Returns:
        List[QgsPointXY]: A list of corner points (X, Y) of the polygon.
    
    Example usage:
        # feature = layer.getFeature(1)
        # corners = get_corners_of_polygon(feature.geometry())
        # for corner in corners:
        #     print(f"Corner X: {corner.x()}, Y: {corner.y()}")
    """
    
    if polygon_geom.isNull() or polygon_geom.isEmpty():
        raise ValueError("De aangeleverde geometrie is leeg of null.")
    
    if not polygon_geom.isMultipart():
        return [polygon_geom.asPolygon()[0][i] for i in range(len(polygon_geom.asPolygon()[0]))]
    else:
        return [polygon_geom.asMultiPolygon()[0][0][i] for i in range(len(polygon_geom.asMultiPolygon()[0][0]))]

def print_count_layer(layer: QgsMapLayer):
    """
    Print the count of the features of a valid layer.
    Args:
        layer (QgsMapLayer): The layer to check and print the feature count for.
    """
    if layer.isValid():
        count = layer.featureCount()
        print(f"✅ {layer.name()}: {count} features")
    else:
        print(f"❌ Layer '{layer.name()}' is invalid")

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

def make_empty_copy_of_vector_layer(copy_layer_name: str, source_layer: QgsVectorLayer):
    """
    Copy the given layer schema to a new temporary layer in memory (wich is empty, without features)
    
    Args:
        copy_layer_name (str): The name for the copied layer.
        source_layer (QgsVectorLayer): The layer to copy.
        
    Returns:
    """
    new_layer = QgsVectorLayer(
        f"{source_layer.wkbType().name}?crs={source_layer.crs().authid()}",
        copy_layer_name,
        "memory"
    )
    
    new_layer.startEditing()
    new_layer.dataProvider().addAttributes(source_layer.fields())
    new_layer.updateFields()
    new_layer.commitChanges()
    
    if not new_layer.isValid():
        print("❌ Layer is invalid after creation!")
        return None
    return new_layer

def is_within_polygon(search_polygon: QgsGeometry, area_polygon: QgsGeometry) -> bool:
    """
    Check if the search polygon is within the area polygon.

    Args:
        search_polygon (QgsGeometry): The polygon to search if within the search area.
        areaPolygon (QgsGeometry): The polygon that defines the area.

    Returns:
        bool: True if the search polygon is within the area polygon, False otherwise.
    """
    return search_polygon.within(area_polygon)

def is_intersecting_polygon(search_polygon: QgsGeometry, area_polygon: QgsGeometry) -> bool:
    """
    Check if the search polygon intersects with the area polygon.

    Args:
        search_polygon (QgsGeometry): The polygon to search if within the search area.
        area_polygon (QgsGeometry): The polygon that defines the area.

    Returns:
        bool: True if the search polygon intersects with the area polygon, False otherwise.
    """
    return area_polygon.intersects(search_polygon)

def copy_vector_layer_to_temp(copy_layer_name: str, source_layer: QgsVectorLayer) -> QgsVectorLayer:
    """
    Copy the given layer to a new temporary layer in memory
    
    Args:
        copy_layer_name (str): The name for the copied layer.
        source_layer (QgsVectorLayer): The layer to copy.
        
    Returns:
    """
    
    new_layer = make_empty_copy_of_vector_layer(copy_layer_name, source_layer)
    
    new_layer.startEditing()
    

    #for feature in progress_bar(source_layer.getFeatures(), total=source_layer.featureCount(), prefix='Progress:', suffix='Complete'):
    for feature in source_layer.getFeatures():
        new_feat = QgsFeature()
        new_feat.setGeometry(feature.geometry())
        new_feat.setAttributes(feature.attributes())
        new_layer.dataProvider().addFeature(new_feat)

    new_layer.updateFields()
    new_layer.commitChanges()
    

    return new_layer

    
def copy_raster_layer_to_temp(copy_layer_name: str, source_layer: QgsRasterLayer) -> QgsRasterLayer:
        """
        Copy the given raster layer to a new temporary raster layer.

        This function is currently unimplemented and serves as a placeholder.
        Raster layer cloning/copying in memory is non-trivial in QGIS and often
        requires writing to a temporary file and reloading with QgsRasterLayer.
        
        Args:
            copy_layer_name (str): The name for the copied layer.
            source_layer (QgsRasterLayer): The raster layer to copy.

        Raises:
            NotImplementedError: Always, until this function is implemented.

        Returns:
            QgsRasterLayer: (not returned, placeholder only)
        """
        raise NotImplementedError(
            "copy_raster_layer_to_temp is not yet implemented. "
            "Implement with temporary file export + reloading if needed."
        )
    
def copy_mesh_layer_to_temp(copy_layer_name: str, source_layer: QgsMeshLayer) -> QgsMeshLayer:
    """
    Copy the given layer to a new temporary layer in memory
    
    Args:
        copy_layer_name (str): The name for the copied layer.
        source_layer (QgsMeshLayer): The layer to copy.
    Raises:
            NotImplementedError: Always, until this function is implemented. 
    Returns:
        QgsMeshLayer: The in memory copy of the input layer
    """
    raise NotImplementedError(
            "copy_raster_layer_to_temp is not yet implemented. "
            "Implement with temporary file export + reloading if needed."
    )

def copy_vector_tile_layer_to_temp(copy_layer_name: str, source_layer: QgsVectorTileLayer) -> QgsVectorTileLayer:
    """
    Copy the given layer to a new temporary layer in memory
    
    Args:
        copy_layer_name (str): The name for the copied layer.
        source_layer (QgsVectorTileLayer): The layer to copy.
        
    Returns:
        QgsVectorTileLayer: The in memory copy of the input layer

    Raises:
            NotImplementedError: Always, until this function is implemented.
    """
    raise NotImplementedError(
            "copy_vector_tile_layer_to_temp is not yet implemented. "
            "Implement with temporary file export + reloading if needed."
        )


def copy_plugin_layer_to_temp(copy_layer_name: str, source_layer: QgsMapLayer) -> QgsMapLayer:
    """
    Copy the given layer to a new temporary layer in memory
    
    Args:
        copy_layer_name (str): The name for the copied layer.
        source_layer (QgsMapLayer): The layer to copy.
        
    Returns:
        QgsMapLayer: The in memory copy of the input layer

    Raises:
            NotImplementedError: Always, until this function is implemented.
    """
    raise NotImplementedError(
            "copy_vector_tile_layer_to_temp is not yet implemented. "
            "Implement with temporary file export + reloading if needed."
        )
    
def copy_layer_to_temp(copy_layer_name: str, source_layer: QgsMapLayer) -> QgsMapLayer:
    """
    Copy any QGIS layer to a temporary layer.
    Works for vector, raster, mesh, and other layer types.

    Args:
        copy_layer_name (str) : The name for the copied layer.
        source_layer (QgsMapLayer): The layer to copy.

    Returns:
        QgsMapLayer: A temporary copy of the layer.
    """
    if source_layer.type() == source_layer.VectorLayer:
        temp_layer = copy_vector_layer_to_temp(copy_layer_name, source_layer)

    elif source_layer.type() == source_layer.RasterLayer:
        temp_layer = copy_raster_layer_to_temp(copy_layer_name, source_layer)

    elif source_layer.type() == source_layer.MeshLayer:
        temp_layer = copy_mesh_layer_to_temp(copy_layer_name, source_layer)

    elif source_layer.type() == source_layer.VectorTileLayer:
        temp_layer = copy_vector_tile_layer_to_temp(copy_layer_name, source_layer)

    elif source_layer.type() == source_layer.PluginLayer:
        temp_layer = copy_plugin_layer_to_temp(copy_layer_name, source_layer)

    else:
        raise ValueError(f"Unsupported layer type: {source_layer.type()}")

    return temp_layer

def generate_search_area_around_point(point: QgsPointXY, radius: float, segments: int = 36) -> QgsGeometry:
    """
    Generate a circular search area around a given point.

    Args:
        point (QgsPointXY): The point around which to generate a search area.
        radius (float): The radius of the circular search area in the same units as the layer's CRS.
        segments (int): The number of segments to use for the circular buffer.

    Returns:
        QgsGeometry: The circular search area geometry.
    """
    return QgsGeometry.fromPointXY(point).buffer(radius, segments)

def generate_search_areas_layer_around_points_from_points_layer(points: QgsVectorLayer, radius: float, generated_layer_name: str = "Search_Areas", layer: QgsVectorLayer = None, segments: int = 36) -> QgsVectorLayer:
    """
    Generate a layer of circular search areas around given a list of points.

    Args:
        points (QgsPointsLayer): The layer containing the points around which to generate search areas.
        radius (float): The radius of the circular search areas in the same units as the layer's CRS.
        generated_layer_name (str): The name for the generated layer.
        layer (QgsVectorLayer): The existing layer to add the search areas to. If None, a new memory layer will be created.
        segments (int): The number of segments to use for the circular buffers.

    Returns:
        QgsVectorLayer: The layer containing the circular search areas.
    """

    if points is None or points.featureCount() == 0 or points.geometryType() != QgsWkbTypes.PointGeometry:
        raise ValueError("The provided points layer is invalid. It must be a non-empty point layer.")
    
    if layer is None:
        layer = QgsVectorLayer(
            f"Polygon?crs={points.crs().authid()}",
            generated_layer_name,
            "memory"
        )
        layer.startEditing()
        layer.dataProvider().addAttributes([QgsField("source_point_id", QVariant.Int)])
        layer.dataProvider().addAttributes(points.fields())
        layer.updateFields()
        layer.commitChanges()

    for point in points.getFeatures():
        search_area = generate_search_area_around_point(point.geometry().asPoint(), radius, segments)
        feature = QgsFeature()
        feature.setGeometry(search_area)
        feature.setAttributes([point.id()] + point.attributes())
        layer.dataProvider().addFeature(feature)
    layer.updateFields()
    layer.commitChanges()

    return layer

def split_layer_by_search_areas(layer: QgsVectorLayer, search_areas_layer: QgsVectorLayer) -> Tuple[QgsVectorLayer, QgsVectorLayer, QgsVectorLayer]:
    """
    Split a layer by given search areas.

    Args:
        layer (QgsVectorLayer): The layer to split.
        search_areas_layer (QgsVectorLayer): The layer containing the search areas to split by.

    Returns:
        tuple: A tuple containing three layers: (features_within_search_areas, features_intersecting_search_areas, features_outside_search_areas)
    """

    if layer is None or layer.featureCount() == 0:
        raise ValueError("The provided layer to split is invalid. It must be a non-empty vector layer.")
    if search_areas_layer is None:
        raise ValueError("The provided search areas layer is invalid. It must be a non-empty vector layer.")
    if search_areas_layer.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError("The search areas layer must be a polygon layer.")
    if search_areas_layer.featureCount() == 0:
        raise ValueError("The search areas layer must contain at least one feature.")
    
    within_layer = make_empty_copy_of_vector_layer(f"{layer.name()}_within_search_areas", layer)
    intersecting_layer = make_empty_copy_of_vector_layer(f"{layer.name()}_intersecting_search_areas", layer)
    outside_layer = make_empty_copy_of_vector_layer(f"{layer.name()}_outside_search_areas", layer)

    for feature in layer.getFeatures():
        feature_geom = feature.geometry()
        within = False
        intersecting = False

        for search_area in search_areas_layer.getFeatures():
            search_area_geom = search_area.geometry()
            if feature_geom.within(search_area_geom):
                within = True
                break
            elif feature_geom.intersects(search_area_geom):
                intersecting = True
        
        if within:
            within_layer.dataProvider().addFeature(feature)
            within_layer.updateFields()
            within_layer.commitChanges()
        elif intersecting:
            intersecting_layer.dataProvider().addFeature(feature)
            intersecting_layer.updateFields()
            intersecting_layer.commitChanges()
        else:
            outside_layer.dataProvider().addFeature(feature)
            outside_layer.updateFields()
            outside_layer.commitChanges()
    
    return within_layer, intersecting_layer, outside_layer

def split_layer_by_search_areas_processing(split_layer: QgsVectorLayer, search_areas_layer: QgsVectorLayer) -> Tuple[QgsVectorLayer, QgsVectorLayer, QgsVectorLayer]: 
    """
    Efficiently splits a potentially large layer using QGIS Processing (optimized for memory).
    
    Returns:
        tuple: (fully_inside_layer, partially_inside_layer, outside_layer)
    """

    if split_layer is None or split_layer.featureCount() == 0:
        raise ValueError("The provided layer to split is invalid. It must be a non-empty vector layer.")
    if search_areas_layer is None or search_areas_layer.featureCount() == 0:
        raise ValueError("The search areas layer must be a non-empty polygon layer.")
    if search_areas_layer.geometryType() != 2:  # 2 = PolygonGeometry
        raise ValueError("The search areas layer must be a polygon layer.")

    # 1. CLIP: Extract only features that intersect with search areas.
    try:
        print("Clipping layer to search areas...")
        clip_result = processing.run("native:clip", {
            'INPUT': split_layer,
            'OVERLAY': search_areas_layer,
            'OUTPUT': 'memory:'
        })
        clipped_layer = clip_result['OUTPUT']
        print(f"Type of clipped_layer: {type(clipped_layer)}")
        print(f"Value of clipped_layer: {clipped_layer}")
        
    except Exception as e:
        print(f"Clipping failed: {e}")
        return None, None, None

    clipped_layer = split_layer
    # 2. SPLIT: Use Processing to separate "Within" and "Intersecting" features.
    #    "Within" = features completely inside search areas
    #    "Intersecting" = features partially inside search areas
    try:
        print("Extracting features fully within search areas...")
        within_result = processing.run("native:extractbylocation", {
            'INPUT': clipped_layer,
            'INTERSECT': search_areas_layer,
            'PREDICATE': 6,
            'OUTPUT': 'memory:'
        })
        fully_inside_layer = within_result['OUTPUT']

        print("Extracting features intersecting search areas...")
        intersecting_result = processing.run("native:extractbylocation", {
            'INPUT': clipped_layer,
            'INTERSECT': search_areas_layer,
            'PREDICATE': 0,
            'OUTPUT': 'memory:'
        })
        partially_inside_layer = intersecting_result['OUTPUT']

        print("Removing fully within features from intersecting layer to avoid duplicates...")
        # Remove "Within" features from "Intersecting" layer to avoid duplicates
        processing.run("native:difference", {
            'INPUT': partially_inside_layer,
            'OVERLAY': fully_inside_layer,
            'OUTPUT': 'memory:'
        }, feedback=None)

        print("Difference operation completed. Updating partially inside layer...")
        partially_inside_layer = processing.run("native:difference", {
            'INPUT': partially_inside_layer,
            'OVERLAY': fully_inside_layer,
            'OUTPUT': 'memory:'
        })['OUTPUT']
    
    except Exception as e:
        print(f"Extracting within/intersecting failed: {e}")
        return None, None, None

    # 3. HANDLE "OUTSIDE": Features not intersecting with search areas
    try:
        print("Extracting features outside search areas...")
        outside_result = processing.run("native:extractbylocation", {
            'INPUT': split_layer,
            'INTERSECT': search_areas_layer,
            'PREDICATE': 2,
            'OUTPUT': 'memory:'
        })
        outside_layer = outside_result['OUTPUT']
    except Exception as e:
        print(f"Extracting outside failed: {e}")
        outside_layer = None

    return fully_inside_layer, partially_inside_layer, outside_layer
  
    
