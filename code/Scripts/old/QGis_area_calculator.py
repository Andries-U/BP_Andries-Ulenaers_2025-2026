def calculate_area(polygon: qgis.core.QgsGeometry) -> int:
    geom = polygon.geometry()
    
    if geom.isGeosValid():
        area = geom.area()
        return area

