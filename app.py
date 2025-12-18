import streamlit as st
import pandas as pd
import numpy as np
import io

# --- Calculation Logic (Integrated to ensure no missing imports) ---
def compute_survey_data(df, start_x, start_y):
    # 1. Clean column names
    df.columns = [str(c).strip().lower() for c in df.columns]
    mapping = {
        'n': 'northing', 'northing': 'northing', 'y': 'northing',
        'e': 'easting', 'easting': 'easting', 'x': 'easting',
        'distance': 'distance', 'dist': 'distance', 'bearing': 'bearing', 'brg': 'bearing',
        'name': 'code', 'code': 'code', 'id': 'code'
    }
    df = df.rename(columns=lambda x: mapping.get(x, x))

    # 2. Check if we have Coordinates or Observations
    has_coords = 'northing' in df.columns and 'easting' in df.columns
    has_obs = 'distance' in df.columns and 'bearing' in df.columns

    # 3. If we have Coordinates but NO Observations, back-calculate them
    if has_coords and not has_obs:
        # Calculate changes between sequential points
        df['delta_n'] = df['northing'].diff().fillna(0)
        df['delta_e'] = df['easting'].diff().fillna(0)
        df['distance'] = np.sqrt(df['delta_n']**2 + df['delta_e']**2)
        df['bearing'] = np.degrees(np.arctan2(df['delta_e'], df['delta_n'])) % 360
        # Remove the first row if it's just the starting point with 0 distance
        df = df[df['distance'] > 0].copy()

    # 4. Final cleaning and Trig
    df['Distance'] = pd.to_numeric(df.get('distance', 0), errors='coerce').fillna(0)
    df['Bearing'] = pd.to_numeric(df.get('bearing', 0), errors='coerce').fillna(0)
    
    bear_rad = np.radians(df['Bearing'])
    df['Lat (ΔN)'] = df['Distance'] * np.cos(bear_rad)
    df['Dep (ΔE)'] = df['Distance'] * np.sin(bear_rad)
    
    return df

def apply_bowditch(df, s_x, s_y):
    total_dist = df['Distance'].sum()
    if total_dist == 0: return df, 0, 0, 0
    
    mis_n, mis_e = df['Lat (ΔN)'].sum(), df['Dep (ΔE)'].sum()
    
    # Mathematical strings for the audit
    df['Corr_Lat'] = -(df['Distance'] / total_dist) * mis_n
    df['Corr_Dep'] = -(df['Distance'] / total_dist) * mis_e
    
    df['Math_Lat'] = df.apply(lambda r: f"{r['Distance']:.2f} * cos({r['Bearing']:.2f})", axis=1)
    df['Math_Dep'] = df.apply(lambda r: f"{r['Distance']:.2f} * sin({r['Bearing']:.2f})", axis=1)
    
    final_n, final_e, math_n, math_e = [], [], [], []
    curr_n, curr_e = s_y, s_x
    
    for _, row in df.iterrows():
        adj_lat = row['Lat (ΔN)'] + row['Corr_Lat']
        adj_dep = row['Dep (ΔE)'] + row['Corr_Dep']
        
        math_n.append(f"{curr_n:.3f} + ({adj_lat:.4f})")
        math_e.append(f"{curr_e:.3f} + ({adj_dep:.4f})")
        
        curr_n += adj_lat
        curr_e += adj_dep
        final_n.append(curr_n)
        final_e.append(curr_e)
        
    df['Final_N'], df['Final_E'] = final_n, final_e
    df['Math_N'], df['Math_E'] = math_n, math_e
    return df, mis_n, mis_e, total_dist

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="Survey Computation Pro")
st.title("📐 Survey Computation & Audit Tool")

st.sidebar.header("🛠️ Settings")
# Use the first coordinates from your file as defaults if available
default_e, default_n = 44578.074, 754383.855 # Based on your uploaded file
start_x = st.sidebar.number_input("Start Easting (X)", value=default_e, format="%.3f")
start_y = st.sidebar.number_input("Start Northing (Y)", value=default_n, format="%.3f")
notes = st.sidebar.text_area("Project Notes", "Survey Audit Report")

uploaded_file = st.file_uploader("Upload Your File (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    if not df_raw.empty:
        # Step 1: Detect and Compute
        df_processed = compute_survey_data(df_raw, start_x, start_y)
        
        if df_processed['Distance'].sum() == 0:
            st.error("Wait! We couldn't find Distances or Coordinates in this file. Please check your column headers.")
        else:
            # Step 2: Bowditch Adjustment
            df_final, m_n, m_e, t_dist = apply_bowditch(df_processed, start_x, start_y)
            
            st.success("### ✅ Audit Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Distance", f"{t_dist:.2f} m")
            c2.metric("Linear Misclosure", f"{np.sqrt(m_n**2 + m_e**2):.4f} m")
            c3.metric("Precision", f"1 : {int(t_dist/np.sqrt(m_n**2 + m_e**2)) if m_n != 0 else 'Perfect'}")

            tabs = st.tabs(["📚 Mathematical Audit", "📋 Final Coordinates"])
            
            with tabs[0]:
                st.subheader("1. Change in Northing & Easting (ΔN / ΔE)")
                st.table(df_final[['code', 'Math_Lat', 'Math_Dep', 'Lat (ΔN)', 'Dep (ΔE)']])
                
                st.subheader("2. Adjustment Corrections")
                st.table(df_final[['code', 'Corr_Lat', 'Corr_Dep']])
                
                st.subheader("3. Coordinate Math")
                col_n, col_e = st.columns(2)
                col_n.table(df_final[['code', 'Math_N', 'Final_N']])
                col_e.table(df_final[['code', 'Math_E', 'Final_E']])
                
            with tabs[1]:
                st.dataframe(df_final[['code', 'Final_E', 'Final_N']], use_container_width=True)

            st.download_button("Download Audit CSV", df_final.to_csv(index=False), "Survey_Audit.csv")
