# Load the layer by name
layer = QgsProject.instance().mapLayersByName("ET_MLT Configuration")[0]

# Create a new memory layer to store points
points_layer = QgsVectorLayer("Point?crs=" + layer.crs().authid(), "Extracted Points", "memory")
provider = points_layer.dataProvider()

# Add a field to store the polygon ID
provider.addAttributes([QgsField("polygon_id", QVariant.Int)])
points_layer.updateFields()

# Start editing mode once
points_layer.startEditing()

# Extract vertices and add them to the points layer
for feature in layer.getFeatures():
    geom = feature.geometry()
    polygon_id = feature.id()  # Get the polygon's ID
    for part in geom.parts():
        for point in part.points():
            new_point = QgsFeature()
            new_point.setGeometry(QgsGeometry.fromPoint(point))
            new_point.setAttributes([polygon_id])
            provider.addFeature(new_point)

# Commit changes once
points_layer.commitChanges()

# Add the points layer to the project
QgsProject.instance().addMapLayer(points_layer)

# Print features for verification
for feature in points_layer.getFeatures():
    print(f"Point: {feature.geometry().asPoint()}, Polygon ID: {feature['polygon_id']}")