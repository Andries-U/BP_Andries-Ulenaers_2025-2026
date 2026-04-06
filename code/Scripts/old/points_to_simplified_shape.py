from qgis.core import QgsVectorLayer, QgsFeatureRequest, QgsGeometry, QgsPointXY

# Replace 'your_point_layer_name' with the actual name of your point layer
layer = QgsProject.instance().mapLayersByName('Extracted Points')[0]

# —— CONFIGURATION ——
TOLERANCE = 1e-6  # Adjust this if needed for your data precision

# Get all points
features = [f for f in layer.getFeatures()]
points = [f.geometry().asPoint() for f in features]



def print_all_from_enumerable(enumerable):
    for entry in enumerable:
        print(entry)

def is_point_on_segment(startPoint, endPoint, testPoint, tolerance=1e-6):
    """
    Check if point C lies on the line segment AB, within a given tolerance.

    Args:
        a, b: QgsPointXY — endpoints of the segment
        c: QgsPointXY — point to test
        tolerance: float — maximum allowed deviation (default 1e-6)

    Returns:
        bool: True if C is on segment AB within tolerance
    """
    crossproduct = (testPoint.y() - startPoint.y()) * (endPoint.x() - startPoint.x()) - (testPoint.x() - startPoint.x()) * (endPoint.y() - startPoint.y())

    # compare versus epsilon for floating point values, or != 0 if using integers
    if abs(crossproduct) > tolerance:
        print("point not on same line")
        return False

    dotproduct = (testPoint.x() - startPoint.x()) * (endPoint.x() - startPoint.x()) + (testPoint.y() - startPoint.y())*(endPoint.y() - startPoint.y())
    if dotproduct < 0:
        return False

    squaredlengthba = (endPoint.x() - startPoint.x())*(endPoint.x() - startPoint.x()) + (endPoint.y() - startPoint.y())*(endPoint.y() - startPoint.y())
    if dotproduct > squaredlengthba:
        return False

    return True


def is_point_on_segment_using_distance(startPoint, endPoint, testPoint, tolerance=1e-6):
    print(f"Startpoint: {startPoint}\nEndpoint: {endPoint}")
    combined_distances_to_testpoint = startPoint.distance(testPoint) + endPoint.distance(testPoint)
    test_line_distance = startPoint.distance(endPoint)
    discrepency_in_distances = combined_distances_to_testpoint - test_line_distance
    
    print(f"combined: {combined_distances_to_testpoint}\nLine distance: {test_line_distance}\nDiscrepency: {discrepency_in_distances}\nTolerance: {tolerance}")
    
    print("*"*50)
    print("\n")
    if abs(discrepency_in_distances) > tolerance:
        return False
    
def find_corners_of_triangle(points):
    lowest_x = lowest_y = highest_x = highest_y = points[0]
    
    for point in points:
        if point.x() > highest_x.x():
            highest_x = point
        if point.x() < lowest_x.x():
            lowest_x = point
        if point.y() > highest_y.y():
            highest_y = point
        if point.y() < lowest_y.y():
            lowest_y = point
    
    corners = {lowest_x, lowest_y, highest_x, highest_y}
    
    return corners
    
    
# Find points that are NOT on any segment between two other points
remaining_points = find_corners_of_triangle(points)  # Copy




print("remaining_points")
print_all_from_enumerable(remaining_points)



# Optional: Create a new memory layer with corner points
vl = QgsVectorLayer("Point?crs=" + layer.crs().authid(), "triangle_corners", "memory")
pr = vl.dataProvider()
pr.addAttributes([QgsField("id", QVariant.Int)])
vl.updateFields()

for idx, pt in enumerate(remaining_points):
    feat = QgsFeature()
    feat.setGeometry(QgsGeometry.fromPointXY(pt))
    feat.setAttributes([idx + 1])
    pr.addFeature(feat)

QgsProject.instance().addMapLayer(vl)