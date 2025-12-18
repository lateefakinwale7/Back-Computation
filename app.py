import streamlit as st
import pandas as pd
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from utils.plot_traverse import plot_traverse
from exports.excel_export import export_to_excel
from exports.pdf_export import export_pdf
from exports.dxf_export import export_to_dxf
from inputs.excel_reader import read_excel
from inputs.dxf_reader import read_dxf

st.set_page_config(layout="wide", page_title="Survey Pro", page_icon="📐")

st.title("📐 Universal Survey Computation & Feature Plotter")

# --- Sidebar Configuration ---
st.sidebar.header("Skyy ")
comp_name = st.sidebar.text_input("Skyy", value="Global Survey Solutions")
surveyor_info = st.sidebar.text_input("Lateef", value="001")

st.sidebar.divider()
st.sidebar.header("🛠️ Project Settings")
start_x = st.sidebar.number_input("Starting Easting (X)", value=0.0, format="%.3f")
start_y = st.sidebar.number_input("Starting Northing (Y)", value=0.0, format="%.3f")
close_loop = st.sidebar.toggle("Close Traverse Loop", value=False)

file = st.file_uploader("Upload Survey Data", type=["xlsx", "xls", "csv", "dxf"])

if file:
    ext = file.name.split('.')[-1].lower()
    df_raw = read_dxf(file) if ext == 'dxf' else read_excel(file)

    if df_raw is not None:
        df_lat_dep = compute_lat_depart(df_raw)
        df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(df_lat_dep, start_x, start_y, close_loop)
        
        lin_mis = (mis_n**2 + mis_e**2)**0.5
        prec = total_dist / lin_mis if lin_mis != 0 else 0
        
        # Display Branding in App
        st.info(f"**Reporting for:** {comp_name} | **Surveyor:** {surveyor_info}")
        
        st.success("### ✅ Adjustment Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Length", f"{total_dist:.3f} m")
        m2.metric("Misclosure N", f"{mis_n:.4f} m")
        m3.metric("Misclosure E", f"{mis_e:.4f} m")
        m4.metric("Precision", f"1 : {int(prec)}")

        tab_map, tab_coords, tab_workings = st.tabs(["🗺️ Feature Map", "📋 Adjusted Coordinates", "📚 Mathematical Workings"])
        
        with tab_map:
            st.pyplot(plot_traverse(df_final))
        
        with tab_coords:
            disp_df = df_final[['code', 'Group', 'Final_E', 'Final_N']]
            disp_df.columns = ['Point ID', 'Layer', 'Easting', 'Northing']
            st.dataframe(disp_df, use_container_width=True)
        
        with tab_workings:
            col_n, col_e = st.columns(2)
            with col_n:
                st.write("**Northing (Y) Accumulation**")
                st.table(df_final[['code', 'Math_N', 'Final_N']].head(20))
            with col_e:
                st.write("**Easting (X) Accumulation**")
                st.table(df_final[['code', 'Math_E', 'Final_E']].head(20))

        st.divider()
        st.subheader("📥 Export Professional Reports")
        e1, e2, e3 = st.columns(3)
        with e1:
            # Passing company info to PDF
            pdf_data = export_pdf(df_final, mis_n, mis_e, prec, comp_name, surveyor_info)
            st.download_button("Download PDF Report", pdf_data, "Survey_Report.pdf")
        with e2:
            st.download_button("Download Excel Workings", export_to_excel(df_final), "Calculation_Sheet.xlsx")
        with e3:
            st.download_button("Download CAD DXF", export_to_dxf(df_final), "Survey_Plan.dxf")
