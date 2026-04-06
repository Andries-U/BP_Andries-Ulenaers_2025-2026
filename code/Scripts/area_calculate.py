from qgis.core import QgsVectorLayer, QgsFeatureRequest, QgsRectangle
from qgis.utils import iface

# ⚙️ CONFIGURE
layer_name = "us_emf_stortpl.lb72 — us_emf_stortpl"  # ← Replace with your layer name

# Get the layer
names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
print(names)
layer = QgsProject.instance().mapLayersByName(layer_name)[0]

if not layer:
    print(f"Layer '{layer_name}' not found.")
else:
    # Get current canvas extent (viewport bbox)
    canvas = iface.mapCanvas()
    bbox = canvas.extent()
    
    # Create request with bbox filter
    request = QgsFeatureRequest().setFilterRect(bbox)

    areas = []
    for feature in layer.getFeatures(request):
        print(feature)
        geom = feature.geometry()
        if geom.isGeosValid():
            area = geom.area()
            attributes = {field.name(): feature[field.name()] for field in layer.fields()}
            areas.append((area, feature.id(), geom, attributes))
    # Sort by area descending
    areas.sort(reverse=True)

    print(f"Polygons in current viewport: {len(areas)}")
    print("-" * 50)
    print(areas[0])
    #for area, fid, geom in areas[0]:
    #    print(f"Feature ID: {fid}, Area: {area:.2f} units²")
    
    
    if areas:  # Check if any features were found
        biggest_area, biggest_fid, biggest_geom, biggest_attrs = areas[0]
        print(f"✅ Highlighting biggest parcel: Feature ID {biggest_fid}, Area: {biggest_area:.2f} units²")

        # Get the layer
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]

        # Select only this feature
        layer.selectByIds([biggest_fid])

        # Get current renderer
        renderer = layer.renderer()

        # Create a new "Selection" renderer (shows selected features with custom style)
        from qgis.core import QgsFeatureRenderer, QgsSingleSymbolRenderer, QgsFillSymbol, QgsSymbol

        # Create a blue fill symbol
        blue_symbol = QgsFillSymbol.createSimple({
            'color': '0,0,255,100',      # Blue with 40% opacity (RGB + alpha)
            'outline_color': '0,0,255',   # Blue outline
            'outline_width': '1.5'
        })

        # Create a selection renderer
        selection_renderer = QgsSingleSymbolRenderer(blue_symbol)

        # Apply it temporarily
        layer.setRenderer(selection_renderer)
        layer.triggerRepaint()

        # Optional: Zoom to it
        canvas = iface.mapCanvas()
        canvas.zoomToSelected(layer)
        canvas.refresh()

        print("🔵 Highlighted in blue! (Style reset after closing QGIS or re-running script)")
    else:
        print("⚠️ No features found in current view.")