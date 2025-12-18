import streamlit as st
import pandas as pd
import numpy as np
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from utils.plot_traverse import plot_traverse
from exports.excel_export import export_to_excel
from exports.pdf_export import export_pdf
from exports.dxf_export import export_to_dxf
from inputs.excel_reader import read_excel
from inputs.dxf_reader import read_dxf

st.set_page_config(layout="wide", page_title="Survey Pro Audit", page_icon="📐")

st.title("📐 Universal Survey Computation & Audit Tool")

# --- Sidebar (Restored All Features) ---
st.sidebar.header("🛠️ Project Settings")
# We allow you to set the start, but we can also detect it from the file
start_x = st.sidebar.number_input("Starting Easting (X)", value=0.0, format="%.3f")
start_y = st.sidebar.number_input("Starting Northing (Y)", value=0.0, format="%.3f")

st.sidebar.divider()
close_loop = st.sidebar.toggle("Close Traverse Loop", value=False, help="Connects the last point back to the start.")
project_notes = st.sidebar.text_area("Site Notes", placeholder="Enter site conditions...")

st.sidebar.divider()
st.sidebar.header("📥 Branding")
comp_name = st.sidebar.text_input("Company Name", "SKYY")
surveyor = st.sidebar.text_input("Surveyor", "Lateef")

# --- File Upload & Logic ---
file = st.file_uploader("Upload Survey Data", type=["xlsx", "xls", "csv", "dxf"])

if file:
    ext = file.name.split('.')[-1].lower()
    df_raw = read_dxf(file) if ext == 'dxf' else read_excel(file)

    if df_raw is not None:
        # --- FIX FOR COORDINATE-ONLY FILES ---
        # If the file has N and E but NO Distance/Bearing, we calculate them
        df_raw.columns = [str(c).strip().lower() for c in df_raw.columns]
        if 'n' in df_raw.columns and 'e' in df_raw.columns and 'distance' not in df_raw.columns:
            st.info("💡 Coordinate file detected. Back-calculating Distances and Bearings...")
            df_raw['distance'] = np.sqrt(df_raw['n'].diff()**2 + df_raw['e'].diff()**2).fillna(0)
            df_raw['bearing'] = (np.degrees(np.arctan2(df_raw['e'].diff(), df_raw['n'].diff())) % 360).fillna(0)
            # Update sidebar start values to match the first point in your file automatically
            start_x = df_raw['e'].iloc[0]
            start_y = df_raw['n'].iloc[0]

        # 1. Processing
        df_lat_dep = compute_lat_depart(df_raw)
        df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(
            df_lat_dep, start_x, start_y, close_loop
        )
        
        lin_mis = np.sqrt(mis_n**2 + mis_e**2)
        prec = total_dist / lin_mis if lin_mis != 0 else 0
        
        # 2. Display Metrics
        st.success("### ✅ Adjustment Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Length", f"{total_dist:.3f} m")
        m2.metric("Misclosure N", f"{mis_n:.4f} m")
        m3.metric("Misclosure E", f"{mis_e:.4f} m")
        m4.metric("Precision", f"1 : {int(prec)}")

        # 3. Restored Tabs
        tab_map, tab_coords, tab_workings = st.tabs(["🗺️ Feature Map", "📋 Adjusted Coordinates", "📚 Mathematical Workings"])
        
        with tab_map:
            st.pyplot(plot_traverse(df_final))
        
        with tab_coords:
            st.dataframe(df_final[['code', 'Final_E', 'Final_N']], use_container_width=True)
        
        with tab_workings:
            st.subheader("Trigonometric & Coordinate Audit")
            st.write("**Full Mathematical Steps for every Point:**")
            # Showing the detailed math strings we built earlier
            st.table(df_final[['code', 'Math_Lat', 'Math_Dep', 'Math_N', 'Math_E']])

        # 4. Restored Exports
        st.divider()
        e1, e2, e3 = st.columns(3)
        with e1:
            pdf_data = export_pdf(df_final, mis_n, mis_e, prec, comp_name, surveyor, project_notes)
            st.download_button("Download PDF Report", pdf_data, "Survey_Report.pdf")
        with e2:
            st.download_button("Download Excel Workings", export_to_excel(df_final), "Calculation_Sheet.xlsx")
        with e3:
            st.download_button("Download CAD DXF", export_to_dxf(df_final), "Survey_Plan.dxf")
