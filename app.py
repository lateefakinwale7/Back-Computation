import streamlit as st
from computation.traverse import compute_lat_depart, bowditch_adjustment_with_steps
from utils.plot_traverse import plot_traverse
from exports.excel_export import export_to_excel
from exports.pdf_export import export_pdf
from exports.dxf_export import export_to_dxf
from inputs.excel_reader import read_excel
from inputs.dxf_reader import read_dxf

st.set_page_config(layout="wide", page_title="Survey Computation Pro")

st.title("📐 Survey Computation & Audit Tool")

# --- Sidebar ---
st.sidebar.header("📝 Project Details")
project_notes = st.sidebar.text_area("Project Description", placeholder="Enter site details here...")

st.sidebar.divider()
st.sidebar.header("🛠️ Settings")
start_x = st.sidebar.number_input("Start Easting (X)", value=0.0, format="%.3f")
start_y = st.sidebar.number_input("Start Northing (Y)", value=0.0, format="%.3f")
close_loop = st.sidebar.toggle("Auto-Close Traverse")

file = st.file_uploader("Upload Data (Excel, CSV, DXF)", type=["xlsx", "xls", "csv", "dxf"])

if file:
    ext = file.name.split('.')[-1].lower()
    df_raw = read_dxf(file) if ext == 'dxf' else read_excel(file)

    if df_raw is not None:
        # Processing
        df_lat_dep = compute_lat_depart(df_raw)
        df_final, mis_n, mis_e, total_dist = bowditch_adjustment_with_steps(df_lat_dep, start_x, start_y, close_loop)
        
        lin_mis = (mis_n**2 + mis_e**2)**0.5
        prec = total_dist / lin_mis if lin_mis != 0 else 0
        
        # Summary
        st.success("### ✅ Adjustment Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Length", f"{total_dist:.2f} m")
        m2.metric("Linear Misclosure", f"{lin_mis:.4f} m")
        m3.metric("Precision", f"1 : {int(prec)}")

        tab_map, tab_coords, tab_workings = st.tabs(["🗺️ Feature Map", "📋 Final Coordinates", "📚 Full Mathematical Audit"])
        
        with tab_map:
            st.pyplot(plot_traverse(df_final))
        
        with tab_coords:
            st.dataframe(df_final[['code', 'Final_E', 'Final_N']], use_container_width=True)
        
        with tab_workings:
            st.subheader("1. Calculations for Changes (ΔN and ΔE)")
            st.markdown("Trigonometric expansion: $\Delta N = Dist \cdot \cos(Brg)$ and $\Delta E = Dist \cdot \sin(Brg)$")
            st.table(df_final[['code', 'Math_Lat', 'Math_Dep']])

            st.subheader("2. Applied Corrections (Bowditch)")
            st.markdown("Correction = $-(Distance / Total Distance) \cdot Misclosure$")
            st.table(df_final[['code', 'Corr_Lat', 'Corr_Dep']])

            st.subheader("3. Final Coordinate Accumulation")
            st.markdown("Calculation: $Previous Coordinate + Adjusted Change$")
            col_n, col_e = st.columns(2)
            with col_n:
                st.write("**Northing (Y) Steps**")
                st.table(df_final[['code', 'Math_N', 'Final_N']])
            with col_e:
                st.write("**Easting (X) Steps**")
                st.table(df_final[['code', 'Math_E', 'Final_E']])

        st.divider()
        # Export buttons
        # Note: export_pdf is now called without specific SKYY branding arguments
        pdf_btn = export_pdf(df_final, mis_n, mis_e, prec, "", "", project_notes)
        st.download_button("📥 Download Full Audit PDF", pdf_btn, "Survey_Audit_Report.pdf")
        st.download_button("📥 Download CAD DXF", export_to_dxf(df_final), "Survey_Plan.dxf")
