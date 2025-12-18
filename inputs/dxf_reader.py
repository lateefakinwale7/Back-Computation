import ezdxf
import io

def export_to_dxf(df):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create points and lines for the traverse
    points = []
    # Starting point (assuming 0,0 if not provided or use first coord)
    points.append((0, 0)) 
    
    for _, row in df.iterrows():
        points.append((row['East_Coord'], row['North_Coord']))
    
    # Draw the polyline
    msp.add_lwpolyline(points)
    
    # Save to a string buffer
    out = io.StringIO()
    doc.write(out)
    return out.getvalue()
