import ezdxf
import io

def export_to_dxf(df):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    groups = df.groupby('Group')
    
    for name, group in groups:
        layer_name = str(name).upper()
        if layer_name not in doc.layers:
            doc.layers.new(name=layer_name)
        
        points = [(row['Final_E'], row['Final_N']) for _, row in group.iterrows()]
        if len(points) > 1:
            msp.add_lwpolyline(points, dxfattribs={'layer': layer_name})
        for _, row in group.iterrows():
            msp.add_text(row['code'], dxfattribs={'layer': layer_name, 'height': 0.1}).set_pos((row['Final_E'], row['Final_N']))
            
    out = io.StringIO()
    doc.write(out)
    return out.getvalue()
