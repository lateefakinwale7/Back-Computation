import pandas as pd

def read_excel(file):
    """Reads an uploaded Excel file and returns a DataFrame."""
    try:
        df = pd.read_excel(file)
        return df
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return None
