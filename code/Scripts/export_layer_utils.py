from qgis.core import QgsProject, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutPoint, QgsPrintLayout, QgsLayoutExporter, QgsVectorLayer, QgsCoordinateTransformContext, QgsVectorFileWriter, QgsTextFormat, QgsVectorLayer, QgsMapRendererParallelJob,QgsMapSettings, QgsVectorLayer, QgsFillSymbol
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QImage

import os
import tempfile
import csv
import locale
from collections import Counter
from typing import Optional, Dict, List


 
try:
    from reportlab.lib.pagesizes import A4, landscape, portrait
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        Table, TableStyle, Image, KeepTogether,
    )
except ImportError:
    raise ImportError(
        "ReportLab is not installed.\n"
        "Run:  pip install reportlab\n"
        "(in the OSGeo4W Shell or the shell that launched QGIS)"
    )

def export_layer_to_pdf(layer: QgsVectorLayer, output_pdf_path: str, cardinality_threshold_value: int = 50, cardinality_ratio_threshold: float = 0.5):
    """
    Exports a QGIS layer to a PDF using a plain text table (most compatible).
    """
    project = QgsProject.instance()

    # determine the columns to include based on cardinality thresholds
    field_names = [f.name() for f in layer.fields()]
    fields_to_include = []
    total_count = layer.featureCount()
    cardinality_threshold = min(cardinality_threshold_value, int(total_count * cardinality_ratio_threshold))
    for field in layer.fields():
        if field.typeName() in ("geometry", "unknown"):
            continue 
        if _has_low_cardinality(layer, field.name(), threshold=cardinality_threshold):
            fields_to_include.append(field.name())

    # Create a new layout
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(f"Export_{layer.name()}")

    # --- 1. Add Map ---
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(10, 10, 180, 100)
    map_item.setExtent(layer.extent())
    layout.addLayoutItem(map_item)

    # --- 2. Add Title ---
    title = QgsLayoutItemLabel(layout)
    title.setText(f"Layer: {layer.name()}")
    
    text_format = QgsTextFormat()
    text_format.setSize(16)
    title.setTextFormat(text_format)
    
    title.adjustSizeToText()
    title.attemptMove(QgsLayoutPoint(10, 5))
    layout.addLayoutItem(title)

    # --- 3. Build Plain Text Table ---
    # Calculate column widths dynamically
    col_widths = [max(len(f), 10) for f in fields_to_include]
    
    # Header
    header = " | ".join([f"{name:<{w}}" for name, w in zip(fields_to_include, col_widths)])
    separator = "-+-".join(["-" * w for w in col_widths])
    
    rows = []
    rows.append(header)
    rows.append(separator)
    
    for feature in layer.getFeatures():
        row_vals = []
        for field in fields_to_include:
            val = feature[field]
            # Convert None to string
            val_str = str(val) if val is not None else "NULL"
            row_vals.append(f"{val_str:<{col_widths[fields_to_include.index(field)]}}")
        
        rows.append(" | ".join(row_vals))
    
    # Join with newlines
    text_content = "\n".join(rows)

    # --- 4. Add Label with Text ---
    label_item = QgsLayoutItemLabel(layout)
    label_item.setText(text_content)
    
    # Set font to monospace for alignment
    text_format = QgsTextFormat()
    text_format.setFontFamily("Courier New")
    text_format.setSize(8)
    label_item.setTextFormat(text_format)
    
    # Set position and size (adjust height if needed)
    label_item.setRect(10, 120, 180, 100)
    
    # Add to layout
    layout.addLayoutItem(label_item)

    # --- 5. Export ---
    exporter = QgsLayoutExporter(layout)
    exporter.exportToPdf(output_pdf_path, QgsLayoutExporter.PdfExportSettings())

    print(f"Layer '{layer.name()}' exported to {output_pdf_path}")

