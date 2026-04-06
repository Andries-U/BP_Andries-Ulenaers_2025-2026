from reset_module_cache import reload_all_custom_modules
from generate_docs import generate_docs_for_custom_modules
from qgis_gui_utils import run_selection_dialog_column_values, select_item_from_gui_list, select_layer_from_available_layers
from qgis.core import QgsProject

reload_all_custom_modules()

CUSTOM_MODULES = ['calculation_utils', 'qgis_gui_utils', 'pvgis_client', 'SolarDataClient', "generate_docs", "reset_module_cache", "test", "exceptions", "multiselect_dialog"]
coverage_factor_solar_fields = 0.8  # Assuming 80% of the area can be covered with solar panels.
search_circle_diameter = 5000  # Diameter of the search circle around the corner points of the ET in meters.
features_added = 0

# Generate documentation for custom modules
generate_docs_for_custom_modules(CUSTOM_MODULES)

# Select the search area layer
search_area = select_layer_from_available_layers(title="Select Search Area Layer", prompt="Choose the layer that defines the search area:")

# Make temp group for processing and empty it if it already exists
temp_group_name = "Temp_Group_For_Processing"
root = QgsProject.instance().layerTreeRoot()
temp_group = root.findGroup(temp_group_name)
if temp_group is None:
    temp_group = root.addGroup(temp_group_name)
else :
    temp_group.removeAllChildren()

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
selected_features = run_selection_dialog(analyzing_layer, selected_field)
if not selected_features:
    print("No features selected. Exiting.")


print(f"Selected features: {selected_features}")
