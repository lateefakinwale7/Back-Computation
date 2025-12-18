from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

def export_pdf(df, mis_n, mis_e, precision, comp_name, surveyor_info, project_notes):
    buffer = io.BytesIO()
    # Landscape orientation to fit all calculation columns
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # 1. Generic Header (Specific branding removed)
    elements.append(Paragraph("<b>SURVEY COMPUTATION REPORT</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # 2. Project Details (Shows only the site notes provided in the sidebar)
    if project_notes:
        elements.append(Paragraph("<b>Project Description & Notes:</b>", styles['Normal']))
        elements.append(Paragraph(project_notes, styles['Normal']))
        elements.append(Spacer(1, 12))

    # 3. Accuracy Summary Table
    summary_data = [
        ["Total Linear Misclosure:", f"{((mis_n**2 + mis_e**2)**0.5):.4f} m", "Precision Ratio:", f"1 : {int(precision)}"],
        ["Misclosure North (eN):", f"{mis_n:.4f} m", "Misclosure East (eE):", f"{mis_e:.4f} m"]
    ]
    summary_table = Table(summary_data, colWidths=[150, 100, 150, 100])
    summary_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # 4. Detailed Calculations Table
    data = [["Point ID", "Dist", "Bearing", "Northing Calculation (Math)", "Final N", "Easting Calculation (Math)", "Final E"]]
    
    for _, row in df.iterrows():
        data.append([
            str(row['code']), 
            f"{row['Distance']:.2f}", 
            f"{row['Bearing']:.2f}",
            str(row['Math_N']), 
            f"{row['Final_N']:.3f}", 
            str(row['Math_E']), 
            f"{row['Final_E']:.3f}"
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    return buffer.getvalue()