def export_layer_to_csv(layer: QgsVectorLayer, output_path: str):
    """
    Export a vector layer to CSV format with locale-aware formatting.
    Exports two versions:
    1. Standard format: comma-separated with dot decimal point (for most regions)
    2. EU Excel format: semicolon-separated with comma decimal point (for European regions)

    Args:
        layer (QgsVectorLayer): The vector layer to export.
        output_path (str): The file path where the standard CSV will be saved.
                          EU version will be saved with '_EU' suffix.
    
    Raises:
        ValueError: If layer is invalid or empty.
        RuntimeError: If export fails.
    """
    if layer is None or layer.featureCount() == 0:
        raise ValueError("The provided layer is invalid. It must be a non-empty vector layer.")
    
    # Export standard CSV (comma-separated, dot decimal)
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "CSV"
    options.fileEncoding = "UTF-8"
    
    error = QgsVectorFileWriter.writeAsVectorFormatV2(layer, output_path, QgsCoordinateTransformContext(), options)
    
    if error[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"Failed to export layer to CSV: {error[1]}")
    
    # # Export EU-compatible CSV (semicolon-separated, comma decimal)
    # eu_output_path = output_path.replace(".csv", "_EU.csv") if output_path.endswith(".csv") else output_path + "_EU.csv"
    # _export_layer_to_csv_eu_format(layer, eu_output_path)


# def _export_layer_to_csv_eu_format(layer: QgsVectorLayer, output_path: str):
#     """
#     Export a vector layer to EU-compatible CSV format.
#     Uses semicolon as field separator and comma as decimal point (Excel-compatible for EU regions).

#     Args:
#         layer (QgsVectorLayer): The vector layer to export.
#         output_path (str): The file path where the EU CSV will be saved.
    
#     Raises:
#         ValueError: If layer is invalid or empty.
#         IOError: If file writing fails.
#     """
#     if layer is None or layer.featureCount() == 0:
#         raise ValueError("The provided layer is invalid. It must be a non-empty vector layer.")
    
#     try:
#         with open(output_path, 'w', encoding='UTF-8', newline='') as csvfile:
#             # Write header
#             field_names = [f.name() for f in layer.fields()]
#             csvfile.write(';'.join(field_names) + '\n')
            
#             # Write feature data
#             for feature in layer.getFeatures():
#                 row_values = []
#                 for field_name in field_names:
#                     val = feature[field_name]
                    
#                     # Convert value to string and format decimal points
#                     if val is None:
#                         val_str = ""
#                     elif isinstance(val, float):
#                         # Replace dot with comma for decimal point (EU format)
#                         val_str = f"{val:.10f}".rstrip('0').rstrip('.').replace('.', ',')
#                     else:
#                         val_str = str(val)
                    
#                     # Escape quotes and wrap in quotes if contains semicolon
#                     if ';' in val_str or '"' in val_str or '\n' in val_str:
#                         val_str = '"' + val_str.replace('"', '""') + '"'
                    
#                     row_values.append(val_str)
                
#                 csvfile.write(';'.join(row_values) + '\n')
    
#     except IOError as e:
#         raise IOError(f"Failed to write EU format CSV to {output_path}: {e}")  

def _render_map_image(layer: QgsVectorLayer, map_px: int = 1200, fill_color: QColor = QColor(255,69,0)) -> str:
    """
    Renders the layer to a temporary PNG image.
    Returns the path to the image.
    """
    print("[Render] Rendering map to PNG...")
    map_image_path = None

    # 2. Als een kleur is opgegeven, pas de symboliek van de laag aan
    if fill_color is not None:
        print(f"[Render] Overwriting layer style with color: {fill_color.name()}")
        
        # Maak een nieuwe vulsymbool met de opgegeven kleur
        # De kleur wordt gebruikt voor de vulling (fill)
        symbol = QgsFillSymbol.createSimple({
            'color': fill_color.name(),
            'style': 'solid'
        })
        
        # Pas het symbool toe op de laag
        layer.renderer().setSymbol(symbol)
        
        # Optioneel: Zet de randkleur (outline) ook aan (bijv. zwart)
        # symbol.setColorOutline(QColor(0, 0, 0)) 
        # layer.renderer().setSymbol(symbol)
        
        # **Belangrijk**: Als de laag een "Categorized" of "Graduated" renderer heeft,
        # moet u die eerst resetten of overriden. De bovenstaande code forceert een "Simple Fill".
        # Als u de originele categorisering wilt behouden maar de kleur wilt aanpassen,
        # moet u de logica complexer maken (zie optie 2 hieronder).


    try:
        settings = QgsMapSettings()
        settings.setLayers([layer])
        settings.setExtent(layer.extent())
        settings.setOutputSize(QSize(map_px, map_px))
        settings.setBackgroundColor(QColor(255, 255, 255))

        job = QgsMapRendererParallelJob(settings)
        job.start()
        job.waitForFinished()

        img: QImage = job.renderedImage()
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        img.save(tmp.name, "PNG")
        map_image_path = tmp.name
        print(f"[Render] Map saved to {map_image_path}")
    except Exception as exc:
        print(f"[Render] Map render failed: {exc}")
        map_image_path = None
    
    return map_image_path

