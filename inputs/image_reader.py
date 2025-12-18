from PIL import Image
import numpy as np

def upload_image(file):
    img = Image.open(file)
    return np.array(img)
