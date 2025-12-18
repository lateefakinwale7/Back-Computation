import ezdxf
import io

def export_to_dxf(df):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Check if the new column names exist
    if 'Final_E' in df.columns and 'Final_N' in df.columns:
        points = [(row['Final_E'], row['Final_N']) for _, row in df.iterrows()]
        if len(points) > 1:
            msp.add_lwpolyline(points)
        for p in points:
            msp.add_point(p)
            
    out = io.StringIO()
    doc.write(out)
    return out.getvalue()
