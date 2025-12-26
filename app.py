import streamlit as st
import pandas as pd
import numpy as np
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from utils.plot_traverse import plot_traverse
from exports.pdf_export import export_pdf
from exports.excel_export import export_to_excel
from exports.dxf_export import export_to_dxf

st.set_page_config(layout="wide", page_title="Survey Pro", page_icon="📐")
st.title("📐 Universal Survey Computation & Audit Tool")

# --- SIDEBAR ---
st.sidebar.header("🛠️ Project Settings")
start_x = st.sidebar.number_input("Starting Easting (X)", value=0.0, format="%.3f")
start_y = st.sidebar.number_input("Starting Northing (Y)", value=0.0, format="%.3f")

st.sidebar.divider()
close_loop = st.sidebar.toggle("Close Traverse Loop", value=False)
notes = st.sidebar.text_area("Site Notes", placeholder="Enter survey details...")

# --- DATA UPLOAD ---
file = st.file_uploader("Upload CSV or Excel", type=["xlsx", "csv", "dxf"])

if file:
    df_raw = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    
    if not df_raw.empty:
        # Step 1: Detect Coordinate-only data and compute observations
        df_processed = compute_lat_depart(df_raw)
        
        # Step 2: Bowditch Adjustment
        df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(
            df_processed, start_x, start_y, close_loop
        )
        
        # Summary Statistics
        lin_mis = np.sqrt(mis_n**2 + mis_e**2)
        prec = total_dist / lin_mis if lin_mis != 0 else 0
        
        st.success("### ✅ Adjustment Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Length", f"{total_dist:.3f} m")
        m2.metric("Misclosure N", f"{mis_n:.4f} m")
        m3.metric("Misclosure E", f"{mis_e:.4f} m")
        m4.metric("Precision", f"1 : {int(prec)}")

        # --- AUDIT TABS ---
        t_map, t_coords, t_audit = st.tabs(["🗺️ Plot", "📋 Coordinates", "📚 Mathematical Audit"])
        
        with t_map:
            st.pyplot(plot_traverse(df_final))
            
        with t_coords:
            st.dataframe(df_final[['code', 'Final_E', 'Final_N']], use_container_width=True)
            
        with t_audit:
            st.subheader("Trigonometric & Coordinate Proof")
            # Showing full mathematical steps
            st.table(df_final[['code', 'Math_Lat', 'Math_Dep', 'Math_N', 'Math_E']])
            st.subheader("Bowditch Corrections")
            st.table(df_final[['code', 'Corr_Lat', 'Corr_Dep']])

        # --- EXPORTS ---
        st.divider()
        e1, e2, e3 = st.columns(3)
        with e1:
            pdf = export_pdf(df_final, mis_n, mis_e, prec, "", "", notes)
            st.download_button("Download PDF Audit", pdf, "Survey_Audit.pdf")
        with e2:
            st.download_button("Download Excel", export_to_excel(df_final), "Calculations.xlsx")
        with e3:
            st.download_button("Download DXF", export_to_dxf(df_final), "Plan.dxf")
