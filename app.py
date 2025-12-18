import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# Modular Imports
from inputs.excel_reader import read_excel
from inputs.dxf_reader import read_dxf
from inputs.image_reader import upload_image
from utils.image_points import compute_dist_bearing, convert_points
from utils.plot_traverse import plot_traverse
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from exports.excel_export import export_to_excel
from exports.pdf_export import export_pdf
from exports.dxf_export import export_to_dxf

st.set_page_config(layout="wide", page_title="Survey Toolkit Pro")
st.title("🏗️ Survey Back-Computation & Workings")

tab1, tab2 = st.tabs(["📊 Computation", "🗺️ Digitization"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        file = st.file_uploader("Upload Data (Excel, CSV, DXF)", type=["xlsx", "xls", "csv", "dxf"])
    with col2:
        start_x = st.number_input("Start Easting (X)", value=0.0, format="%.3f")
        start_y = st.number_input("Start Northing (Y)", value=0.0, format="%.3f")

    if file:
        ext = file.name.split('.')[-1].lower()
        df_raw = read_dxf(file) if ext == 'dxf' else read_excel(file)

        if df_raw is not None:
            # 1. Processing
            df_lat_dep = compute_lat_depart(df_raw)
            df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(df_lat_dep, start_x, start_y)
            
            # 2. Precision
            linear_mis = (mis_n**2 + mis_e**2)**0.5
            precision = total_dist / linear_mis if linear_mis != 0 else 0
            
            # 3. Results
            st.subheader("Final Adjusted Coordinates")
            st.dataframe(df_final[['Final_E', 'Final_N']], use_container_width=True)

            # 4. Workings Expander
            with st.expander("📚 View Mathematical Workings"):
                st.latex(r"Correction = -\left( \frac{L_{seg}}{L_{tot}} \right) \times Error")
                st.table(df_final[['Distance', 'Lat (ΔN)', 'Corr_Lat', 'Adj_Lat', 'Final_N']].head(10))
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Length", f"{total_dist:.3f} m")
                c2.metric("Misclosure", f"{linear_mis:.4f} m")
                c3.metric("Precision", f"1 : {int(precision)}")

            st.pyplot(plot_traverse(df_final))

            # 5. Corrected Exports
            st.subheader("Export Results")
            e1, e2, e3 = st.columns(3)
            with e1:
                pdf_bytes = export_pdf(df_final, mis_n, mis_e, precision)
                st.download_button("📥 PDF Report", pdf_bytes, "Survey_Report.pdf")
            with e2:
                st.download_button("📥 Excel File", export_to_excel(df_final), "Adjusted.xlsx")
            with e3:
                st.download_button("📥 DXF (CAD)", export_to_dxf(df_final), "Adjusted.dxf")

with tab2:
    st.header("Digitize from Image")
    img_file = st.file_uploader("Upload Plan", type=["jpg", "png", "jpeg"])
    if img_file:
        img_array = upload_image(img_file)
        img_pil = Image.fromarray(img_array)
        canvas_result = st_canvas(background_image=img_pil, update_streamlit=True, height=600, width=800, drawing_mode="line", key="canvas")
