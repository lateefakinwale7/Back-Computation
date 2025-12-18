import pandas as pd
import numpy as np

def compute_lat_depart(df):
    """
    Computes partial coordinates (Latitude and Departure).
    Latitude (ΔN) = Distance * cos(Bearing)
    Departure (ΔE) = Distance * sin(Bearing)
    """
    # Convert bearing to radians for math functions
    bear_rad = np.radians(df['Bearing'])
    df['Latitude'] = df['Distance'] * np.cos(bear_rad)
    df['Departure'] = df['Distance'] * np.sin(bear_rad)
    return df

def bowditch_adjustment_with_steps(df, start_x, start_y):
    """
    Adjusts the traverse using the Bowditch Rule.
    Distributes misclosure error proportional to the length of each leg.
    """
    total_dist = df['Distance'].sum()
    sum_lat = df['Latitude'].sum()
    sum_dep = df['Departure'].sum()

    # Misclosure is the sum of partial coordinates (for a closed loop)
    mis_N = sum_lat
    mis_E = sum_dep

    # Calculate corrections for each row
    df['Corr_Lat'] = -(df['Distance'] / total_dist) * mis_N
    df['Corr_Dep'] = -(df['Distance'] / total_dist) * mis_E

    # Apply corrections to get Adjusted values
    df['Adj_Lat'] = df['Latitude'] + df['Corr_Lat']
    df['Adj_Dep'] = df['Departure'] + df['Corr_Dep']

    # Calculate Final Coordinates
    coords_n = [start_y]
    coords_e = [start_x]

    for i in range(len(df)):
        coords_n.append(coords_n[-1] + df['Adj_Lat'].iloc[i])
        coords_e.append(coords_e[-1] + df['Adj_Dep'].iloc[i])

    # Add coordinates to the dataframe (dropping the last point to match row count)
    df['North_Coord'] = coords_n[1:]
    df['East_Coord'] = coords_e[1:]

    return df, mis_N, mis_E
