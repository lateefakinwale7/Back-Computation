from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def export_pdf(df, plot_figure=None):
    """Generates a PDF report of the survey computations."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Professional Survey Back-Computation Report")
    
    p.setFont("Helvetica", 10)
    y = 720
    p.drawString(100, y, "Station | Adjusted North | Adjusted East")
    y -= 20
    
    for i, row in df.iterrows():
        text = f"Point {i+1}: {row['North_Coord']:.3f}, {row['East_Coord']:.3f}"
        p.drawString(100, y, text)
        y -= 15
        if y < 100:
            p.showPage()
            y = 750
            
    p.showPage()
    p.save()
    return buffer.getvalue()
