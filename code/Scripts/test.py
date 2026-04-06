import pydoc
from qgis.utils import iface
from pvgis_client import PVGISClient
from andries_utils import get_bbox_from_current_canvas, select_layer_from_available_cui, copy_layer_to_temp, make_empty_copy_of_vector_layer, get_centroid_of_polygon, add_column_to_layer, check_equality_of_layer_crs_to_wanted_crs
from qgis.core import QgsField, QgsFields, QgsFeatureRequest, QgsProject, QgsVectorLayer, QgsFeature, QgsExpression, QgsGeometry
from PyQt5.QtCore import QVariant
from reset_module_cache import reload_all_custom_modules

CUSTOM_MODULES = ['andries_utils', 'pvgis_client', 'SolarDataClient']
coverage_factor_solar_fields = 0.8  # Assuming 80% of the area can be covered with solar panels.
search_circle_diameter = 5000  # Diameter of the search circle around the corner points of the ET in meters.
features_added = 0

# Setup
for each in CUSTOM_MODULES:
    pydoc.writedoc(each)

reload_all_custom_modules()

# Get the root of the layer tree
root = QgsProject.instance().layerTreeRoot()

# Name of the group to check/create
group_name = "Temp"

# Find the group if it exists
temp_group = root.findGroup(group_name)

if temp_group is None:
    # Group does not exist, create it
    temp_group = root.insertGroup(0, group_name)
    print(f"Created group: {group_name}")
else:
    # Group exists, remove all layers from it
    temp_group.removeAllChildren()
    print(f"Cleared all layers from group: {group_name}")

if temp_group:
    # Set the selection in the layer tree view
    iface.layerTreeView().setCurrentNode(temp_group)

# Get the project instance and print the name of the project.
project = QgsProject.instance()
print(f"Project name: {project.fileName()}")

# Create circles around the corner points of the ET
# Create a new layer for circles around points  
points_layer = select_layer_from_available_cui(title="Select Points Layer", prompt="Choose the layer that contains the corner points:")
circles_layer = QgsVectorLayer(
        f"Polygon?crs={points_layer.crs().authid()}",
        points_layer.name() + "_circles_memory",
        "memory"
    )

circles_layer.startEditing()
circles_layer.dataProvider().addAttributes(points_layer.fields())
circles_layer.updateFields()
circles_layer.commitChanges()

project.addMapLayer(circles_layer)  

# Define the circle diameter in meters

circles_layer.startEditing()
for feature in points_layer.getFeatures():
    geometry = feature.geometry()
    if geometry is not None and geometry.isMultipart() == False:
        point = geometry.asPoint()
        # Create a circle (buffer) around the point
        circle_geometry = geometry.buffer(search_circle_diameter / 2, 32)
        new_feature = QgsFeature()
        new_feature.setGeometry(circle_geometry)
        new_feature.setAttributes(feature.attributes())
        circles_layer.dataProvider().addFeature(new_feature)

circles_layer.commitChanges()
print(f"Circle layer created with {circles_layer.featureCount()} circles")

# Select the layer to work with
parcel_layer = select_layer_from_available_cui(title="Select a Parcel Layer", prompt="Choose the parcel layer to analyze:")

# Create a temporary layer with the same schema as the selected layer
temp_layer = make_empty_copy_of_vector_layer(f"{parcel_layer.name()}_temp2", parcel_layer)
project.addMapLayer(temp_layer)
print(f"Temporary layer created: {temp_layer.name()}")

# Add new fields to store the results
within_circles_field, within_circles_field_index = add_column_to_layer(temp_layer, "within_circles", QVariant.String)
intersects_circles_field, intersects_circles_field_index = add_column_to_layer(temp_layer, "intersects_circles", QVariant.String)

# Add features within the view from the selected layer to the temporary layer
#print("Adding features within the current view to the temporary layer...")
#request = QgsFeatureRequest().setFilterRect(get_bbox_from_current_canvas())
# 
print("Adding features that intersect or are within the circles to the temporary layer...")

# Get all exclusion zone geometries as a union for faster processing
search_area_union = QgsGeometry.unaryUnion([f.geometry() for f in circles_layer.getFeatures()])

# Check if the CRS of the parcel layer matches the CRS of the circles layer
check_equality_of_layer_crs_to_wanted_crs([parcel_layer, circles_layer], project.crs())

