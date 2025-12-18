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
st.title("📐 Universal Survey Computation & Feature Grouping")

# Sidebar Settings
st.sidebar.header("Global Settings")
start_x = st.sidebar.number_input("Start X (Easting)", value=0.0, format="%.3f")
start_y = st.sidebar.number_input("Start Y (Northing)", value=0.0, format="%.3f")
close_loop = st.sidebar.toggle("Auto-Close Loop", value=False)

file = st.file_uploader("Upload Survey File", type=["xlsx", "xls", "csv", "dxf"])

if file:
    ext = file.name.split('.')[-1].lower()
    df_raw = read_dxf(file) if ext == 'dxf' else read_excel(file)

    if df_raw is not None:
        df_lat_dep = compute_lat_depart(df_raw)
        df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(df_lat_dep, start_x, start_y, close_loop)
        
        lin_mis = (mis_n**2 + mis_e**2)**0.5
        prec = total_dist / lin_mis if lin_mis != 0 else 0
        
        st.success(f"✅ Processed {len(df_final)} points across {df_final['Group'].nunique()} layers.")
        
        t1, t2, t3 = st.tabs(["🗺️ Visual Map", "📋 Coordinate Table", "📚 Mathematical Workings"])
        
        with t1:
            st.pyplot(plot_traverse(df_final))
        
        with t2:
            disp = df_final[['code', 'Group', 'Final_E', 'Final_N']]
            disp.columns = ['Point ID', 'Layer', 'Easting', 'Northing']
            st.dataframe(disp, use_container_width=True)
        
        with t3:
            st.write("### Northing Calculation Workings")
            st.table(df_final[['Math_N', 'Final_N']].head(15))
            st.metric("Linear Misclosure", f"{lin_mis:.4f} m")
            st.metric("Precision Ratio", f"1 : {int(prec)}")

        st.divider()
        e1, e2, e3 = st.columns(3)
        e1.download_button("📥 PDF Report", export_pdf(df_final, mis_n, mis_e, prec), "Report.pdf")
        e2.download_button("📥 Excel File", export_to_excel(df_final), "Data.xlsx")
        e3.download_button("📥 CAD DXF", export_to_dxf(df_final), "Plan.dxf")
