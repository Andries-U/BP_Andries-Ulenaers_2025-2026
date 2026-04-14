from reset_module_cache import reload_all_custom_modules
from generate_docs import generate_docs_for_custom_modules
from qgis_gui_utils import run_selection_dialog_column_values, select_item_from_gui_list, select_layer_from_available_layers,get_user_input_dialog, show_error_popup
from calculation_utils import generate_search_areas_layer_around_points_from_points_layer, split_layer_by_search_areas, check_equality_of_layer_crs_to_wanted_crs, split_layer_by_search_areas_processing
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer, QgsWkbTypes, QgsLayerTreeGroup
from qgis.utils import iface
from action_selector_dialog import ActionSelectorDialog, ActionMap
from layer_statistics_dialog import LayerStatisticsDialog
from PyQt5.QtWidgets import QDialog

MY_MODULES = [
    'reset_module_cache',
    'calculation_utils', 
    'gis_utils',
    'qgis_gui_utils', 
    'pvgis_client', 
    'SolarDataClient', 
    "generate_docs",
    "exceptions", 
    "multiselect_dialog",
    "item_selection",
    "action_selector_dialog",
    "layer_statistics_dialog"
]
TEMP_GROUP_NAME = "Temp_Group_For_Processing"
coverage_factor_solar_fields = 0.8  # Assuming 80% of the area can be covered with solar panels.
default_search_circle_diameter = 5000  # Diameter of the search circle around the corner points of the ET in meters.
features_added = 0

def prepare_temporary_group(group_name: str) -> QgsLayerTreeGroup:
    root = QgsProject.instance().layerTreeRoot()
    temp_group = root.findGroup(group_name)
    if temp_group is None:
        temp_group = root.addGroup(group_name)
    else:
        temp_group.removeAllChildren()
    return temp_group

def select_group_layer(group_name: str) -> None:
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found.")
    iface.layerTreeView().setCurrentNode(group)

# Reload all custom modules to ensure the latest code is used
reload_all_custom_modules()

# Generate documentation for custom modules
generate_docs_for_custom_modules(MY_MODULES)

# Make temp group for processing and empty it if it already exists
temp_group = prepare_temporary_group(TEMP_GROUP_NAME)

# Get the project instance and print the name of the project.
project = QgsProject.instance()
print(f"Project name: {project.fileName()}")

def run_layer_analysis():
    selected_area = select_layer_from_available_layers(title="Select the analysis layer", prompt="Select the layer you want to analyze:")

    if not selected_area:
        print("No layer selected. Please select a vector layer in the QGIS Layers panel.")
        return

    # 2. Open the dialog
    dialog = LayerStatisticsDialog(selected_area, parent=iface.mainWindow())
    dialog.exec_()

def run_size_analysis():
    selected_area = select_layer_from_available_layers(title="Select the analysis layer", prompt="Select the layer you want to analyze inside the search area:")

    search_area_layer = select_layer_from_available_layers(title="Select the search area layer", prompt="Select the layer that defines the search area:")

    if search_area_layer.geometryType() == QgsWkbTypes.PointGeometry:
        print("This layer holds Points. Generating circular search areas around the points.")
        search_area_radius = get_user_input_dialog(title="Search Area Size", prompt="Enter the radius of the search area in meters:", default_value=default_search_circle_diameter)
        try:
            search_area_radius = float(search_area_radius)
        except ValueError:
            search_area_radius = default_search_circle_diameter
            print("Error: Please enter a valid number.")
        search_area_layer = generate_search_areas_layer_around_points_from_points_layer(points=search_area_layer, radius=search_area_radius, layer=None, segments=36)

    if not check_equality_of_layer_crs_to_wanted_crs([search_area_layer], iface.mapCanvas().mapSettings().destinationCrs()):
        print("CRS of the search area layer does not match the CRS of the map canvas. Please reproject the layer to the correct CRS and try again.")
        show_error_popup("CRS Mismatch", "The CRS of the search area layer does not match the CRS of the map canvas. Please reproject the layer to the correct CRS and try again.")
        return

    layer_within, layer_intersecting, layer_outside = split_layer_by_search_areas_processing(selected_area, search_area_layer)
    
    search_area_layer.updateFields()
    search_area_layer.commitChanges()



    select_group_layer(TEMP_GROUP_NAME)
    if search_area_layer is not None:
        project.addMapLayer(search_area_layer)
    if layer_within is not None:
        project.addMapLayer(layer_within)
        layer_within.setName(f"{selected_area.name()} - Within Search Area")
    if layer_intersecting is not None:
        project.addMapLayer(layer_intersecting)
        layer_intersecting.setName(f"{selected_area.name()} - Intersecting Search Area")
    if layer_outside is not None:
        project.addMapLayer(layer_outside)

    dialog = LayerStatisticsDialog(layer_within, parent=iface.mainWindow(), title="Features Within Search Area")
    dialog.exec_()

    dialog2 = LayerStatisticsDialog(layer_intersecting, parent=iface.mainWindow(), title="Features Intersecting Search Area")
    dialog2.exec_()

def run_solar_potential():
    print("Analyzing solar potential...")
    # TODO: Implement solar potential analysis logic


def main():
    # 1. Define your dynamic actions
    # The value can be a function (if no extra params needed) 
    # or a tuple/dict (if you need to pass parameters like 'search_area')
    
    actions: ActionMap = {
        "Analyze Layer Options": run_layer_analysis,
        "Analyze Size (Search Area)": run_size_analysis,
        "Analyze Solar Potential": run_solar_potential,
    }

    # 2. Instantiate and run
    dialog = ActionSelectorDialog(action_map=actions)
    
    if dialog.exec_() == QDialog.Accepted:
        selected_func_or_data = dialog.selected_action
        selected_label = dialog.selected_label
        
        print(f"User selected: {selected_label}")
        
        # 3. Execute the logic
        if callable(selected_func_or_data):
            # Case A: It's a direct function
            # If the function requires arguments (like 'layer'), pass them here
            # selected_func_or_data(current_layer) 
            selected_func_or_data() 
            
        elif isinstance(selected_func_or_data, tuple):
            # Case B: It's a tuple (Function, Arguments)
            func, *args = selected_func_or_data
            # Execute with the arguments
            # func(current_layer, *args)
            print(f"Executing {func.__name__} with args: {args}")
            
        elif isinstance(selected_func_or_data, dict):
            # Case C: It's a configuration dict
            print(f"Executing action with config: {selected_func_or_data}")
            # logic_based_on_config(selected_func_or_data)

    else:
        print("Operation cancelled.")

def old_main():
    # Select the search area layer
    selected_area = select_layer_from_available_layers(title="Select Search Area Layer", prompt="Choose the layer that defines the search area:")

    # decide action based on the geometry type of the selected layer
    geom_type = selected_area.geometryType()

    if geom_type == QgsWkbTypes.PointGeometry:
        # Layher holds points. Generate circular search areas around the points.
        print("This layer holds Points. Generating circular search areas around the points.")
        search_area = generate_search_areas_layer_around_points_from_points_layer(points=selected_area, radius=default_search_circle_diameter/2, layer=None, segments=36)

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

main()