temp_layer.startEditing()
for parcel in parcel_layer.getFeatures():
    if parcel.geometry() is None:
        continue
    parcel_geom = parcel.geometry()

    new_feat = QgsFeature()
    new_feat.setGeometry(parcel_geom)
    new_feat.setAttributes(parcel.attributes())
    add_feature = False
    if search_area_union.contains(parcel_geom):
        add_feature = True
        within_circles = [str(f.id()) for f in circles_layer.getFeatures() if f.geometry().contains(parcel_geom)]
        intersects_circles = []
    elif search_area_union.intersects(parcel_geom):
        add_feature = True
        within_circles = []
        intersects_circles = [str(f.id()) for f in circles_layer.getFeatures() if f.geometry().intersects(parcel_geom)]
    if add_feature:
        temp_layer.dataProvider().addFeature(new_feat)
        new_feat.setAttribute(within_circles_field_index, ','.join((within_circles)))
        new_feat.setAttribute(intersects_circles_field_index, ','.join(intersects_circles))
        features_added += 1

temp_layer.commitChanges()
print(f"Features added to the temporary layer: {features_added}")

# Calculate area for each feature and update the new "area" field
print("Calculating area for each feature.")
area_field_name = "area"
area_field, area_field_index = add_column_to_layer(temp_layer, area_field_name, QVariant.Double)
temp_layer.startEditing()

features_added = 0
for feature in temp_layer.getFeatures():
    geometry = feature.geometry()
    if geometry is not None:
        area = geometry.area()  # Returns area in the layer's CRS units
        temp_layer.changeAttributeValue(feature.id(), area_field_index, area)
        features_added += 1

temp_layer.commitChanges()
print(f"Area calculation completed and updated in the 'area' field. Features processed: {features_added}")

# Calculate the centroid for each feature and update the new "centroid" field

print("Calculating centroid for each feature and updating the 'centroid_x' and 'centroid_y' fields...")
centroid_x_field, centroid_x_field_index = add_column_to_layer(temp_layer, "centroid_x", QVariant.Double)
centroid_y_field, centroid_y_field_index = add_column_to_layer(temp_layer, "centroid_y", QVariant.Double)

temp_layer.startEditing()
features_added = 0
for feature in temp_layer.getFeatures():
    geometry = feature.geometry()
    if geometry is not None:
        centroid = get_centroid_of_polygon(geometry)  # Get centroid as QPointF
        temp_layer.changeAttributeValue(feature.id(), centroid_x_field_index, centroid.x())
        temp_layer.changeAttributeValue(feature.id(), centroid_y_field_index, centroid.y())
        features_added += 1

temp_layer.commitChanges()
print(f"Centroid calculation completed and updated in the 'centroid_x' and 'centroid_y' fields. Features processed: {features_added}.")

# Make a SolarDataClient instance.
pvClientInstance = PVGISClient(peakpower=0.24, slope=15.0, aspect=0.0, losses=15.0)

# Calculate the total yearly solar potential for each feature (per square meter and for the whole feature) and update the new fields."
print("Calculating solar potential at centroid for each feature and updating the 'solar_potential_at_centroid' field...")

total_yearly_solar_potential_field_name = "total_yearly_solar_potential_feature"
total_yearly_solar_potential_per_square_meter_field_name = "total_yearly_solar_potential_per_square_meter_feature"

total_yearly_solar_potential_field, total_yearly_solar_potential_field_index = add_column_to_layer(temp_layer, total_yearly_solar_potential_field_name, QVariant.Double)
total_yearly_solar_potential_per_square_meter_field, total_yearly_solar_potential_per_square_meter_field_index = add_column_to_layer(temp_layer, total_yearly_solar_potential_per_square_meter_field_name, QVariant.Double)

temp_layer.startEditing()
features_added = 0
for feature in temp_layer.getFeatures():
    centroid_x = feature[centroid_x_field.name()]  # Get the centroid from the attribute
    centroid_y = feature[centroid_y_field.name()]
    area = feature[area_field.name()]
    if centroid_x is not None and centroid_y is not None and area is not None:
        solar_potential_per_square_meter_at_centroid = pvClientInstance.get_yearly_total_solar_potential(lat=centroid_y, lon=centroid_x, src_crs=temp_layer.crs())

        total_solar_potential = area * solar_potential_per_square_meter_at_centroid*coverage_factor_solar_fields

        temp_layer.changeAttributeValue(feature.id(), total_yearly_solar_potential_per_square_meter_field_index, solar_potential_per_square_meter_at_centroid)
        temp_layer.changeAttributeValue(feature.id(), total_yearly_solar_potential_field_index, total_solar_potential)
        features_added += 1

temp_layer.commitChanges()
print(f"Solar potential calculation completed and updated in the 'yearly_solar_potential_per_square_meter_at_centroid' field. Features processed: {features_added}")

# calculate the average daily solar production (per square meter and the whole feature) for each feature.
print("Calculating average daily solar potential (whole field and per square meter) for each feature")

