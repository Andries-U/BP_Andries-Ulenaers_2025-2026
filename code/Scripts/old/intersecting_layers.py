from qgis.core import (
    QgsVectorLayer, QgsFeatureRequest, QgsVectorFileWriter, QgsVectorLayerUtils,
    QgsVectorDataProvider, QgsFeature, QgsVectorLayer, QgsMapLayer, QgsSingleSymbolRenderer
)

#Config 
perceel_layer_name = "Administratieve_percelen_limburg"
exclusion_layer_name = "Exclusion_layer"

# print the count of the features of a valid layer
def print_count_layer(layer: QgsMapLayer):
    if layer.isValid():
        count = layer.featureCount()
        print(f"✅ {layer.name()}: {count} features")
    else:
        print(f"❌ Layer '{layer.name()}' is invalid")

# Create a new memory layer with the same schema
def make_empty_copy_of_layer_in_memory(copy_layer_name: str, source_layer: QgsVectorLayer):
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
    
# Get layers by name
percelen_layer = QgsProject.instance().mapLayersByName(perceel_layer_name)[0]
exclusion_layer = QgsProject.instance().mapLayersByName(exclusion_layer_name)[0]

# Create three memory layers with same schema as percelen (to hold the subsets of percelen)
layer_within = make_empty_copy_of_layer_in_memory("percelen_within", percelen_layer)
layer_intersecting = make_empty_copy_of_layer_in_memory("percelen_intersecting", percelen_layer)
layer_outside = make_empty_copy_of_layer_in_memory("percelen_outside", percelen_layer)

# Get all exclusion zone geometries as a union for faster processing
exclusion_union = QgsGeometry.unaryUnion([f.geometry() for f in exclusion_layer.getFeatures()])

# Create a request that only fetches features intersecting the current view
canvas = iface.mapCanvas()
extent = canvas.extent()
request = QgsFeatureRequest().setFilterRect(extent)

# Process each parcel
for parcel in percelen_layer.getFeatures(request):
    geom = parcel.geometry()
    
    new_feat = QgsFeature()
    new_feat.setGeometry(parcel.geometry())
    new_feat.setAttributes(parcel.attributes())
    
    if exclusion_union.contains(geom):
        layer_within.startEditing()
        # Fully within exclusion zone
        layer_within.addFeature(new_feat)
        layer_within.commitChanges()
    elif exclusion_union.intersects(geom):
        layer_intersecting.startEditing()
        # Partially intersecting (but not fully contained)
        layer_intersecting.addFeature(new_feat)
        layer_intersecting.commitChanges()
    else:
        # Not intersecting at all
        layer_outside.startEditing()
        layer_outside.addFeature(new_feat)
        layer_outside.commitChanges()

# Commit changes
print(f"✅ percelen_within: {layer_within.featureCount()} features")
print(f"✅ percelen_intersecting: {layer_intersecting.featureCount()} features")
print(f"✅ percelen_outside: {layer_outside.featureCount()} features")

# Add layers to project
QgsProject.instance().addMapLayer(layer_within)
QgsProject.instance().addMapLayer(layer_intersecting)
QgsProject.instance().addMapLayer(layer_outside)

# Define color styles
def set_layer_color(layer, color_hex):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(QColor(color_hex))
    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)
    layer.triggerRepaint()

# Apply colors
set_layer_color(layer_within, "#00FF00")        # Green
set_layer_color(layer_intersecting, "#FFA500")   # Orange
set_layer_color(layer_outside, "#FF0000")       # Red



# Optional: turn off original layer
QgsProject.instance().layerTreeRoot().findLayer(percelen_layer.id()).setItemVisibilityChecked(False)

root = QgsProject.instance().layerTreeRoot()
mytreelayer = root.findLayer(exclusion_layer.id())
root.insertChildNode(0,mytreelayer.clone())
root.removeChildNode(mytreelayer)

exclusion_layer.setOpacity(0.5)
exclusion_layer.triggerRepaint()

print("✅ Three new layers created. Original 'percelen' layer turned off.")

