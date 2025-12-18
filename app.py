import streamlit as st
import matplotlib.pyplot as plt
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# Import from your new modular structure
from inputs.excel_reader import read_excel
from inputs.dxf_reader import read_dxf
from inputs.image_reader import upload_image
from utils.image_points import compute_dist_bearing, compute_scale, convert_points
from utils.plot_traverse import plot_traverse
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from exports.excel_export import export_to_excel
from exports.pdf_export import export_pdf
from exports.dxf_export import export_to_dxf

st.set_page_config(layout="wide", page_title="Professional Survey App")
st.title("🏗️ Professional Survey Back-Computation App")

tab1, tab2 = st.tabs(["📊 Excel/DXF Input", "🗺️ Interactive Image Digitization"])

# ------------------- TAB 1: FILE INPUTS -------------------
with tab1:
    st.header("Upload Data")
    col_input, col_settings = st.columns([2, 1])
    
    with col_input:
        file = st.file_uploader("Upload Excel (.xlsx) or DXF (.dxf)", type=["xlsx", "dxf"])
    
    with col_settings:
        start_x = st.number_input("Starting Easting (X)", value=0.0)
        start_y = st.number_input("Starting Northing (Y)", value=0.0)

    if file:
        # Determine file type and read
        if file.name.endswith('.xlsx'):
            df_raw = read_excel(file)
        else:
            df_raw = read_dxf(file)

        if df_raw is not None:
            # 1. Compute Partial Coordinates
            df_lat_dep = compute_lat_depart(df_raw)
            
            # 2. Apply Bowditch Adjustment
            df_final, mis_N, mis_E = bowditch_adjustment_with_steps(df_lat_dep, start_x, start_y)
            
            # 3. Display Results
            st.subheader("Adjustment Summary")
            c1, c2 = st.columns(2)
            c1.metric("Misclosure North", f"{mis_N:.4f}m")
            c2.metric("Misclosure East", f"{mis_E:.4f}m")
            
            st.dataframe(df_final, use_container_width=True)
            
            # 4. Plot
            st.subheader("Traverse Plot")
            fig = plot_traverse(df_final)
            st.pyplot(fig)
            
            # 5. Exports
            st.subheader("Export Workings")
            ex_col1, ex_col2, ex_col3 = st.columns(3)
            ex_col1.download_button("📥 Excel", export_to_excel(df_final), "workings.xlsx")
            ex_col2.download_button("📥 PDF Report", export_pdf(df_final, fig), "report.pdf")
            ex_col3.download_button("📥 DXF CAD", export_to_dxf(df_final), "adjusted.dxf")

# ------------------- TAB 2: IMAGE DIGITIZATION -------------------
with tab2:
    st.header("Digitize from Image")
    file_img = st.file_uploader("Upload Plan", type=["png","jpg","jpeg"])
    
    if file_img:
        img_array = upload_image(file_img)
        img_pil = Image.fromarray(img_array)
        
        # Scale settings
        st.subheader("1. Define Scale")
        real_dist = st.number_input("Reference Distance (meters)", value=10.0)
        st.info("Tip: Click two points on the image to set the scale.")
        
        # Canvas for drawing
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#ff0000",
            background_image=img_pil,
            update_streamlit=True,
            height=img_pil.size[1],
            width=img_pil.size[0],
            drawing_mode="line",
            key="canvas"
        )
        
        # Processing Canvas Data
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if len(objects) >= 1:
                # Simple logic: use first line drawn to compute scale
                first_line = objects[0]
                p1 = (first_line["left"], first_line["top"])
                p2 = (p1[0] + first_line["width"], p1[1] + first_line["height"])
                
                scale = compute_scale(p1, p2, real_dist)
                st.write(f"Calculated Scale: **{scale:.4f} m/pixel**")
                
                # Convert all lines to traverse data
                # (You can expand this to extract all points from all objects)
                st.success("Points captured. Check Tab 1 logic to process this data!")
