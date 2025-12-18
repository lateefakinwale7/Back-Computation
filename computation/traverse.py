import pandas as pd
import numpy as np
import streamlit as st

def compute_lat_depart(df):
    """
    Automatically detects headers (N, E, Northing, Easting, Distance, Bearing)
    and prepares the data for Bowditch adjustment.
    """
    # 1. Clean column names
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # 2. Define Mapping Dictionary for common survey terms
    mapping = {
        'n': 'northing', 'northing': 'northing', 'north': 'northing', 'y': 'northing',
        'e': 'easting', 'easting': 'easting', 'east': 'easting', 'x': 'easting',
        'distance': 'distance', 'dist': 'distance', 'd': 'distance', 'length': 'distance',
        'bearing': 'bearing', 'brg': 'bearing', 'angle': 'bearing', 'theta': 'bearing'
    }

    # Rename columns based on mapping
    df = df.rename(columns=lambda x: mapping.get(x, x))

    # --- LOGIC A: If user provided Coordinates (N & E) ---
    if 'northing' in df.columns and 'easting' in df.columns:
        st.info("🛰️ Coordinates detected. Calculating Distance and Bearing automatically...")
        
        # Calculate differences between consecutive points
        dn = df['northing'].diff().shift(-1)
        de = df['easting'].diff().shift(-1)
        
        df['distance'] = np.sqrt(dn**2 + de**2)
        df['bearing'] = np.degrees(np.arctan2(de, dn)) % 360
        
        # Remove the last row which will be NaN after shifting
        df = df.dropna(subset=['distance'])

    # --- LOGIC B: Standard Distance/Bearing Mode ---
    if 'distance' in df.columns and 'bearing' in df.columns:
        # Final formatting for internal use
        df = df.rename(columns={'distance': 'Distance', 'bearing': 'Bearing'})
        
        df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce')
        df['Bearing'] = pd.to_numeric(df['Bearing'], errors='coerce')
        df = df.dropna(subset=['Distance', 'Bearing'])

        bear_rad = np.radians(df['Bearing'])
        df['Latitude'] = df['Distance'] * np.cos(bear_rad)
        df['Departure'] = df['Distance'] * np.sin(bear_rad)
        return df
    else:
        st.error("❌ Could not find valid headers. Please use 'N', 'E' or 'Distance', 'Bearing'.")
        st.stop()

def bowditch_adjustment_with_steps(df, start_x, start_y):
    """Standard Bowditch adjustment logic."""
    total_dist = df['Distance'].sum()
    if total_dist == 0: return df, 0, 0
    
    mis_N = df['Latitude'].sum()
    mis_E = df['Departure'].sum()

    df['Adj_Lat'] = df['Latitude'] - (df['Distance'] / total_dist * mis_N)
    df['Adj_Dep'] = df['Departure'] - (df['Distance'] / total_dist * mis_E)

    df['North_Coord'] = start_y + df['Adj_Lat'].cumsum()
    df['East_Coord'] = start_x + df['Adj_Dep'].cumsum()

    return df, mis_N, mis_E
