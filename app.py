import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# Modular Imports
from inputs.excel_reader import read_excel
from inputs.dxf_reader import read_dxf
from inputs.image_reader import upload_image
from utils.image_points import compute_dist_bearing, compute_scale, convert_points
from utils.plot_traverse import plot_traverse
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from exports.excel_export import export_to_excel
from exports.pdf_export import export_pdf
from exports.dxf_export import export_to_dxf

st.set_page_config(layout="wide", page_title="Survey Toolkit Pro")

st.title("🏗️ Survey Back-Computation & Workings")

tab1, tab2 = st.tabs(["📊 Computation", "🗺️ Digitization"])

# ------------------- TAB 1: COMPUTATION -------------------
with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        file = st.file_uploader("Upload Data (Excel, CSV, DXF)", type=["xlsx", "xls", "csv", "dxf"])
    with col2:
        start_x = st.number_input("Start Easting (X)", value=0.0)
        start_y = st.number_input("Start Northing (Y)", value=0.0)

    if file:
        ext = file.name.split('.')[-1].lower()
        df_raw = read_dxf(file) if ext == 'dxf' else read_excel(file)

        if df_raw is not None:
            # 1. Processing
            df_lat_dep = compute_lat_depart(df_raw)
            df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(df_lat_dep, start_x, start_y)
            
            # 2. Precision Calculation
            linear_mis = (mis_n**2 + mis_e**2)**0.5
            precision = total_dist / linear_mis if linear_mis != 0 else 0
            
            # 3. Main Results Display
            st.subheader("Final Coordinates")
            st.dataframe(df_final[['Final_N', 'Final_E']], use_container_width=True)

            # 4. Detailed Workings
            with st.expander("📚 View Mathematical Workings"):
                st.write("### Bowditch Rule Application")
                st.latex(r"Correction = -\left( \frac{L_{segment}}{L_{total}} \right) \times Error")
                st.table(df_final[['Distance', 'Lat (ΔN)', 'Corr_Lat', 'Adj_Lat', 'Final_N']].head(10))
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Distance", f"{total_dist:.3f} m")
                c2.metric("Misclosure (Linear)", f"{linear_mis:.4f} m")
                c3.metric("Precision Ratio", f"1 : {int(precision)}")

            # 5. Plotting
            st.subheader("Traverse Plot")
            fig = plot_traverse(df_final)
            st.pyplot(fig)

            # 6. Exports
            st.subheader("Export Results")
            e1, e2, e3 = st.columns(3)
            with e1:
                pdf_bytes = export_pdf(df_final, mis_n, mis_e, precision)
                st.download_button("📥 Download PDF Report", pdf_bytes, "Survey_Report.pdf")
            with e2:
                st.download_button("📥 Download Excel", export_to_excel(df_final), "Adjusted.xlsx")
            with e3:
                st.download_button("📥 Download DXF", export_to_dxf(df_final), "Adjusted.dxf")

# ------------------- TAB 2: DIGITIZATION -------------------
with tab2:
    st.header("Digitize from Image")
    img_file = st.file_uploader("Upload Plan (JPG/PNG)", type=["jpg", "png", "jpeg"])
    
    if img_file:
        img_array = upload_image(img_file)
        img_pil = Image.fromarray(img_array)
        
        # Resize for stability
        max_size = 1000
        ratio = min(max_size/img_pil.size[0], max_size/img_pil.size[1])
        new_size = (int(img_pil.size[0] * ratio), int(img_pil.size[1] * ratio))
        img_resized = img_pil.resize(new_size)
        
        real_dist = st.number_input("Reference Distance for Scale (m)", value=10.0)
        st.info("Draw the scale line first, then your traverse lines.")

        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#00FF00",
            background_image=img_resized,
            update_streamlit=True,
            height=img_resized.size[1],
            width=img_resized.size[0],
            drawing_mode="line",
            key="canvas_main"
        )

        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if len(objects) > 0:
                # Basic scaling logic
                obj0 = objects[0]
                px_dist = ((obj0["width"])**2 + (obj0["height"])**2)**0.5
                scale = real_dist / px_dist if px_dist > 0 else 1
                st.write(f"Calculated Scale: **{scale:.4f} m/px**")