def _build_pdf(
    layer: QgsVectorLayer, 
    output_path: str, 
    title: str, 
    total_count: int, 
    stats_data: Dict, 
    area_data: Dict, 
    field_total_areas: Dict,
    included_fields: List[str],
    skipped_fields: List[str],
    map_image_path: Optional[str],
    cardinality_threshold_value: int, 
    cardinality_ratio_threshold: float,
    filtered_column: Optional[str] = None,
    included_values: Optional[List[str]] = None
) -> str:
    """
    Constructs the PDF document using the filtered data.
    """
    print(f"[PDF] Building report → {output_path}")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=portrait(A4),
        leftMargin=0.8 * cm, rightMargin=0.8 * cm,
        topMargin=0.8 * cm, bottomMargin=0.8 * cm,
        title=title,
    )

    page_w, page_h = portrait(A4)
    usable_w = page_w - 3 * cm

    styles = getSampleStyleSheet()

    s_title = ParagraphStyle("T", parent=styles["Title"], fontSize=14, spaceAfter=4, textColor=colors.HexColor("#1a1a2e"))
    s_sub = ParagraphStyle("S", parent=styles["Normal"], fontSize=8, spaceAfter=6, textColor=colors.HexColor("#555555"))
    s_field = ParagraphStyle("F", parent=styles["Heading2"], fontSize=9, spaceBefore=6, spaceAfter=2, textColor=colors.HexColor("#1a1a2e"))
    s_uniq = ParagraphStyle("U", parent=s_field, textColor=colors.HexColor("#888888"), fontName="Helvetica-Oblique")
    s_note = ParagraphStyle("N", parent=styles["Normal"], fontSize=7, fontName="Helvetica-Oblique", textColor=colors.HexColor("#888888"))

    story = []

    # Title & Summary
    story.append(Paragraph(title, s_title))
    story.append(Paragraph(
        f"Total Features: <b>{total_count:,}</b> &nbsp;|&nbsp; "
        f"Fields Analysed: <b>{len(stats_data)}</b> &nbsp;|&nbsp; "
        f"Fields Displayed: <b>{len(included_fields)}</b>",
        s_sub,
    ))

    # Note about skipped fields
    if skipped_fields:
        skipped_count = len(skipped_fields)
        story.append(Paragraph(
            f"<b>Note:</b> {skipped_count} field(s) were skipped because they had too many unique values "
            f"(Threshold: >{cardinality_ratio_threshold * 100:.0f}% ratio OR >= {cardinality_threshold_value} distinct values).",
            s_note
        ))
        story.append(Spacer(1, 4))

    # Note about filtered column (if applicable)
    if filtered_column and included_values is not None:
        story.append(Paragraph(
            f"<b>Note:</b> Analysis was filtered on column '<b>{filtered_column}</b>' only including <b>{len(included_values)}</b> value(s).\nValues included: {', '.join(included_values)}",
            s_note
        ))
        story.append(Spacer(1, 4))

    # Map Image
    if map_image_path and os.path.exists(map_image_path):
        max_h = (page_h - 3 * cm) * 0.35
        draw_size = min(usable_w, max_h)
        story.append(Image(map_image_path, width=draw_size, height=draw_size))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Extent: {layer.extent().toString(4)}", s_note))
        story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("(Map image could not be rendered.)", s_note))
        story.append(Spacer(1, 4))

    # Column widths
    col_w = [usable_w * p for p in (0.30, 0.12, 0.13, 0.23, 0.22)]
    
    # Base Table Styles
    HEADER_BG = colors.HexColor("#1a1a2e")
    ROW_ODD = colors.HexColor("#f7f7f7")
    ROW_EVEN = colors.white
    UNIQUE_BG = colors.HexColor("#eeeeee")
    GREY_TEXT = colors.HexColor("#888888")

    # Common table style configuration
    base_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]

    for field_name in included_fields:
        counts = stats_data[field_name]
        areas = area_data[field_name]
        total_area = field_total_areas[field_name]
        unique_count = len(counts)
        
        is_unique = unique_count == total_count

        # Heading
        if is_unique:
            heading = Paragraph(
                f'{field_name} <font size="8" color="#888888">(Unique Identifier)</font>',
                s_uniq,
            )
        else:
            heading = Paragraph(field_name, s_field)

        # Build rows
        rows = [["Distinct Value", "Count", "Count %", "Total Area", "Area %"]]
        
        # Sort by total area descending
        sorted_items = sorted(counts.items(), key=lambda x: areas.get(x[0], 0.0), reverse=True)
        
        for i, (val, cnt) in enumerate(sorted_items):
            ri = i + 1  # Row index (1-based for table)
            a = areas.get(val, 0.0)
            rows.append([
                val,
                f"{cnt:,}",
                f"{cnt / total_count * 100:.2f}%" if total_count else "0.00%",
                f"{a:,.2f}",
                f"{a / total_area * 100:.2f}%" if total_area else "0.00%",
            ])

        # Create Table Style dynamically to match row count
        # We start with base styles
        current_style = list(base_style)
        
        if is_unique:
            # Style for unique fields (grey text, grey background)
            for r_idx, (val, cnt) in enumerate(sorted_items):
                ri = r_idx + 1
                current_style.append(("BACKGROUND", (0, ri), (-1, ri), UNIQUE_BG))
                current_style.append(("TEXTCOLOR", (0, ri), (-1, ri), GREY_TEXT))
        else:
            # Style for normal fields (zebra striping)
            for r_idx, (val, cnt) in enumerate(sorted_items):
                ri = r_idx + 1
                bg = ROW_ODD if r_idx % 2 == 0 else ROW_EVEN
                current_style.append(("BACKGROUND", (0, ri), (-1, ri), bg))

        tbl = Table(rows, colWidths=col_w, repeatRows=1)
        tbl.setStyle(TableStyle(current_style))
        story.append(KeepTogether([heading, tbl]))

    doc.build(story)
    
    # Cleanup map image if it was created inside this function
    if map_image_path and os.path.exists(map_image_path):
        # Note: In the full flow, we might want to keep the image if passed from outside,
        # but here we assume we manage it. If the caller manages it, they should handle cleanup.
        # However, to avoid double deletion if the caller did it, we check if it's still there.
        # In the main function flow, we will handle cleanup there.
        pass 

    print(f"[PDF] Done → {output_path}")
    return output_path

