import pandas as pd
import io

def export_to_excel(df):
    """Converts the processed DataFrame into a downloadable Excel binary."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Adjusted Traverse')
    return output.getvalue()
