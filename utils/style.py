from streamlit.components.v1 import html
import streamlit as st
import base64
from pathlib import Path

def img_to_bytes(img_path):
    """
    Convert an image file to bytes.

    Parameters:
    img_path (str): Path to the image file.

    Returns:
    str: The image file converted to bytes and encoded in base64.
    """
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def img_to_html(img_path):
    """
    Convert an image file to HTML.

    Parameters:
    img_path (str): Path to the image file.

    Returns:
    str: The image file converted to HTML.
    """
    img_html = "<img src='data:image/png;base64,{}' class='img-fluid'>".format(
      img_to_bytes(img_path)
    )
    return img_html

def header(path_to_logo,title):
    """
    Display a header with a logo and a title.

    Parameters:
    path_to_logo (str): Path to the logo image file.
    title (str): The title to display.
    """
    col1,col2,col3=st.columns([1,1,1])
    with col2:
        st.markdown(img_to_html(f'{path_to_logo}'), unsafe_allow_html=True)
    st.title(title)