def generate_layer_statistics_to_pdf_full_analysis(
    layer: QgsVectorLayer,
    output_path: Optional[str] = None,
    map_px: int = 1200,
    area_field: Optional[str] = None,
    cardinality_threshold_value: int = 200, 
    cardinality_ratio_threshold: float = 0.3
) -> str:
    """
    Main function: Collects stats, filters fields, renders map, and builds PDF.
    Performs full analysis on all fields without pre-filtering.
    """
    if not layer or not layer.isValid():
        raise ValueError("Layer is invalid or not a vector layer.")

    output_path = output_path or os.path.join(
        tempfile.gettempdir(), f"{layer.name()}_statistics_full.pdf"
    )
    title = f"Statistics Report – {layer.name()}"
    total_count = layer.featureCount()

    if total_count == 0:
        raise ValueError("Layer has no features.")


    # ── 1. Collect Statistics ─────────────────────────────────────────────────
    print(f"[stats_pdf] Scanning {total_count:,} features …")
    stats_data = {}
    area_data = {}
    field_total_areas = {}

    # cardinality_threshold = cardinality_threshold_value if total_count * cardinality_ratio_threshold > cardinality_threshold_value else int(total_count * cardinality_ratio_threshold)
    features = list(layer.getFeatures())

    for field in layer.fields():
        field_name = field.name()
        if field.typeName() in ("geometry", "unknown"):
            continue
        
        categorical = _has_low_cardinality(layer, field_name)
        counts = Counter()
        areas = Counter()
        field_total_area = 0.0

        for feature in features:
            val = feature[field_name]
            key = "NULL" if val is None else str(val)
            counts[key] += 1
            geom = feature.geometry()
            if geom and not geom.isEmpty():
                area = geom.area()
                areas[key] += area
                field_total_area += area

        stats_data[field_name] = dict(counts)
        area_data[field_name] = dict(areas)
        field_total_areas[field_name] = field_total_area
        print(f"  '{field_name}': {len(counts)} distinct values")

    # ── 2. Filter Fields ───────────────────────────────────────────────────────
    included_fields = []
    skipped_fields = []
    total_count = layer.featureCount()
    cardinality_threshold = min(cardinality_threshold_value, int(total_count * cardinality_ratio_threshold))
    for field in layer.fields():
        if field.typeName() in ("geometry", "unknown"):
            continue 
        if _has_low_cardinality(layer, field.name(), threshold=cardinality_threshold):
            included_fields.append(field.name())
        else:
            skipped_fields.append(field.name())

    # ── 3. Render Map ──────────────────────────────────────────────────────────
    map_image_path = _render_map_image(layer, map_px, fill_color=QColor(255,69,0))

    # ── 4. Build PDF ───────────────────────────────────────────────────────────
    output_path = _build_pdf(
        layer, 
        output_path, 
        title, 
        total_count, 
        stats_data, 
        area_data, 
        field_total_areas,
        included_fields,
        skipped_fields,
        map_image_path,
        cardinality_threshold_value, 
        cardinality_ratio_threshold
    )

    # Cleanup
    if map_image_path and os.path.exists(map_image_path):
        try:
            os.remove(map_image_path)
        except OSError:
            pass

    print(f"[stats_pdf] Done → {output_path}")
    return output_path

