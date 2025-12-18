from PIL import Image
import numpy as np

def upload_image(file_img):
    """Opens an uploaded image and converts it to a NumPy array for Streamlit."""
    img = Image.open(file_img)
    return np.array(img)
