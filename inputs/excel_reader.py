import pandas as pd
import streamlit as st

def read_excel(file):
    """
    Reads CSV, XLS, or XLSX and standardizes headers.
    """
    try:
        file_extension = file.name.split('.')[-1].lower()
        
        # Select correct reader based on extension
        if file_extension == 'csv':
            df = pd.read_csv(file)
        elif file_extension in ['xls', 'xlsx']:
            df = pd.read_excel(file)
        else:
            st.error(f"Format .{file_extension} is not supported here.")
            return None

        # Clean column names (Remove spaces and standardize case)
        df.columns = [str(col).strip().capitalize() for col in df.columns]
        
        # --- Data Preview UI ---
        st.write("### 🔍 Data Preview")
        col_list = list(df.columns)
        st.info(f"Detected File: **{file.name}** | Columns: `{', '.join(col_list)}`")
        
        # Basic validation check displayed to user
        if 'Distance' in df.columns and 'Bearing' in df.columns:
            st.success("✅ Required columns 'Distance' and 'Bearing' found.")
        else:
            st.warning("⚠️ Column mismatch. Ensure headers are 'Distance' and 'Bearing'.")
            
        st.dataframe(df.head(5), use_container_width=True)
        return df

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None
