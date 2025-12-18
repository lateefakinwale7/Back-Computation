import ezdxf
import pandas as pd
import math
import os

def read_dxf(file):
    """Reads DXF and extracts Line entities into a Traverse DataFrame."""
    # Save the uploaded file locally temporarily to read it
    temp_filename = "temp_upload.dxf"
    with open(temp_filename, "wb") as f:
        f.write(file.getbuffer())
    
    try:
        doc = ezdxf.readfile(temp_filename)
        msp = doc.modelspace()
        data = []
        
        for e in msp.query('LINE'):
            dx = e.dxf.end.x - e.dxf.start.x
            dy = e.dxf.end.y - e.dxf.start.y
            dist = math.sqrt(dx**2 + dy**2)
            # Survey bearing: 0 is North (Up), clockwise positive
            bearing = math.degrees(math.atan2(dx, dy)) % 360
            data.append({"Distance": dist, "Bearing": bearing})
            
        return pd.DataFrame(data)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
