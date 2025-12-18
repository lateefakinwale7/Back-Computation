import pandas as pd
import numpy as np
import streamlit as st

def compute_lat_depart(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    mapping = {
        'n': 'northing', 'northing': 'northing', 'e': 'easting', 'easting': 'easting',
        'distance': 'distance', 'dist': 'distance', 'bearing': 'bearing', 'brg': 'bearing'
    }
    df = df.rename(columns=lambda x: mapping.get(x, x))

    if 'northing' in df.columns and 'easting' in df.columns:
        dn = df['northing'].diff().shift(-1)
        de = df['easting'].diff().shift(-1)
        df['distance'] = np.sqrt(dn**2 + de**2)
        df['bearing'] = np.degrees(np.arctan2(de, dn)) % 360
        df = df.dropna(subset=['distance'])

    df = df.rename(columns={'distance': 'Distance', 'bearing': 'Bearing'})
    df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce')
    df['Bearing'] = pd.to_numeric(df['Bearing'], errors='coerce')
    
    # Calculate Initial Lat/Dep
    bear_rad = np.radians(df['Bearing'])
    df['Lat (ΔN)'] = df['Distance'] * np.cos(bear_rad)
    df['Dep (ΔE)'] = df['Distance'] * np.sin(bear_rad)
    return df

def bowditch_adjustment_with_steps(df, start_x, start_y):
    total_dist = df['Distance'].sum()
    mis_N = df['Lat (ΔN)'].sum()
    mis_E = df['Dep (ΔE)'].sum()

    # Step-by-step corrections
    df['Corr_Lat'] = -(df['Distance'] / total_dist) * mis_N
    df['Corr_Dep'] = -(df['Distance'] / total_dist) * mis_E

    # Adjusted values
    df['Adj_Lat'] = df['Lat (ΔN)'] + df['Corr_Lat']
    df['Adj_Dep'] = df['Dep (ΔE)'] + df['Corr_Dep']

    # Final Coordinates
    df['Final_N'] = start_y + df['Adj_Lat'].cumsum()
    df['Final_E'] = start_x + df['Adj_Dep'].cumsum()

    return df, mis_N, mis_E, total_dist
