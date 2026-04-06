from qgis.utils import iface
from Item_selection import ItemSelectionDialog
from PyQt5.QtWidgets import QDialog
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRectangle, QgsMapLayer, QgsProject , 
    QgsRasterLayer, QgsMeshLayer, QgsFeature, QgsVectorTileLayer, QgsField, QgsGeometry, QgsPointXY, QgsCoordinateReferenceSystem
)
import sys
from PyQt5.QtCore import QVariant
from typing import TypeVar, Generic, List
from exceptions import SelectionCancelledError, NoItemSelectedError, LayerFeatureError

T = TypeVar('T')

def progress_bar(iterable, total, prefix='', suffix='', length=30, fill='█'):
    for i, item in enumerate(iterable):
        percent = ("{0:.1f}").format(100 * (i / float(total)))
        filled_length = int(length * i // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
        sys.stdout.flush()
        yield item
    sys.stdout.write('\n')


def select_item_from_gui_list(items: list[T], prompt: str = "Select a item", title: str = "Select an item from the list") -> tuple[T, int]:
    """
    Select an item from a list using a GUI dialog.
    Args:
        items (list[T]): The list of items to select from.
        prompt (str): The prompt to display in the selection dialog.
        title (str): The title of the selection dialog.
    Returns:
        tuple[T, int]: The selected item and its index in the original list.
    
    Raises:
        SelectionCancelledError: If the user clicks Cancel.
        NoItemSelectedError: If the dialog accepts but returns no item.

    """
    dialog = ItemSelectionDialog(
        items=items,
        title=title,
        prompt=prompt
    )

    if dialog.exec_() == QDialog.Accepted:
        selected_item= dialog.get_selected_item()
        
        if selected_item is None:
            raise NoItemSelectedError("Dialog accepted but returned no item.")
            
        try:
            index = items.index(selected_item)
            return selected_item, index
        except ValueError:
            raise NoItemSelectedError("Selected item not found in the original list.")
    elif dialog.exec_() == QDialog.Rejected:
        raise SelectionCancelledError("User cancelled the selection dialog.")
    
    # If exec_() returns something other than Accepted or Rejected (rare)
    raise SelectionCancelledError(f"Unknown dialog result.: {dialog.result()}")

def select_feature_from_layer_database(layer: QgsVectorLayer, prompt: str = "Select a feature", title: str = "Select a Feature") -> tuple[QgsFeature, int]:
    """
    Select a feature ID from a vector layer.
    
    Args:
        layer (QgsVectorLayer): The vector layer to select from.
        prompt (str): The prompt to display in the selection dialog.
        title (str): The title of the selection dialog.
    
    Returns:
        tuple[QgsFeature, int]: The selected feature and its ID.

    Raises:
        LayerFeatureError: If features cannot be retrieved.
        SelectionCancelledError: If the user cancels the GUI.
    """

    if not layer:
        raise LayerFeatureError("The provided layer is None.", layer_name="Unknown")
    

    try:
        features = list(layer.getFeatures())
        if not features:
            raise LayerFeatureError("No features found in the layer.", layer_name=layer.name())
        
        features_info = []
        for feature in layer.getFeatures():
            # Gather all info: ID, attributes (as dict), geometry summary (centroid or WKT)
            attr_dict = {layer.fields()[i].name(): feature.attributes()[i] for i in range(len(feature.attributes()))}
            geom_summary = feature.geometry().asWkt() if feature.geometry() else "No geometry"
            display_string = f"ID: {feature.id()}, Attributes: {attr_dict}, Geometry: {geom_summary}"
            features_info.append((display_string, feature.id()))
        
        selected_feature, selected_feature_id = select_item_from_gui_list(
            items=features_info,
            prompt=prompt,
            title=title
        )
    except SelectionCancelledError:
        raise
    except Exception as e:
        raise LayerFeatureError(f"Error retrieving features: {str(e)}", layer_name=layer.name()) from e
    
    if selected_feature is None and selected_feature_id is None:
        raise NoItemSelectedError("No feature selected from the list.")
    return selected_feature, selected_feature_id


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
        raise ValueError("De aangeleverde geometrie is leeg of null.")

    # Calculate the centroid
    centroid_geom = polygon_geom.centroid()
    
    # Check if centroid calculation was successful
    if centroid_geom.isEmpty():
        raise ValueError("Kon geen centroïde berekenen voor deze geometrie.")
        
    return centroid_geom.asPoint()

def get_bbox_from_current_canvas() -> QgsRectangle:
    """
    Gives the QgsRectangle with the coordinates for the current view in the visual editor.
    
    Returns:
        QgsRectangle: Rectangle that encompasses the view of the visual editor
    """
    canvas = iface.mapCanvas()
    bbox = canvas.extent()
    return bbox

def check_equality_of_layer_crs_to_wanted_crs(layers: List[QgsMapLayer], wanted_crs: QgsCoordinateReferenceSystem) -> bool:
    """
    Check if the CRS of two layers are the same.
    
    Args:
        layer1 (QgsMapLayer): The first layer to compare.
        layer2 (QgsMapLayer): The second layer to compare.
        wanted_crs (QgsCoordinateReferenceSystem): The wanted coordinate reference system.
    
    Returns:
        bool: True if the CRS of both layers are the same, False otherwise.
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

def select_layer_from_available_cui(title: str = "Select a Layer", prompt: str = "Choose a layer:") -> QgsMapLayer:
    """
    Command line tool to select one layer from the current project.
    Returns:
        QgsMapLayer: The selected layer
    """
    # Get all layers in the project
    project = QgsProject.instance()
    layers = list(project.mapLayers().values())

    # Show the dialog
    dialog = ItemSelectionDialog(
        items=layers,
        title=title,
        prompt=prompt
    )

    if dialog.exec_() == QDialog.Accepted:
        selected_layer = dialog.get_selected_item()
        return selected_layer
        # Do something with selected_layer

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
        raise Exception(f"Failed to add column '{column_name}' to layer '{layer.name()}'.")
    
    layer.updateFields()
    field_index = layer.fields().indexFromName(column_name)
    if field_index == -1:
        raise Exception(f"Column '{column_name}' added but index could not be resolved.")
    
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

def is_within_polygon(searchPolygon: QgsGeometry, areaPolygon: QgsGeometry) -> bool:
    """
    Check if the search polygon is within the area polygon.

    Args:
        searchPolygon (QgsGeometry): The polygon to search if within the search area.
        areaPolygon (QgsGeometry): The polygon that defines the area.

    Returns:
        bool: True if the search polygon is within the area polygon, False otherwise.
    """
    return areaPolygon.within(searchPolygon)

def is_intersecting_polygon(searchPolygon: QgsGeometry, areaPolygon: QgsGeometry) -> bool:
    """
    Check if the search polygon intersects with the area polygon.

    Args:
        searchPolygon (QgsGeometry): The polygon to search if within the search area.
        areaPolygon (QgsGeometry): The polygon that defines the area.

    Returns:
        bool: True if the search polygon intersects with the area polygon, False otherwise.
    """
    return areaPolygon.intersects(searchPolygon)

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
