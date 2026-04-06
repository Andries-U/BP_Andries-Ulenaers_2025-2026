from code.Scripts.calculation_utils import select_layer_from_available_cui, select_feature_from_layer_database, select_item_from_gui_list, generate_triangle_from_multiline_string_using_convex_hull
from reset_module_cache import reload_all_custom_modules
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsPointXY, QgsGeometry
from PyQt5.QtCore import QVariant

reload_all_custom_modules()

# Get the current QGIS project and its CRS
project = QgsProject.instance()
project_crs = project.crs().authid()  # e.g., "EPSG:31370"
point_layer_name = "Corner_Points_ET"

# List of possible attributes to add
point_layer_attributes = [
    QgsField("id_original", QVariant.Int)
]

selected_layer = select_layer_from_available_cui("Select the layer containing the triangle:")

point_layer = QgsVectorLayer(f"Point?crs={project_crs}", point_layer_name, "memory")
point_layer.dataProvider().addAttributes(point_layer_attributes)
point_layer.dataProvider().addAttributes(selected_layer.fields())
point_layer.updateFields()

if selected_layer is None:
    print("No layer selected. Exiting.")

for feature in selected_layer.getFeatures():
    corner_points = generate_triangle_from_multiline_string_using_convex_hull(feature.geometry())
    print(f"corner points for feature ID {feature.id()}: {corner_points}")
    for idx, point in enumerate(corner_points):
        new_feature = QgsFeature()
        new_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point)))
        new_feature.setAttributes([feature.id()] + feature.attributes())
        point_layer.dataProvider().addFeature(new_feature)

QgsProject.instance().addMapLayer(point_layer)