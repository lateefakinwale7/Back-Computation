import pandas as pd
import numpy as np

def compute_lat_depart(df):
    # 1. Clean column names
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # 2. Priority Mapping to avoid duplicate "code" columns
    final_mapping = {}
    
    # Map Coordinates
    for c in df.columns:
        if c in ['n', 'northing', 'y']: final_mapping[c] = 'northing'
        elif c in ['e', 'easting', 'x']: final_mapping[c] = 'easting'
        elif c in ['distance', 'dist', 'length']: final_mapping[c] = 'distance'
        elif c in ['bearing', 'brg', 'angle']: final_mapping[c] = 'bearing'

    # Map Identity (Priority: code > name > id > pt)
    found_id = False
    for target in ['code', 'name', 'id', 'pt']:
        if target in df.columns and not found_id:
            final_mapping[target] = 'code'
            found_id = True
            
    df = df.rename(columns=final_mapping)

    # 3. Coordinate Detection (Back-calculate Dist/Brg if missing)
    if 'northing' in df.columns and 'easting' in df.columns and 'distance' not in df.columns:
        df['distance'] = np.sqrt(df['northing'].diff()**2 + df['easting'].diff()**2).fillna(0)
        df['bearing'] = (np.degrees(np.arctan2(df['easting'].diff(), df['northing'].diff())) % 360).fillna(0)
        df = df[df['distance'] > 0].copy() # Start from first movement

    # 4. Standardize for Math Engine
    df['Distance'] = pd.to_numeric(df.get('distance', 0), errors='coerce').fillna(0.0)
    df['Bearing'] = pd.to_numeric(df.get('bearing', 0), errors='coerce').fillna(0.0)
    
    bear_rad = np.radians(df['Bearing'])
    df['Lat (ΔN)'] = df['Distance'] * np.cos(bear_rad)
    df['Dep (ΔE)'] = df['Distance'] * np.sin(bear_rad)
    
    if 'code' not in df.columns:
        df['code'] = [f"PT{i}" for i in range(len(df))]
        
    return df

def bowditch_adjustment_with_steps(df, start_x, start_y, close_loop=False):
    df = df.reset_index(drop=True)

    # 1. Loop Closure
    if close_loop:
        current_n = start_y + df['Lat (ΔN)'].sum()
        current_e = start_x + df['Dep (ΔE)'].sum()
        dn, de = start_y - current_n, start_x - current_e
        
        if abs(dn) > 0.0001 or abs(de) > 0.0001:
            dist_close = np.sqrt(dn**2 + de**2)
            bear_close = np.degrees(np.arctan2(de, dn)) % 360
            
            close_row_dict = {col: [None] for col in df.columns}
            close_row_dict.update({
                'Distance': [dist_close], 'Bearing': [bear_close], 
                'Lat (ΔN)': [dn], 'Dep (ΔE)': [de], 'code': ['CLOSE']
            })
            df = pd.concat([df, pd.DataFrame(close_row_dict)], ignore_index=True)

    # 2. Bowditch Adjustment
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
    
    # 3. Safe Group Extraction
    df['Group'] = df['code'].astype(str).str.extract('([a-zA-Z]+)', expand=False).fillna('PT')
    
    return df, mis_N, mis_E, total_dist
