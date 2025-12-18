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

    elements.append(Paragraph("Survey Computation & Feature Report", styles['Title']))
    elements.append(Spacer(1, 12))

    data = [["ID", "Dist", "Bearing", "Northing Math", "Final_N", "Easting Math", "Final_E"]]
    for _, row in df.iterrows():
        data.append([row['code'], f"{row['Distance']:.2f}", f"{row['Bearing']:.2f}",
                     row['Math_N'], f"{row['Final_N']:.3f}", 
                     row['Math_E'], f"{row['Final_E']:.3f}"])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTSIZE', (0,0), (-1,-1), 6)]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()
