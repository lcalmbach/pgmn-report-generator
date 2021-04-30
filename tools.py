import base64
import os

def get_base64_encoded_image(image_path):
    """
    returns bytecode for an image file
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

def color_gradient(row: int, value_col: str, min_val: float, max_val: float, rgb: str) -> int:
    """
    Projects a value on a color gradient scale given the min and max value.
    the color gradient type is defined in the config, e.g. blue-green, red, blue etc.
    returns a string with rgb values
    """

    result = {'r': 0, 'g': 0, 'b': 0}
    if max_val - min_val != 0:
        x = int((row[value_col] - min_val) / (max_val - min_val) * 255)
    else:
        x = 0

    if 1==1: # cn.GRADIENT == 'blue-green'
        if row[value_col] > max_val:
            result['r'] = 255
        else:
            result['g'] = x
            result['b'] = abs(255 - x)
    return result[rgb]