average_daily_solar_potential_per_square_meter_field_name = "average_daily_solar_potential_per_square_meter_at_centroid"
average_daily_solar_potential_field_name = "average_daily_solar_potential_field"

temp_layer.startEditing()
average_daily_solar_potential_per_square_meter_field_name, average_daily_solar_potential_per_square_meter_field_index = add_column_to_layer(temp_layer, average_daily_solar_potential_per_square_meter_field_name, QVariant.Double)
average_daily_solar_potential_field, average_daily_solar_potential_field_index = add_column_to_layer(temp_layer, average_daily_solar_potential_field_name, QVariant.Double)

temp_layer.startEditing()
features_added = 0 
for feature in temp_layer.getFeatures():
    centroid_x = feature[centroid_x_field.name()]  # Get the centroid from the attribute
    centroid_y = feature[centroid_y_field.name()]
    area = feature[area_field.name()]
    if centroid_x is not None and centroid_y is not None and area is not None:
        average_daily_solar_potential_per_square_meter = pvClientInstance.get_average_daily_solar_potential(lat=centroid_y, lon=centroid_x, src_crs=temp_layer.crs())
        average_daily_solar_potential_field_value = average_daily_solar_potential_per_square_meter * area * coverage_factor_solar_fields

        print(f"Feature ID {feature.id()}: Average daily solar potential per square meter at centroid: {average_daily_solar_potential_per_square_meter} kwh/square meter for area {area} square meters")
        print(f"Feature ID {feature.id()}: Average daily solar potential for the whole field: {average_daily_solar_potential_field_value} kwh for area {area} square meters")
        print(f"average_daily_solar_potential_per_square_meter index: {average_daily_solar_potential_per_square_meter_field_index}, average_daily_solar_potential_field index: {average_daily_solar_potential_field_index}")

        temp_layer.changeAttributeValue(feature.id(), average_daily_solar_potential_per_square_meter_field_index, average_daily_solar_potential_per_square_meter)
        temp_layer.changeAttributeValue(feature.id(), average_daily_solar_potential_field_index, average_daily_solar_potential_field_value)

        features_added += 1

temp_layer.commitChanges()
print(f"Average daily solar potential calculation completed. Features processed: {features_added}")



# Calculate the combined yearly solar potential, daily average solar potential and area for all features and print the result
total_yearly_solar_potential = 0.0
total_area = 0.0
total_average_daily_solar_potential = 0.0

for feature in temp_layer.getFeatures():
    # Add the average daily solar potential for this feature to the total
    average_daily_solar_potential_field_value = feature[average_daily_solar_potential_field.name()]
    if average_daily_solar_potential_field_value is not None:
        total_average_daily_solar_potential += average_daily_solar_potential_field_value
    # Add the yearly solar potential for this feature to the total
    total_solar_potential = feature[total_yearly_solar_potential_field.name()]
    if total_solar_potential is not None:
        total_yearly_solar_potential += total_solar_potential
    # Add the area for this feature to the total area
    area = feature[area_field.name()]
    if area is not None:
        total_area += area


# Print the results in a human-readable format, converting units where appropriate.
print('*'*50)
# Area
if total_area < 10000:
    print(f"Total area of all features: {total_area} square meters")
elif total_area < 10000000:
    print(f"Total area of all features: {total_area/10000:.2f} hectares")
else:
    print(f"Total area of all features: {total_area/1000000:.2f} square kilometers")

# Yearly solar potential
if total_yearly_solar_potential < 100:
    print(f"Combined yearly solar potential for all features: {total_yearly_solar_potential} kwh")
elif total_yearly_solar_potential < 10000:
    print(f"Combined yearly solar potential for all features: {total_yearly_solar_potential/100:.2f} mWh")
else:    
    print(f"Combined yearly solar potential for all features: {total_yearly_solar_potential/1000000:.2f} GWh")

print(f"Average yearly solar potential per square meter across all features: {total_yearly_solar_potential/total_area if total_area > 0 else 'N/A'} kwh/square meter")

# Average daily solar potential
if total_average_daily_solar_potential < 100:
    print(f"Combined average daily solar potential for all features: {total_average_daily_solar_potential} kwh")
elif total_average_daily_solar_potential < 10000:
    print(f"Combined average daily solar potential for all features: {total_average_daily_solar_potential/100:.2f} mWh")
else:    
    print(f"Combined average daily solar potential for all features: {total_average_daily_solar_potential/1000000:.2f} GWh")
average_daily_solar_potential_field_value = total_average_daily_solar_potential/total_area if total_area > 0 else 'N/A'
print(f"Average daily solar potential per square meter across all features: {average_daily_solar_potential_field_value} kwh/square meter")

print('*'*50)

# Add the temporary layer to the project
project.addMapLayer(temp_layer)
