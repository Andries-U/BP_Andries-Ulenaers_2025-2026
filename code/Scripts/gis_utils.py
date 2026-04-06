from qgis.core import QgsGeometry, QgsPointXY

def get_polygon_centroid(polygon_geom: QgsGeometry) -> QgsPointXY:
    """
    Bereken het meetkundig middenpunt (centroïde) van een QGIS polygon geometrie.
    
    Args:
        polygon_geom (QgsGeometry): Het geometry object van de polygon.
                                    Bijv: feature.geometry()
    
    Returns:
        QgsPointXY: Het middenpunt (X, Y).
                    Geeft None terug als de geometrie ongeldig of leeg is.
    
    Voorbeeld gebruik:
        # feature = layer.getFeature(1)
        # punt = get_polygon_centroid(feature.geometry())
        # print(f"X: {punt.x()}, Y: {punt.y()}")
    """
    
    # 1. Validatie: Check op lege of ongeldige geometrie
    if polygon_geom.isNull() or polygon_geom.isEmpty():
        raise ValueError("De aangeleverde geometrie is leeg of null.")

    # 2. Bereken het centroïde
    # .centroid() geeft weer een QgsGeometry object terug (van het type Point)
    centroid_geom = polygon_geom.centroid()
    
    # 3. Extraheer het punt object
    if centroid_geom.isEmpty():
        raise ValueError("Kon geen centroïde berekenen voor deze geometrie.")
        
    return centroid_geom.asPoint()