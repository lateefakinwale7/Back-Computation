import ezdxf
import io

def export_to_dxf(df):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Group by feature code (e.g., RD, PT, BW)
    groups = df.groupby('Group')
    
    for name, group in groups:
        layer_name = str(name).upper()
        if layer_name not in doc.layers:
            doc.layers.new(name=layer_name)
        
        # Create a list of (E, N) tuples for the polyline
        points = [(row['Final_E'], row['Final_N']) for _, row in group.iterrows()]
        
        # Draw the line connecting the points
        if len(points) > 1:
            msp.add_lwpolyline(points, dxfattribs={'layer': layer_name})
            
        # Add labels at each point
        for _, row in group.iterrows():
            # Placing text at the specific coordinate (Final_E, Final_N)
            # We use dpp (dxfattribs) directly for position to avoid set_pos errors
            msp.add_text(
                str(row['code']), 
                dxfattribs={
                    'layer': layer_name, 
                    'height': 0.15,
                    'insert': (row['Final_E'], row['Final_N'])
                }
            )
            
    out = io.StringIO()
    doc.write(out)
    return out.getvalue()
