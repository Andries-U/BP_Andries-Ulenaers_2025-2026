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

def generate_layer_statistics_to_pdf(
    layer: QgsVectorLayer,
    output_path: Optional[str] = None,
    map_px: int = 1200,
) -> str:
    """
    Collect field statistics for `layer` and write a PDF report.
 
    Parameters
    ----------
    layer       : QgsVectorLayer  – the layer to analyse
    output_path : str | None      – destination path for the PDF;
                                    defaults to a temp file
    map_px      : int             – pixel size of the rendered map image
 
    Returns
    -------
    str  – path to the generated PDF
    """
    if not layer or not layer.isValid():
        raise ValueError("Layer is invalid or not a vector layer.")
 
    output_path = output_path or os.path.join(
        tempfile.gettempdir(), f"{layer.name()}_statistics.pdf"
    )
    title = f"Statistics Report – {layer.name()}"
    total_count = layer.featureCount()
 
    # ── 1. Collect statistics ─────────────────────────────────────────────────
    print(f"[stats_pdf] Scanning {total_count:,} features …")
    stats_data = {}        # field -> {value: count}
    area_data = {}         # field -> {value: area}
    field_total_areas = {} # field -> float
 
    features = list(layer.getFeatures())
 
    for field in layer.fields():
        field_name = field.name()
        if field.typeName() in ("geometry", "unknown"):
            continue
 
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
 
    # ── 2. Render map to a temp PNG ───────────────────────────────────────────
    print("[stats_pdf] Rendering map …")
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
    except Exception as exc:
        print(f"[stats_pdf] Map render failed: {exc}")
 
    # ── 3. Build PDF ──────────────────────────────────────────────────────────
    print(f"[stats_pdf] Writing PDF → {output_path}")
 
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm,  bottomMargin=1.5 * cm,
        title=title,
    )
 
    page_w, page_h = landscape(A4)
    usable_w = page_w - 3 * cm  # left + right margins
 
    styles = getSampleStyleSheet()
 
    s_title = ParagraphStyle("T", parent=styles["Title"],
                             fontSize=18, spaceAfter=6,
                             textColor=colors.HexColor("#1a1a2e"))
    s_sub   = ParagraphStyle("S", parent=styles["Normal"],
                             fontSize=10, spaceAfter=12,
                             textColor=colors.HexColor("#555555"))
    s_field = ParagraphStyle("F", parent=styles["Heading2"],
                             fontSize=11, spaceBefore=14, spaceAfter=4,
                             textColor=colors.HexColor("#1a1a2e"))
    s_uniq  = ParagraphStyle("U", parent=s_field,
                             textColor=colors.HexColor("#888888"),
                             fontName="Helvetica-Oblique")
    s_note  = ParagraphStyle("N", parent=styles["Normal"],
                             fontSize=8, fontName="Helvetica-Oblique",
                             textColor=colors.HexColor("#888888"))
 
    story = []
 
    # Title & summary
    story.append(Paragraph(title, s_title))
    story.append(Paragraph(
        f"Total Features: <b>{total_count:,}</b> &nbsp;|&nbsp; "
        f"Fields Analysed: <b>{len(stats_data)}</b>",
        s_sub,
    ))
 
    # Map image
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
 
    HEADER_BG = colors.HexColor("#1a1a2e")
    ROW_ODD   = colors.HexColor("#f7f7f7")
    ROW_EVEN  = colors.white
    UNIQUE_BG = colors.HexColor("#eeeeee")
    GREY_TEXT = colors.HexColor("#888888")
 
    base_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE",   (0, 1), (-1, -1), 8),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN",      (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN",      (0, 1), (0,  -1), "LEFT"),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]
 
    for field_name, counts in stats_data.items():
        is_unique = all(c <= 1 for c in counts.values())
        areas = area_data[field_name]
        total_area = field_total_areas[field_name]
 
        if is_unique:
            heading = Paragraph(
                f'{field_name} <font size="8" color="#888888">(Unique Identifier)</font>',
                s_uniq,
            )
        else:
            heading = Paragraph(field_name, s_field)
 
        rows = [["Distinct Value", "Count", "Count %", "Total Area", "Area %"]]
        extra = []
 
        for i, (val, cnt) in enumerate(sorted(counts.items(), key=lambda x: x[1], reverse=True)):
            ri = i + 1
            a = areas.get(val, 0.0)
            rows.append([
                val,
                f"{cnt:,}",
                f"{cnt / total_count * 100:.2f}%" if total_count else "0.00%",
                f"{a:,.2f}",
                f"{a / total_area * 100:.2f}%" if total_area else "0.00%",
            ])
            bg = UNIQUE_BG if is_unique else (ROW_ODD if i % 2 == 0 else ROW_EVEN)
            extra.append(("BACKGROUND", (0, ri), (-1, ri), bg))
            if is_unique:
                extra.append(("TEXTCOLOR", (0, ri), (-1, ri), GREY_TEXT))
 
        tbl = Table(rows, colWidths=col_w, repeatRows=1)
        tbl.setStyle(TableStyle(base_style + extra))
        story.append(KeepTogether([heading, tbl]))
 
    doc.build(story)
 
    # Cleanup temp map image
    if map_image_path and os.path.exists(map_image_path):
        os.remove(map_image_path)
 
    print(f"[stats_pdf] Done → {output_path}")
    return output_path

