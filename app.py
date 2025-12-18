import streamlit as st
import matplotlib.pyplot as plt
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# 1. Import your modular functions
from inputs.excel_reader import read_excel
from inputs.dxf_reader import read_dxf
from inputs.image_reader import upload_image
from utils.image_points import compute_dist_bearing, compute_scale, convert_points
from utils.plot_traverse import plot_traverse
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from exports.excel_export import export_to_excel
from exports.pdf_export import export_pdf
from exports.dxf_export import export_to_dxf

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Surveyor's Toolkit", page_icon="🏗️")

st.title("🏗️ Professional Survey Back-Computation & Digitization")
st.markdown("---")

# Initialize Session State for image points if not exists
if 'points' not in st.session_state:
    st.session_state['points'] = []

tab1, tab2 = st.tabs(["📊 File Input (Excel/CSV/DXF)", "🗺️ Image Digitization"])

# ---------------------------------------------------------
# TAB 1: FILE INPUTS (EXCEL, CSV, DXF)
# ---------------------------------------------------------
with tab1:
    st.header("1. Upload Survey Data")
    col_file, col_coords = st.columns([2, 1])
    
    with col_file:
        file = st.file_uploader("Upload Excel (.xlsx, .xls), CSV (.csv), or DXF (.dxf)", 
                               type=["xlsx", "xls", "csv", "dxf"])
    
    with col_coords:
        start_x = st.number_input("Starting Easting (X)", value=0.0, format="%.3f")
        start_y = st.number_input("Starting Northing (Y)", value=0.0, format="%.3f")

    if file:
        ext = file.name.split('.')[-1].lower()
        
        # Read the data based on extension
        if ext == 'dxf':
            df_raw = read_dxf(file)
        else:
            df_raw = read_excel(file)

        if df_raw is not None:
            # Step 1: Compute Latitude and Departure
            df_lat_dep = compute_lat_depart(df_raw)
            
            # Step 2: Apply Bowditch Adjustment
            df_final, mis_n, mis_e = bowditch_adjustment_with_steps(df_lat_dep, start_x, start_y)
            
            # --- Display Results ---
            st.markdown("---")
            st.subheader("Adjustment Results")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Misclosure North", f"{mis_n:.4f} m")
            m2.metric("Misclosure East", f"{mis_e:.4f} m")
            total_error = (mis_n**2 + mis_e**2)**0.5
            m3.metric("Linear Misclosure", f"{total_error:.4f} m")

            st.dataframe(df_final, use_container_width=True)
            
            # --- Plotting ---
            st.subheader("Traverse Plot")
            fig = plot_traverse(df_final)
            st.pyplot(fig)
            
            # --- Exports ---
            st.subheader("Download Adjusted Workings")
            e1, e2, e3 = st.columns(3)
            e1.download_button("📥 Excel Workings", export_to_excel(df_final), "survey_adjustment.xlsx")
            e2.download_button("📥 PDF Report", export_pdf(df_final), "survey_report.pdf")
            e3.download_button("📥 DXF for CAD", export_to_dxf(df_final), "adjusted_traverse.dxf")

# ---------------------------------------------------------
# TAB 2: INTERACTIVE IMAGE DIGITIZATION
# ---------------------------------------------------------
with tab2:
    st.header("2. Digitize from Plan/Image")
    img_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "png", "jpeg"])
    
   if img_file:
    # 1. Load the image properly
    img_array = upload_image(img_file)
    img_pil = Image.fromarray(img_array)
    
    # 2. Force the image to a manageable size if it's massive
    # Large images can sometimes trigger memory errors in the canvas
    max_size = 1000
    ratio = min(max_size/img_pil.size[0], max_size/img_pil.size[1])
    new_size = (int(img_pil.size[0] * ratio), int(img_pil.size[1] * ratio))
    img_resized = img_pil.resize(new_size)
    
    st.subheader("Set Scale")
    # ... (rest of your scale code)

    # 3. Canvas for Digitization
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="#00FF00",
        background_image=img_resized, # Use the resized PIL image here
        update_streamlit=True,
        height=img_resized.size[1],
        width=img_resized.size[0],
        drawing_mode="line",
        key="canvas_digitize"
    )

        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if len(objects) >= 1:
                # Use the first line to set scale
                obj = objects[0]
                p1 = (obj["left"], obj["top"])
                p2 = (p1[0] + obj["width"], p1[1] + obj["height"])
                
                px_dist = ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5
                scale = real_dist / px_dist if px_dist != 0 else 1.0
                
                st.write(f"Current Scale: **{scale:.4f} m/pixel**")
                
                # Extract all points from lines drawn
                all_points = []
                for obj in objects:
                    all_points.append((obj["left"], obj["top"]))
                
                if len(all_points) > 1:
                    real_coords = convert_points(all_points, scale)
                    df_digitized = compute_dist_bearing(real_coords)
                    
                    st.subheader("Digitized Data")
                    st.dataframe(df_digitized, use_container_width=True)
                    
                    # Option to send this to the adjustment logic
                    if st.button("Send Digitized Data to Adjustment"):
                        st.session_state['digitized_data'] = df_digitized
                        st.success("Data transferred to Adjustment logic!")

st.sidebar.markdown("---")
st.sidebar.info("Support: Ensure Excel headers are 'Distance' and 'Bearing'.")
