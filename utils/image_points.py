import numpy as np
import pandas as pd

def compute_scale(p1, p2, real_distance):
    """Calculates meters per pixel based on two reference points."""
    pixel_dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    if pixel_dist == 0:
        return 1.0
    return real_distance / pixel_dist

def convert_points(points, scale):
    """Multiplies pixel coordinates by the scale factor."""
    return [(p[0] * scale, p[1] * scale) for p in points]

def compute_dist_bearing(points):
    """
    Calculates distance and bearing between consecutive points.
    Bearing is returned in decimal degrees (0-360).
    """
    data = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        distance = np.sqrt(dx**2 + dy**2)
        
        # Calculate bearing (Surveyor's North = 0 degrees)
        # Using atan2(dx, dy) because in surveying North is Y and East is X
        bearing_rad = np.arctan2(dx, dy)
        bearing_deg = np.degrees(bearing_rad) % 360
        
        data.append({
            "Station": f"{i+1} to {i+2}",
            "Distance": round(distance, 3),
            "Bearing": round(bearing_deg, 3)
        })
    
    return pd.DataFrame(data)
