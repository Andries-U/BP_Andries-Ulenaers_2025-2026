from andries_utils import select_layer_from_available_cui, select_feature_from_layer_database, select_item_from_gui_list
from reset_module_cache import reload_all_custom_modules

reload_all_custom_modules()

selected_layer = select_layer_from_available_cui("Select a layer to analyze:")
if selected_layer is None:
    print("No layer selected. Exiting.") 
print(f"Selected layer: {selected_layer.name()}")

layer_fields = [field.name() for field in selected_layer.fields()] + ['Geometry']
selected_field, selected_field_index = select_item_from_gui_list(
    items=layer_fields,
    prompt="Select a field from the layer:",
    title="Select a Field"
)

selected_feature, selected_feature_id = select_feature_from_layer_database(selected_layer, "Select a feature from the layer:", "Select a Feature")
if selected_feature_id is None:
    print("No feature selected. Exiting.") 

print(f"selected feature: {selected_feature}")
if selected_field == 'Geometry':
    geom = selected_layer.getFeature(selected_feature_id).geometry()
    print_info = f"Geometry type: {geom.type()}, WKT: {geom.asWkt()}"
else:    
    print_info = selected_feature.attribute(selected_field)
print(f"The data from the selected field '{selected_field}'")
print(f"for the selected feature ID {selected_feature_id} is:")
print(f"({print_info})")