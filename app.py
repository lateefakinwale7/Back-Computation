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

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Survey Pro", page_icon="📐")

st.title("📐 Universal Survey Computation & Feature Plotter")
st.markdown("Automated Bowditch Adjustment with Full Mathematical Audit Trail")

# --- Sidebar Configuration ---
st.sidebar.header("🛠️ Project Settings")
start_x = st.sidebar.number_input("Starting Easting (X)", value=0.0, format="%.3f")
start_y = st.sidebar.number_input("Starting Northing (Y)", value=0.0, format="%.3f")
close_loop = st.sidebar.toggle("Close Traverse Loop", value=False, help="Connects the last point back to the start.")

st.sidebar.divider()
st.sidebar.info("""
**Supported Headings:**
- **Points:** PT, ID, Name, Code
- **Coords:** N, E, X, Y, Northing, Easting
- **Data:** Distance, Bearing, Brg, Dist
""")

# --- File Upload ---
file = st.file_uploader("Upload Survey Data (Excel, CSV, DXF)", type=["xlsx", "xls", "csv", "dxf"])

if file:
    ext = file.name.split('.')[-1].lower()
    df_raw = read_dxf(file) if ext == 'dxf' else read_excel(file)

    if df_raw is not None:
        # 1. Core Processing
        df_lat_dep = compute_lat_depart(df_raw)
        df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(df_lat_dep, start_x, start_y, close_loop)
        
        # 2. Accuracy Metrics
        lin_mis = (mis_n**2 + mis_e**2)**0.5
        prec = total_dist / lin_mis if lin_mis != 0 else 0
        
        # --- 3. Final Summary Box ---
        st.success("### ✅ Adjustment Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Length", f"{total_dist:.3f} m")
        m2.metric("Misclosure N", f"{mis_n:.4f} m")
        m3.metric("Misclosure E", f"{mis_e:.4f} m")
        m4.metric("Precision", f"1 : {int(prec)}")

        # --- 4. Results & Workings Tabs ---
        tab_map, tab_coords, tab_workings = st.tabs(["🗺️ Feature Map", "📋 Adjusted Coordinates", "📚 Mathematical Workings"])
        
        with tab_map:
            st.subheader("Automated Feature Plot")
            st.pyplot(plot_traverse(df_final))
            st.caption("Lines are automatically grouped by Point ID prefixes (e.g., RD, BD, WALL).")
        
        with tab_coords:
            st.subheader("Final Adjusted Values")
            # Cleaner display for coordinates
            disp_df = df_final[['code', 'Group', 'Final_E', 'Final_N']]
            disp_df.columns = ['Point ID', 'Layer/Feature', 'Easting (X)', 'Northing (Y)']
            st.dataframe(disp_df, use_container_width=True)
        
        with tab_workings:
            st.subheader("Step-by-Step Coordinate Calculations")
            
            col_n, col_e = st.columns(2)
            
            with col_n:
                st.write("**Northing (Y) Accumulation**")
                n_work = df_final[['code', 'Math_N', 'Final_N']]
                n_work.columns = ['ID', 'Prev N + Adj ΔN', 'Result N']
                st.table(n_work.head(25))
            
            with col_e:
                st.write("**Easting (X) Accumulation**")
                e_work = df_final[['code', 'Math_E', 'Final_E']]
                e_work.columns = ['ID', 'Prev E + Adj ΔE', 'Result E']
                st.table(e_work.head(25))

        # --- 5. Export Section ---
        st.divider()
        st.subheader("📥 Export Professional Reports")
        e1, e2, e3 = st.columns(3)
        with e1:
            st.download_button("Download PDF Report", export_pdf(df_final, mis_n, mis_e, prec), "Survey_Report.pdf")
        with e2:
            st.download_button("Download Excel Workings", export_to_excel(df_final), "Calculation_Sheet.xlsx")
        with e3:
            st.download_button("Download CAD DXF", export_to_dxf(df_final), "Survey_Plan.dxf")

else:
    st.info("👋 Welcome! Please upload your survey file to begin. The app will automatically detect your Point IDs and feature layers.")
