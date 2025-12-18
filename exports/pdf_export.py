from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

def export_pdf(df, mis_n, mis_e, precision):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Survey Adjustment Report", styles['Title']))
    
    # Table Data with updated column names
    data = [["Dist", "Bearing", "Lat (ΔN)", "Dep (ΔE)", "Corr_N", "Corr_E", "Final_N", "Final_E"]]
    for _, row in df.iterrows():
        data.append([
            f"{row['Distance']:.2f}", f"{row['Bearing']:.2f}",
            f"{row.get('Lat (ΔN)', 0):.3f}", f"{row.get('Dep (ΔE)', 0):.3f}",
            f"{row.get('Corr_Lat', 0):.4f}", f"{row.get('Corr_Dep', 0):.4f}",
            f"{row['Final_N']:.3f}", f"{row['Final_E']:.3f}"
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('FONTSIZE', (0,0), (-1,-1), 7)]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()
