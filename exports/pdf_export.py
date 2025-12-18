from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import os

def export_pdf(df, mis_n, mis_e, precision, comp_name, surveyor_info, project_notes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # 1. Add Logo if it exists
    logo_path = "logo.png" 
    if os.path.exists(logo_path):
        img = Image(logo_path, width=60, height=60)
        img.hAlign = 'CENTER'
        elements.append(img)
        elements.append(Spacer(1, 10))

    # 2. Branded Header
    elements.append(Paragraph(f"<b>{comp_name.upper()}</b>", styles['Title']))
    elements.append(Paragraph(f"Prepared by: {surveyor_info}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # 3. Project Notes
    if project_notes:
        elements.append(Paragraph("<b>Site Notes:</b>", styles['Normal']))
        elements.append(Paragraph(project_notes, styles['Normal']))
        elements.append(Spacer(1, 12))

    # 4. Accuracy Summary
    summary_data = [
        ["Total Length", "Precision", "Misclosure North", "Misclosure East"],
        [f"{df['Distance'].sum():.2f}m", f"1:{int(precision)}", f"{mis_n:.4f}m", f"{mis_e:.4f}m"]
    ]
    summary_table = Table(summary_data, colWidths=[100, 100, 120, 120])
    summary_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # 5. The "Workings" Table (The math proof)
    data = [["Point ID", "Distance", "Bearing", "Northing Math", "Final N", "Easting Math", "Final E"]]
    for _, row in df.iterrows():
        data.append([
            str(row['code']), f"{row['Distance']:.2f}", f"{row['Bearing']:.2f}",
            str(row['Math_N']), f"{row['Final_N']:.3f}", 
            str(row['Math_E']), f"{row['Final_E']:.3f}"
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(table)
    
    doc.build(elements)
    return buffer.getvalue()
