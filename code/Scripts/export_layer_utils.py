from qgis.core import QgsProject, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemHtml, QgsLayoutSize, QgsLayoutPoint, QgsPrintLayout, QgsLayoutExporter, QgsVectorLayer, QgsCoordinateTransformContext, QgsVectorFileWriter, QgsUnitTypes, QgsTextFormat,     QgsVectorLayer, QgsMapRendererParallelJob,QgsMapSettings, QgsRectangle
from qgis.PyQt.QtCore import QSize

import os
import tempfile
from collections import Counter
from typing import Optional

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QImage
 
try:
    from reportlab.lib.pagesizes import A4, landscape
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

def export_layer_to_pdf(layer: QgsVectorLayer, output_pdf_path: str):
    """
    Exports a QGIS layer to a PDF using a plain text table (most compatible).
    """
    project = QgsProject.instance()

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
    field_names = [f.name() for f in layer.fields()]
    col_widths = [max(len(f), 10) for f in field_names]
    
    # Header
    header = " | ".join([f"{name:<{w}}" for name, w in zip(field_names, col_widths)])
    separator = "-+-".join(["-" * w for w in col_widths])
    
    rows = []
    rows.append(header)
    rows.append(separator)
    
    for feature in layer.getFeatures():
        row_vals = []
        for field in layer.fields():
            val = feature[field.name()]
            # Convert None to string
            val_str = str(val) if val is not None else "NULL"
            row_vals.append(f"{val_str:<{col_widths[layer.fields().index(field)]}}")
        
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
    Export a vector layer to CSV format.

    Args:
        layer (QgsVectorLayer): The vector layer to export.
        output_path (str): The file path where the CSV will be saved.
    """
    if layer is None or layer.featureCount() == 0:
        raise ValueError("The provided layer is invalid. It must be a non-empty vector layer.")
    
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "CSV"
    options.fileEncoding = "UTF-8"
    
    error = QgsVectorFileWriter.writeAsVectorFormatV2(layer, output_path, QgsCoordinateTransformContext(), options)
    
    if error[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"Failed to export layer to CSV: {error[1]}")  

def _filter_fields(layer: QgsVectorLayer, stats_data: Dict, area_data: Dict, field_total_areas: Dict, total_count: int) -> List[str]:
    """
    Filter fields based on uniqueness thresholds.
    Returns a list of field names that should be included in the report.
    """
    included_fields = []
    skipped_fields = []
    
    # Thresholds (can be made parameters if needed, but kept local for this split)
    min_unique_ratio = 0.95  # Skip if >95% of rows are unique
    max_unique_count = 10    # Skip if unique values <= 10 (absolute count)

    print("[Filter] Analyzing fields for uniqueness...")
    
    for field_name in stats_data.keys():
        counts = stats_data[field_name]
        unique_count = len(counts)
        ratio = unique_count / total_count if total_count > 0 else 1.0
        
        # Logic: Skip if (ratio > threshold) OR (unique_count <= absolute_limit)
        # Note: We use `>` for ratio and `<=` for count.
        # If unique_count == total_count, ratio is 1.0 (100%), which is > 0.95.
        skip_field = (ratio > min_unique_ratio) or (unique_count <= max_unique_count)
        
        if not skip_field:
            included_fields.append(field_name)
            print(f"  -> Keep '{field_name}' (Ratio: {ratio:.2%}, Count: {unique_count})")
        else:
            skipped_fields.append(field_name)
            print(f"  -> Skip '{field_name}' (Ratio: {ratio:.2%}, Count: {unique_count})")

    if not included_fields:
        print("[Filter] Warning: No fields met the uniqueness criteria.")
    
    return included_fields, skipped_fields

def _render_map_image(layer: QgsVectorLayer, map_px: int = 1200) -> str:
    """
    Renders the layer to a temporary PNG image.
    Returns the path to the image.
    """
    print("[Render] Rendering map to PNG...")
    map_image_path = None
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
    map_image_path: Optional[str]
) -> str:
    """
    Constructs the PDF document using the filtered data.
    """
    print(f"[PDF] Building report → {output_path}")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title=title,
    )

    page_w, page_h = landscape(A4)
    usable_w = page_w - 3 * cm

    styles = getSampleStyleSheet()

    s_title = ParagraphStyle("T", parent=styles["Title"], fontSize=18, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
    s_sub = ParagraphStyle("S", parent=styles["Normal"], fontSize=10, spaceAfter=12, textColor=colors.HexColor("#555555"))
    s_field = ParagraphStyle("F", parent=styles["Heading2"], fontSize=11, spaceBefore=14, spaceAfter=4, textColor=colors.HexColor("#1a1a2e"))
    s_uniq = ParagraphStyle("U", parent=s_field, textColor=colors.HexColor("#888888"), fontName="Helvetica-Oblique")
    s_note = ParagraphStyle("N", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Oblique", textColor=colors.HexColor("#888888"))

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
            f"(Threshold: >95% ratio OR <= 10 distinct values).",
            s_note
        ))
        story.append(Spacer(1, 10))

    # Map Image
    if map_image_path and os.path.exists(map_image_path):
        max_h = (page_h - 3 * cm) * 0.45
        draw_size = min(usable_w, max_h)
        story.append(Image(map_image_path, width=draw_size, height=draw_size))
        story.append(Paragraph(f"Extent: {layer.extent().toString(4)}", s_note))
        story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("(Map image could not be rendered.)", s_note))
        story.append(Spacer(1, 10))

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
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
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
        
        # Sort by count descending
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
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

def generate_layer_statistics_to_pdf(
    layer: QgsVectorLayer,
    output_path: Optional[str] = None,
    map_px: int = 1200,
) -> str:
    """
    Main function: Collects stats, filters fields, renders map, and builds PDF.
    """
    if not layer or not layer.isValid():
        raise ValueError("Layer is invalid or not a vector layer.")

    output_path = output_path or os.path.join(
        tempfile.gettempdir(), f"{layer.name()}_statistics.pdf"
    )
    title = f"Statistics Report – {layer.name()}"
    total_count = layer.featureCount()

    if total_count == 0:
        raise ValueError("Layer has no features.")
    
    # filter fields based on uniqueness thresholds and prepare data for the report
    

    # ── 1. Collect Statistics ─────────────────────────────────────────────────
    print(f"[stats_pdf] Scanning {total_count:,} features …")
    stats_data = {}
    area_data = {}
    field_total_areas = {}

    features = list(layer.getFeatures())

    for field in layer.fields():
        field_name = field.name()
        if field.typeName() in ("geometry", "unknown"):
            continue
        
        categorical = 
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
    included_fields, skipped_fields = _filter_fields(
        layer, stats_data, area_data, field_total_areas, total_count
    )

    # ── 3. Render Map ──────────────────────────────────────────────────────────
    map_image_path = _render_map_image(layer, map_px)

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
        map_image_path
    )

    # Cleanup
    if map_image_path and os.path.exists(map_image_path):
        try:
            os.remove(map_image_path)
        except OSError:
            pass

    print(f"[stats_pdf] Done → {output_path}")
    return output_path

