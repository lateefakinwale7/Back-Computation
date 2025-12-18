import pandas as pd
import numpy as np
import streamlit as st
import re

def compute_lat_depart(df):
    # Clean column names
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # 1. Improved Mapping (Detects 'pt', 'id', 'name', 'code', 'remarks')
    mapping = {
        'n': 'northing', 'northing': 'northing', 'y': 'northing',
        'e': 'easting', 'easting': 'easting', 'x': 'easting',
        'distance': 'distance', 'dist': 'distance', 'length': 'distance',
        'bearing': 'bearing', 'brg': 'bearing', 'angle': 'bearing',
        'code': 'code', 'id': 'code', 'pt': 'code', 'point': 'code', 'name': 'code', 'remark': 'code'
    }
    df = df.rename(columns=lambda x: mapping.get(x, x))

    # 2. If user provided coordinates instead of Dist/Brg, calculate them
    if 'northing' in df.columns and 'easting' in df.columns:
        dn = df['northing'].diff().shift(-1)
        de = df['easting'].diff().shift(-1)
        df['distance'] = np.sqrt(dn**2 + de**2)
        df['bearing'] = np.degrees(np.arctan2(de, dn)) % 360

    # Ensure 'code' column exists, otherwise name it 'Point'
    if 'code' not in df.columns:
        df['code'] = [f"PT{i+1}" for i in range(len(df))]

    df['Distance'] = pd.to_numeric(df['distance'], errors='coerce').fillna(0)
    df['Bearing'] = pd.to_numeric(df['bearing'], errors='coerce').fillna(0)
    
    bear_rad = np.radians(df['Bearing'])
    df['Lat (ΔN)'] = df['Distance'] * np.cos(bear_rad)
    df['Dep (ΔE)'] = df['Distance'] * np.sin(bear_rad)
    return df

def bowditch_adjustment_with_steps(df, start_x, start_y, close_loop=False):
    if close_loop:
        temp_n = start_y + df['Lat (ΔN)'].sum()
        temp_e = start_x + df['Dep (ΔE)'].sum()
        dn, de = start_y - temp_n, start_x - temp_e
        dist_close = np.sqrt(dn**2 + de**2)
        bear_close = np.degrees(np.arctan2(de, dn)) % 360
        close_row = pd.DataFrame({'Distance': [dist_close], 'Bearing': [bear_close], 
                                  'Lat (ΔN)': [dn], 'Dep (ΔE)': [de], 'code': ['CLOSE']})
        df = pd.concat([df, close_row], ignore_index=True)

    total_dist = df['Distance'].sum()
    mis_N, mis_E = df['Lat (ΔN)'].sum(), df['Dep (ΔE)'].sum()

    df['Corr_Lat'] = -(df['Distance'] / total_dist) * mis_N if total_dist != 0 else 0
    df['Corr_Dep'] = -(df['Distance'] / total_dist) * mis_E if total_dist != 0 else 0
    df['Adj_Lat'] = df['Lat (ΔN)'] + df['Corr_Lat']
    df['Adj_Dep'] = df['Dep (ΔE)'] + df['Corr_Dep']

    final_n, final_e, work_n, work_e = [], [], [], []
    curr_n, curr_e = start_y, start_x
    
    for _, row in df.iterrows():
        prev_n, prev_e = curr_n, curr_e
        curr_n += row['Adj_Lat']
        curr_e += row['Adj_Dep']
        
        final_n.append(curr_n)
        final_e.append(curr_e)
        
        # Calculation strings for both N and E
        work_n.append(f"{prev_n:.3f} + ({row['Adj_Lat']:.4f})")
        work_e.append(f"{prev_e:.3f} + ({row['Adj_Dep']:.4f})")

    df['Final_N'], df['Final_E'] = final_n, final_e
    df['Math_N'], df['Math_E'] = work_n, work_e
    
    # Smart Grouping: Extract alphabetic prefix (RD1 -> RD)
    df['Group'] = df['code'].astype(str).str.extract('([a-zA-Z]+)', expand=False).fillna('PT')
    
    return df, mis_N, mis_E, total_dist
