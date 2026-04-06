from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsSymbol, QgsRendererSingleSymbol
import random

# Get the source layer
perceel_layer_name = "Administratieve_percelen_limburg"
source_layer = QgsProject.instance().mapLayersByName(perceel_layer_name)[0]

test_layer = QgsVectorLayer("Point?crs=epsg:4326&field=id:integer&field=name:string(20)&index=yes", "test_written_uri", "memory")

# Create a new memory layer with the same schema
def make_empty_copy_of_layer(copy_layer_name: str, source_layer: QgsVectorLayer):
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

# Create a test layer
test_layer = give_empty_copy_of_layer("test_layer_3_features", source_layer)


# Create a request that only fetches features intersecting the current view
canvas = iface.mapCanvas()
extent = canvas.extent()
request = QgsFeatureRequest().setFilterRect(extent)
# Get 3 random features from the source layer
features = list(source_layer.getFeatures(request))
random_features = random.sample(features, min(3, len(features)))

# Add the 3 features to the test layer
test_layer.startEditing()
for feature in random_features:
    new_feat = QgsFeature()
    new_feat.setGeometry(feature.geometry())
    new_feat.setAttributes(feature.attributes())
    print(new_feat)
    print(test_layer.dataProvider().addFeature(new_feat))
    test_layer.commitChanges()
test_layer.commitChanges()

# Add the test layer to the project
QgsProject.instance().addMapLayer(test_layer)

# Define color styles
def set_layer_color(layer, color_hex):
    print(layer)
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(QColor(color_hex))
    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    
set_layer_color(test_layer, "#00FF00")
