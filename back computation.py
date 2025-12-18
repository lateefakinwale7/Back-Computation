import streamlit as st
import matplotlib.pyplot as plt
from streamlit_drawable_canvas import st_canvas

from inputs.excel_reader import read_excel
from inputs.dxf_reader import read_dxf
from inputs.image_reader import upload_image
from utils.image_points import compute_dist_bearing, compute_scale, convert_points
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from utils.plot_traverse import plot_traverse
from exports.excel_export import export_to_excel
from exports.pdf_export import export_pdf
from exports.dxf_export import export_to_dxf

st.set_page_config(layout="wide")
st.title("Professional Survey Back Computation App")

tab1, tab2 = st.tabs(["Excel/DXF Input", "Interactive Image Digitization"])

# ------------------- TAB 1 -------------------
with tab1:
    st.header("Upload Excel (.xlsx) or DXF")
    file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if file:
        df = read_excel(file)
        df = compute_lat_depart(df)
        start_x = st.number_input("Starting X coordinate", value=0.0)
        start_y = st.number_input("Starting Y coordinate", value=0.0)
        df_steps, mis_N, mis_E = bowditch_adjustment_with_steps(df, start_x, start_y)
        st.write(f"Misclosure North: {mis_N:.3f}, East: {mis_E:.3f}")
        st.subheader("Step-by-Step Workings")
        st.dataframe(df_steps)
        plt_obj = plot_traverse(df_steps)
        st.pyplot(plt_obj)
        st.download_button("Download Excel", export_to_excel(df_steps))
        st.download_button("Download PDF", export_pdf(df_steps, plot_figure=plt_obj))
        st.download_button("Download DXF", export_to_dxf(df_steps))

# ------------------- TAB 2 -------------------
with tab2:
    st.header("Interactive Traverse Digitization from Image")
    file_img = st.file_uploader("Upload Survey Plan Image", type=["png","jpg","jpeg"])
    
    if file_img:
        img = upload_image(file_img)
        st.image(img, caption="Survey Plan", use_column_width=True)
        
        # Reference scale input
        st.subheader("Define Reference Scale")
        ref1_x = st.number_input("Reference Point 1 X (pixel)", value=0.0, key="ref1x")
        ref1_y = st.number_input("Reference Point 1 Y (pixel)", value=0.0, key="ref1y")
        ref2_x = st.number_input("Reference Point 2 X (pixel)", value=0.0, key="ref2x")
        ref2_y = st.number_input("Reference Point 2 Y (pixel)", value=0.0, key="ref2y")
        real_dist = st.number_input("Known Distance between points (meters)", value=50.0)
        scale = compute_scale((ref1_x, ref1_y), (ref2_x, ref2_y), real_dist)
        st.write(f"Scale factor: {scale:.4f} meters per pixel")
        
        st.write("Click points on the image to define traverse stations:")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            background_image=img,
            update_streamlit=True,
            height=img.shape[0],
            width=img.shape[1],
            key="canvas"
        )
        
        if canvas_result.json_data is not None:
            points = []
            for obj in canvas_result.json_data["objects"]:
                for p in obj["path"]:
                    points.append((p["x"], p["y"]))
            points = [points[i] for i in range(len(points)) if i==0 or points[i]!=points[i-1]]
            
            if len(points)>=2:
                # Convert points using scale
                real_points = convert_points(points, scale)
                df = compute_dist_bearing(real_points)
                df = compute_lat_depart(df)
                start_x = st.number_input("Starting X coordinate", value=0.0, key="canvas_x")
                start_y = st.number_input("Starting Y coordinate", value=0.0, key="canvas_y")
                df_steps, mis_N, mis_E = bowditch_adjustment_with_steps(df, start_x, start_y)
                st.write(f"Misclosure North: {mis_N:.3f}, East: {mis_E:.3f}")
                st.subheader("Step-by-Step Workings")
                st.dataframe(df_steps)
                
                # Plot with scale bar
                plt_obj = plot_traverse(df_steps, scale_bar_length=real_dist)
                st.pyplot(plt_obj)
                
                st.download_button("Download Excel", export_to_excel(df_steps))
                st.download_button("Download PDF", export_pdf(df_steps, plot_figure=plt_obj))
                st.download_button("Download DXF", export_to_dxf(df_steps))
