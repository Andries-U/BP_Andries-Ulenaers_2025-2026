from reset_module_cache import reload_all_custom_modules
from generate_docs import generate_docs_for_custom_modules
from qgis_gui_utils import run_selection_dialog_column_values, select_item_from_gui_list, select_layer_from_available_layers
from calculation_utils import generate_search_areas_layer_around_points_from_points_layer
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer, QgsWkbTypes

MY_MODULES = [
    'reset_module_cache',
    'calculation_utils', 
    'gis_utils',
    'qgis_gui_utils', 
    'pvgis_client', 
    'SolarDataClient', 
    "generate_docs",
    "exceptions", 
    "multiselect_dialog"
]
TEMP_GROUP_NAME = "Temp_Group_For_Processing"
coverage_factor_solar_fields = 0.8  # Assuming 80% of the area can be covered with solar panels.
search_circle_diameter = 5000  # Diameter of the search circle around the corner points of the ET in meters.
features_added = 0

def prepare_temporary_group(group_name: str) -> QgsLayerTreeGroup:
    root = QgsProject.instance().layerTreeRoot()
    temp_group = root.findGroup(group_name)
    if temp_group is None:
        temp_group = root.addGroup(group_name)
    else:
        temp_group.removeAllChildren()
    return temp_group

# Reload all custom modules to ensure the latest code is used
reload_all_custom_modules()

# Generate documentation for custom modules
generate_docs_for_custom_modules(MY_MODULES)

# Make temp group for processing and empty it if it already exists
temp_group = prepare_temporary_group(TEMP_GROUP_NAME)

# Get the project instance and print the name of the project.
project = QgsProject.instance()
print(f"Project name: {project.fileName()}")

# Select the search area layer
selected_area = select_layer_from_available_layers(title="Select Search Area Layer", prompt="Choose the layer that defines the search area:")

# decide action based on the geometry type of the selected layer
geom_type = selected_area.geometryType()

if geom_type == QgsWkbTypes.PointGeometry:
    # Layher holds points. Generate circular search areas around the points.
    print("This layer holds Points. Generating circular search areas around the points.")
    search_area = generate_search_areas_layer_around_points_from_points_layer(points=selected_area, radius=search_circle_diameter/2, layer=None, segments=36)

elif geom_type == QgsWkbTypes.PolygonGeometry:
    search_area = selected_area
    print("This layer holds Polygons. Will use the polygons as search areas.")
# elif geom_type == QgsWkbTypes.LineGeometry:
#     print("This layer holds Lines.")
# elif geom_type == QgsWkbTypes.NoGeometry:
#     print("This layer has no geometry (e.g., attribute-only table).")
else:
    print(f"Unknown geometry type: {geom_type}")

# Select the layer to analyze
analyzing_layer = select_layer_from_available_layers(title="Select a Layer to Analyze", prompt="Choose a layer to analyze:")
if analyzing_layer is None:
    print("No layer selected. Exiting.")

print(f"Selected layer: {analyzing_layer.name()}")

# Select the field on wich to select wanted features
layer_fields = [field.name() for field in analyzing_layer.fields()] + ['Geometry']
selected_field, selected_field_index = select_item_from_gui_list(
    items=layer_fields,
    prompt="Choose a field to filter features:",
    title="Select Field"
)

# Select the features to filter on the selected field
selected_features = run_selection_dialog_column_values(analyzing_layer, selected_field)
if not selected_features:
    print("No features selected. Exiting.")


print(f"Selected features: {selected_features}")
