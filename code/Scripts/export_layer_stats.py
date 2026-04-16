from qgis.core import (
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsProject,
    QgsVectorFileWriter,
    QgsLayout,
    QgsLayoutExporter,
    QgsLayoutItemMap,
    QgsMapSettings,
    QgsRectangle,
    QgsUnitTypes,
    QgsCoordinateTransformContext,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant
import os


def export_layer_with_stats(
    layer: QgsVectorLayer,
    output_path: str,
    export_type: str = "CSV",
    area_field: str = "area_m2",
    pct_field: str = "area_pct",
):
    """Add area and area percentage attributes to *layer* and export it.

    Parameters
    ----------
    layer: QgsVectorLayer
        The layer to process. Must be a polygon layer.
    output_path: str
        Destination file path. For CSV the extension should be .csv, for PDF .pdf.
    export_type: str, optional
        ``"CSV"`` or ``"PDF"``. Defaults to ``"CSV"``.
    area_field: str, optional
        Name of the field that will store the area in square metres.
    pct_field: str, optional
        Name of the field that will store the area percentage.
    """

    if not layer.isValid() or layer.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError("Layer must be a valid polygon layer.")

    # Compute total area of the layer
    total_area = 0.0
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom and not geom.isEmpty():
            total_area += geom.area()

    # Add fields if they do not exist
    layer.startEditing()
    if area_field not in [f.name() for f in layer.fields()]:
        layer.addAttribute(QgsField(area_field, QVariant.Double))
    if pct_field not in [f.name() for f in layer.fields()]:
        layer.addAttribute(QgsField(pct_field, QVariant.Double))
    layer.updateFields()

    area_idx = layer.fields().indexFromName(area_field)
    pct_idx = layer.fields().indexFromName(pct_field)

    # Populate attributes
    for feat in layer.getFeatures():
        geom = feat.geometry()
        area = geom.area() if geom and not geom.isEmpty() else 0.0
        pct = (area / total_area) * 100 if total_area > 0 else 0.0
        layer.changeAttributeValue(feat.id(), area_idx, area)
        layer.changeAttributeValue(feat.id(), pct_idx, pct)

    layer.commitChanges()

    # Export
    if export_type.upper() == "CSV":
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        QgsVectorFileWriter.writeAsVectorFormat(
            layer,
            output_path,
            "utf-8",
            layer.crs(),
            "CSV",
            onlySelected=False,
            driverName="CSV",
            options=["GEOMETRY=AS_WKT"],
        )
    elif export_type.upper() == "PDF":
        # Create a simple layout with a map of the layer
        project = QgsProject.instance()
        layout = QgsLayout(project)
        layout.initializeDefaults()
        layout.setName("Export Layout")

        # Map item
        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(20, 20, 200, 200)
        map_item.setExtent(layer.extent())
        map_item.setLayers([layer])
        layout.addItem(map_item)

        exporter = QgsLayoutExporter(layout)
        export_settings = QgsLayoutExporter.PdfExportSettings()
        exporter.exportToPdf(output_path, export_settings)
    else:
        raise ValueError("Unsupported export_type. Use 'CSV' or 'PDF'.")

    return output_path

# Example usage (uncomment to run in QGIS Python console):
# layer = QgsProject.instance().mapLayersByName("my_polygon_layer")[0]
# export_layer_with_stats(layer, r"C:\\temp\\layer_stats.csv", export_type="CSV")
