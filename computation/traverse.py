import pandas as pd
import numpy as np

def compute_lat_depart(df):
    # Standardize column names (lowercase and stripped)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Expanded mapping to catch almost any naming convention
    mapping = {
        'n': 'northing', 'northing': 'northing', 'y': 'northing',
        'e': 'easting', 'easting': 'easting', 'x': 'easting',
        'distance': 'distance', 'dist': 'distance', 'length': 'distance', 'len': 'distance',
        'bearing': 'bearing', 'brg': 'bearing', 'angle': 'bearing', 'azimuth': 'bearing',
        'code': 'code', 'id': 'code', 'pt': 'code', 'name': 'code', 'remark': 'code'
    }
    df = df.rename(columns=lambda x: mapping.get(x, x))

    # Force numeric conversion and handle errors
    for col in ['distance', 'bearing']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            df[col] = 0.0 # Placeholder if column is missing

    # Perform raw trigonometry
    bear_rad = np.radians(df['bearing'])
    df['Lat (ΔN)'] = df['distance'] * np.cos(bear_rad)
    df['Dep (ΔE)'] = df['distance'] * np.sin(bear_rad)
    
    # Ensure distance is renamed for the rest of the app logic
    df = df.rename(columns={'distance': 'Distance', 'bearing': 'Bearing'})
    return df

def bowditch_adjustment_with_steps(df, start_x, start_y, close_loop=False):
    # Safety: Ensure Distance is numeric before summing
    df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce').fillna(0.0)
    
    total_dist = df['Distance'].sum()
    
    # If total_dist is 0, the math will fail/result in zero
    if total_dist == 0:
        return df, 0, 0, 0

    mis_N, mis_E = df['Lat (ΔN)'].sum(), df['Dep (ΔE)'].sum()

    # Calculate Corrections
    df['Corr_Lat'] = -(df['Distance'] / total_dist) * mis_N
    df['Corr_Dep'] = -(df['Distance'] / total_dist) * mis_E
    
    # Adjusted Changes
    df['Adj_Lat'] = df['Lat (ΔN)'] + df['Corr_Lat']
    df['Adj_Dep'] = df['Dep (ΔE)'] + df['Corr_Dep']

    final_n, final_e = [], []
    work_n, work_e, work_lat, work_dep = [], [], [], []
    
    curr_n, curr_e = start_y, start_x
    
    for _, row in df.iterrows():
        # Audit Strings
        work_lat.append(f"{row['Distance']:.2f} × cos({row['Bearing']:.2f}°)")
        work_dep.append(f"{row['Distance']:.2f} × sin({row['Bearing']:.2f}°)")
        
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
    
    # Extract Group
    df['Group'] = df['code'].astype(str).str.extract('([a-zA-Z]+)', expand=False).fillna('PT')
    
    return df, mis_N, mis_E, total_dist
