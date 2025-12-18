from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

def export_pdf(df, mis_n, mis_e, precision, comp_name, surveyor_info, project_notes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # Branding Header
    elements.append(Paragraph(f"<b>{comp_name.upper()}</b>", styles['Title']))
    elements.append(Paragraph(f"Official Survey Report - {surveyor_info}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Project Notes Section
    if project_notes:
        elements.append(Paragraph("<b>Project Notes:</b>", styles['Normal']))
        elements.append(Paragraph(project_notes, styles['Normal']))
        elements.append(Spacer(1, 12))

    # Misclosure Summary Table
    summary_data = [
        ["Total Linear Misclosure:", f"{((mis_n**2 + mis_e**2)**0.5):.4f} m", "Precision Ratio:", f"1 : {int(precision)}"],
        ["Misclosure North:", f"{mis_n:.4f} m", "Misclosure East:", f"{mis_e:.4f} m"]
    ]
    summary_table = Table(summary_data, colWidths=[150, 100, 150, 100])
    summary_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 9)]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Detailed Workings
    data = [["ID", "Dist", "Bearing", "Northing Calculation", "Result N", "Easting Calculation", "Result E"]]
    for _, row in df.iterrows():
        data.append([
            row['code'], f"{row['Distance']:.2f}", f"{row['Bearing']:.2f}",
            row['Math_N'], f"{row['Final_N']:.3f}", 
            row['Math_E'], f"{row['Final_E']:.3f}"
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(table)
    
    doc.build(elements)
    return buffer.getvalue()
