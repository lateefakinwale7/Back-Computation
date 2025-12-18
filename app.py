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

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="SKYY Survey Pro", page_icon="📐")

st.title("📐 SKYY Survey Computation & Feature Plotter")
st.markdown("Professional Bowditch Adjustment Tool for Lateef & Co.")

# --- Sidebar Configuration ---
st.sidebar.header("🏢 Company Branding")
# Defaulting to your specific details
comp_name = st.sidebar.text_input("Company Name", value="SKYY")
surveyor_info = st.sidebar.text_input("Surveyor Name", value="Lateef")

st.sidebar.divider()
st.sidebar.header("📝 Project Details")
project_notes = st.sidebar.text_area(
    "Site Notes", 
    placeholder="Describe site conditions, equipment used, or project location...",
    height=100
)

st.sidebar.divider()
st.sidebar.header("🛠️ Traverse Settings")
start_x = st.sidebar.number_input("Starting Easting (X)", value=0.0, format="%.3f")
start_y = st.sidebar.number_input("Starting Northing (Y)", value=0.0, format="%.3f")
close_loop = st.sidebar.toggle(
    "Close Traverse Loop", 
    value=False, 
    help="Mathematically closes the loop by connecting the last point to the start."
)

# --- File Upload ---
file = st.file_uploader("Upload Survey Data (Excel, CSV, DXF)", type=["xlsx", "xls", "csv", "dxf"])

if file:
    ext = file.name.split('.')[-1].lower()
    df_raw = read_dxf(file) if ext == 'dxf' else read_excel(file)

    if df_raw is not None:
        # 1. Processing & Adjustment
        df_lat_dep = compute_lat_depart(df_raw)
        df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(
            df_lat_dep, start_x, start_y, close_loop
        )
        
        # 2. Precision Metrics
        lin_mis = (mis_n**2 + mis_e**2)**0.5
        prec = total_dist / lin_mis if lin_mis != 0 else 0
        
        # 3. Branding & Summary Display
        st.info(f"**Reporting for:** {comp_name} | **Surveyor:** {surveyor_info}")
        
        st.success("### ✅ Calculation Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Length", f"{total_dist:.3f} m")
        m2.metric("Misclosure N", f"{mis_n:.4f} m")
        m3.metric("Misclosure E", f"{mis_e:.4f} m")
        m4.metric("Precision Ratio", f"1 : {int(prec)}")

        # 4. Results & Workings Tabs
        tab_map, tab_coords, tab_workings = st.tabs(["🗺️ Feature Map", "📋 Adjusted Coordinates", "📚 Mathematical Workings"])
        
        with tab_map:
            st.subheader("Automated Feature Plot")
            st.pyplot(plot_traverse(df_final))
            st.caption("💡 Features are automatically grouped by ID prefixes (e.g., RD, WALL, PT).")
        
        with tab_coords:
            st.subheader("Final Coordinates List")
            disp_df = df_final[['code', 'Group', 'Final_E', 'Final_N']]
            disp_df.columns = ['Point ID', 'Feature Type', 'Easting (X)', 'Northing (Y)']
            st.dataframe(disp_df, use_container_width=True)
        
        with tab_workings:
            st.subheader("Calculation Audit Trail (Step-by-Step)")
            col_n, col_e = st.columns(2)
            
            with col_n:
                st.write("**Northing (Y) Calculations**")
                n_work = df_final[['code', 'Math_N', 'Final_N']]
                n_work.columns = ['ID', 'Step (Prev N + Adj ΔN)', 'Result N']
                st.table(n_work.head(30))
            
            with col_e:
                st.write("**Easting (X) Calculations**")
                e_work = df_final[['code', 'Math_E', 'Final_E']]
                e_work.columns = ['ID', 'Step (Prev E + Adj ΔE)', 'Result E']
                st.table(e_work.head(30))

        # 5. Professional Exports
        st.divider()
        st.subheader("📥 Professional Output Files")
        e1, e2, e3 = st.columns(3)
        
        with e1:
            # Matches the updated 7 arguments in exports/pdf_export.py
            pdf_data = export_pdf(
                df_final, mis_n, mis_e, prec, comp_name, surveyor_info, project_notes
            )
            st.download_button("Download Branded PDF Report", pdf_data, f"{comp_name}_Survey_Report.pdf")
            
        with e2:
            st.download_button("Download Excel Sheet", export_to_excel(df_final), f"{comp_name}_Calculations.xlsx")
            
        with e3:
            st.download_button("Download CAD DXF", export_to_dxf(df_final), f"{comp_name}_Plan.dxf")

else:
    st.info("👋 Ready for data upload. Please provide your survey file to generate the SKYY professional report.")
