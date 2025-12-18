import pandas as pd
import numpy as np
import streamlit as st

def compute_lat_depart(df):
    """
    Computes Lat/Dep with safety checks for missing columns.
    """
    # Force column names to match internal logic
    # In case the user has 'distance' instead of 'Distance'
    cols = {col.lower(): col for col in df.columns}
    
    if 'distance' in cols:
        df = df.rename(columns={cols['distance']: 'Distance'})
    if 'bearing' in cols:
        df = df.rename(columns={cols['bearing']: 'Bearing'})

    # Final check before math
    if 'Distance' not in df.columns or 'Bearing' not in df.columns:
        st.error("Missing 'Distance' or 'Bearing' columns. Check your file headers.")
        st.stop()

    # Ensure data is numeric
    df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce')
    df['Bearing'] = pd.to_numeric(df['Bearing'], errors='coerce')
    df = df.dropna(subset=['Distance', 'Bearing'])

    # Core Calculations
    bear_rad = np.radians(df['Bearing'])
    df['Latitude'] = df['Distance'] * np.cos(bear_rad)
    df['Departure'] = df['Distance'] * np.sin(bear_rad)
    
    return df

def bowditch_adjustment_with_steps(df, start_x, start_y):
    """
    Standard Bowditch adjustment.
    """
    total_dist = df['Distance'].sum()
    mis_N = df['Latitude'].sum()
    mis_E = df['Departure'].sum()

    # Apply corrections
    df['Adj_Lat'] = df['Latitude'] - (df['Distance'] / total_dist * mis_N)
    df['Adj_Dep'] = df['Departure'] - (df['Distance'] / total_dist * mis_E)

    # Accumulate Coordinates
    df['North_Coord'] = start_y + df['Adj_Lat'].cumsum()
    df['East_Coord'] = start_x + df['Adj_Dep'].cumsum()

    return df, mis_N, mis_E
