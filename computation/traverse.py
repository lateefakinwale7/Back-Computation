import pandas as pd
import numpy as np

def compute_lat_depart(df):
    # Standardize column names immediately
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Comprehensive mapping
    mapping = {
        'n': 'northing', 'northing': 'northing', 'y': 'northing',
        'e': 'easting', 'easting': 'easting', 'x': 'easting',
        'distance': 'distance', 'dist': 'distance', 'length': 'distance',
        'bearing': 'bearing', 'brg': 'bearing', 'angle': 'bearing',
        'name': 'code', 'code': 'code', 'id': 'code', 'pt': 'code'
    }
    df = df.rename(columns=lambda x: mapping.get(x, x))

    # Support for Coordinate-only files (Like your Export CSV)
    if 'northing' in df.columns and 'easting' in df.columns and 'distance' not in df.columns:
        # Calculate sequential changes
        df['distance'] = np.sqrt(df['northing'].diff()**2 + df['easting'].diff()**2).fillna(0)
        df['bearing'] = (np.degrees(np.arctan2(df['easting'].diff(), df['northing'].diff())) % 360).fillna(0)
        # We must keep the first row for the 'code', but it has 0 distance
        # Filter only when we actually start moving
        df = df.reset_index(drop=True)

    # Ensure numeric types
    df['Distance'] = pd.to_numeric(df.get('distance', 0), errors='coerce').fillna(0.0)
    df['Bearing'] = pd.to_numeric(df.get('bearing', 0), errors='coerce').fillna(0.0)
    
    # Calculate Lat/Dep
    bear_rad = np.radians(df['Bearing'])
    df['Lat (ΔN)'] = df['Distance'] * np.cos(bear_rad)
    df['Dep (ΔE)'] = df['Distance'] * np.sin(bear_rad)
    
    # Ensure 'code' exists for the next function
    if 'code' not in df.columns:
        df['code'] = [f"PT{i}" for i in range(len(df))]
        
    return df

def bowditch_adjustment_with_steps(df, start_x, start_y, close_loop=False):
    df = df.reset_index(drop=True)

    # 1. Loop Closure Logic
    if close_loop:
        current_n = start_y + df['Lat (ΔN)'].sum()
        current_e = start_x + df['Dep (ΔE)'].sum()
        dn, de = start_y - current_n, start_x - current_e
        
        if abs(dn) > 0.0001 or abs(de) > 0.0001:
            dist_close = np.sqrt(dn**2 + de**2)
            bear_close = np.degrees(np.arctan2(de, dn)) % 360
            
            close_data = {col: [None] for col in df.columns}
            close_data.update({
                'Distance': [dist_close], 
                'Bearing': [bear_close], 
                'Lat (ΔN)': [dn], 
                'Dep (ΔE)': [de], 
                'code': ['CLOSE']
            })
            close_row = pd.DataFrame(close_data)
            df = pd.concat([df, close_row], ignore_index=True)

    # 2. Adjustment
    total_dist = df['Distance'].sum()
    mis_N, mis_E = df['Lat (ΔN)'].sum(), df['Dep (ΔE)'].sum()

    df['Corr_Lat'] = -(df['Distance'] / total_dist) * mis_N if total_dist != 0 else 0
    df['Corr_Dep'] = -(df['Distance'] / total_dist) * mis_E if total_dist != 0 else 0
    
    df['Adj_Lat'] = df['Lat (ΔN)'] + df['Corr_Lat']
    df['Adj_Dep'] = df['Dep (ΔE)'] + df['Corr_Dep']

    final_n, final_e, work_n, work_e, work_lat, work_dep = [], [], [], [], [], []
    curr_n, curr_e = start_y, start_x
    
    for _, row in df.iterrows():
        work_lat.append(f"{row['Distance']:.2f} * cos({row['Bearing']:.2f})")
        work_dep.append(f"{row['Distance']:.2f} * sin({row['Bearing']:.2f})")
        
        prev_n, prev_e = curr_n, curr_e
        curr_n += row['Adj_Lat']
        curr_e += row['Adj_Dep']
        
        final_n.append(curr_n)
        final_e.append(curr_e)
        work_n.append(f"{prev_n:.3f} + ({row['Adj_Lat']:.4f})")
        work_e.append(f"{prev_e:.3f} + ({row['Adj_Dep']:.4f})")

    df['Final_N'], df['Final_E'] = final_n, final_e
    df['Math_Lat'], df['Math_Dep'] = work_lat, work_dep
    df['Math_N'], df['Math_E'] = work_n, work_e
    
    # THE FIX: Safely extract characters from the 'code' column
    # We use .get('code') and fillna to prevent AttributeError
    df['Group'] = df['code'].astype(str).str.extract('([a-zA-Z]+)', expand=False).fillna('PT')
    
    return df, mis_N, mis_E, total_dist
