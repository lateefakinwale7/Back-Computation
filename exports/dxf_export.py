import ezdxf
import io

def export_to_dxf(df):
    """Creates a new DXF file containing the adjusted traverse polyline."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Collect coordinates (East=X, North=Y)
    points = [(row['East_Coord'], row['North_Coord']) for _, row in df.iterrows()]
    
    if points:
        msp.add_lwpolyline(points)
        
    # Write to a string buffer and return as bytes
    out = io.StringIO()
    doc.write(out)
    return out.getvalue().encode('utf-8')
