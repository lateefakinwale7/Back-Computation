import streamlit as st
import pandas as pd
import numpy as np
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from utils.plot_traverse import plot_traverse
from exports.pdf_export import export_pdf
from exports.excel_export import export_to_excel
from exports.dxf_export import export_to_dxf

st.set_page_config(layout="wide", page_title="SKYY Survey Audit", page_icon="📐")
st.title("📐 Universal Survey Computation & Feature Plotter")

# --- SIDEBAR (ALL FEATURES RESTORED) ---
st.sidebar.header("🛠️ Project Settings")
# Defaulting back to 0.0 so they are not "locked"
start_x = st.sidebar.number_input("Starting Easting (X)", value=0.0, format="%.3f")
start_y = st.sidebar.number_input("Starting Northing (Y)", value=0.0, format="%.3f")

st.sidebar.divider()
close_loop = st.sidebar.toggle("Close Traverse Loop", value=False, help="Connects the last point back to the origin.")
project_notes = st.sidebar.text_area("Site Notes", placeholder="Enter site conditions...")

st.sidebar.divider()
st.sidebar.header("🏢 Branding")
comp_name = st.sidebar.text_input("Company Name", "SKYY")
surveyor = st.sidebar.text_input("Surveyor", "Lateef")

# --- FILE HANDLING ---
file = st.file_uploader("Upload Survey Data (Excel, CSV, DXF)", type=["xlsx", "csv", "dxf"])

if file:
    # Read the data
    df_raw = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    
    if not df_raw.empty:
        # Step 1: Process and Detect Data Type (Coordinates vs Measurements)
        df_processed = compute_lat_depart(df_raw)
        
        # Step 2: Bowditch Adjustment (Including Loop Closure)
        df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(
            df_processed, start_x, start_y, close_loop
        )
        
        # Calculations for metrics
        lin_mis = np.sqrt(mis_n**2 + mis_e**2)
        prec = total_dist / lin_mis if lin_mis != 0 else 0
        
        st.success("### ✅ Adjustment Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Length", f"{total_dist:.3f} m")
        m2.metric("Misclosure N", f"{mis_n:.4f} m")
        m3.metric("Misclosure E", f"{mis_e:.4f} m")
        m4.metric("Precision", f"1 : {int(prec)}")

        # --- TABS ---
        t_map, t_coords, t_audit = st.tabs(["🗺️ Feature Map", "📋 Adjusted Coordinates", "📚 Mathematical Audit"])
        
        with t_map:
            st.pyplot(plot_traverse(df_final))
            
        with t_coords:
            st.dataframe(df_final[['code', 'Final_E', 'Final_N']], use_container_width=True)
            
        with t_audit:
            st.subheader("1. Change Calculations (Trig)")
            st.table(df_final[['code', 'Math_Lat', 'Math_Dep', 'Lat (ΔN)', 'Dep (ΔE)']])
            
            st.subheader("2. Adjustment Calculations (Bowditch)")
            st.table(df_final[['code', 'Corr_Lat', 'Corr_Dep']])
            
            st.subheader("3. Coordinate Accumulation")
            col_n, col_e = st.columns(2)
            col_n.table(df_final[['code', 'Math_N', 'Final_N']])
            col_e.table(df_final[['code', 'Math_E', 'Final_E']])

        # --- EXPORTS ---
        st.divider()
        e1, e2, e3 = st.columns(3)
        with e1:
            pdf = export_pdf(df_final, mis_n, mis_e, prec, comp_name, surveyor, project_notes)
            st.download_button("Download PDF Report", pdf, "Survey_Report.pdf")
        with e2:
            st.download_button("Download Excel", export_to_excel(df_final), "Calculations.xlsx")
        with e3:
            st.download_button("Download DXF", export_to_dxf(df_final), "Map.dxf")