def generate_layer_statistics_to_pdf_partial_analysis(
    layer: QgsVectorLayer,
    output_path: Optional[str] = None,
    map_px: int = 1200,
    area_field: Optional[str] = None,
    filtered_column: str = None,
    included_values: Optional[List[str]] = None,
    cardinality_threshold_value: int = 100, 
    cardinality_ratio_threshold: float = 0.2
) -> str:
    """
    Partial analysis version: Collects stats, filters fields, renders map, and builds PDF.
    Uses more lenient thresholds than full analysis since data is already filtered.
    """
    if not layer or not layer.isValid():
        raise ValueError("Layer is invalid or not a vector layer.")

    output_path = output_path or os.path.join(
        tempfile.gettempdir(), f"{layer.name()}_statistics_partial.pdf"
    )
    title = f"Statistics Report – {layer.name()}"
    total_count = layer.featureCount()

    if total_count == 0:
        raise ValueError("Layer has no features.")

    # ── 1. Collect Statistics ─────────────────────────────────────────────────
    print(f"[stats_pdf_partial] Scanning {total_count:,} features …")
    stats_data = {}
    area_data = {}
    field_total_areas = {}

    features = list(layer.getFeatures())

    for field in layer.fields():
        field_name = field.name()
        if field.typeName() in ("geometry", "unknown"):
            continue
        
        categorical = _has_low_cardinality(layer, field_name)
        counts = Counter()
        areas = Counter()
        field_total_area = 0.0

        for feature in features:
            val = feature[field_name]
            key = "NULL" if val is None else str(val)
            counts[key] += 1
            geom = feature.geometry()
            if geom and not geom.isEmpty():
                area = geom.area()
                areas[key] += area
                field_total_area += area

        stats_data[field_name] = dict(counts)
        area_data[field_name] = dict(areas)
        field_total_areas[field_name] = field_total_area
        print(f"  '{field_name}': {len(counts)} distinct values")

    # ── 2. Filter Fields ───────────────────────────────────────────────────────
    included_fields = []
    skipped_fields = []
    total_count = layer.featureCount()
    cardinality_threshold = min(cardinality_threshold_value, int(total_count * cardinality_ratio_threshold))
    for field in layer.fields():
        if field.typeName() in ("geometry", "unknown"):
            continue 
        if _has_low_cardinality(layer, field.name(), threshold=cardinality_threshold):
            included_fields.append(field.name())
        else:
            skipped_fields.append(field.name())

    # ── 3. Render Map ──────────────────────────────────────────────────────────
    map_image_path = _render_map_image(layer, map_px, fill_color=QColor(0, 71, 171))

    # ── 4. Build PDF ───────────────────────────────────────────────────────────
    output_path = _build_pdf(
        layer, 
        output_path, 
        title, 
        total_count, 
        stats_data, 
        area_data, 
        field_total_areas,
        included_fields,
        skipped_fields,
        map_image_path,
        cardinality_threshold_value, 
        cardinality_ratio_threshold,
        filtered_column,
        included_values
    )

    # Cleanup
    if map_image_path and os.path.exists(map_image_path):
        try:
            os.remove(map_image_path)
        except OSError:
            pass

    print(f"[stats_pdf_partial] Done → {output_path}")
    return output_path



def _has_low_cardinality(layer: QgsVectorLayer, field_name: str, threshold: int = 10) -> bool:
    if not layer or not layer.isValid():
        raise ValueError("Layer is invalid or not a vector layer.")

    if field_name not in [f.name() for f in layer.fields()]:
        raise ValueError(f"Field '{field_name}' does not exist in the layer.")

    # Use QGIS's built-in method to fetch unique values
    unique_values = layer.uniqueValues(layer.fields().indexFromName(field_name))
    return len(unique_values) <= threshold