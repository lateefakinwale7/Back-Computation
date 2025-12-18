from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

def export_pdf(df, mis_n, mis_e, precision):
    buffer = io.BytesIO()
    # Use landscape to fit all the "Workings" columns
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # Title and Summary
    elements.append(Paragraph("Survey Back-Computation Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    summary_data = [
        ["Misclosure North:", f"{mis_n:.4f} m"],
        ["Misclosure East:", f"{mis_e:.4f} m"],
        ["Precision Ratio:", f"1 : {int(precision)}"]
    ]
    summary_table = Table(summary_data, hAlign='LEFT')
    elements.append(summary_table)
    elements.append(Spacer(1, 24))

    # Workings Table
    # Selecting key columns for the report
    data = [["Dist", "Bearing", "Lat(ΔN)", "Dep(ΔE)", "Corr_N", "Corr_E", "Final_N", "Final_E"]]
    
    for _, row in df.iterrows():
        data.append([
            f"{row['Distance']:.2f}",
            f"{row['Bearing']:.2f}",
            f"{row['Lat (ΔN)']:.3f}",
            f"{row['Dep (ΔE)']:.3f}",
            f"{row['Corr_Lat']:.4f}",
            f"{row['Corr_Dep']:.4f}",
            f"{row['Final_N']:.3f}",
            f"{row['Final_E']:.3f}"
        ])

    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(elements.append(Paragraph("Detailed Adjustment Workings (Bowditch Rule)", styles['Heading2'])))
    elements.append(t)
    
    doc.build(elements)
    return buffer.getvalue()
