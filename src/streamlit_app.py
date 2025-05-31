import streamlit as st

st.set_page_config(page_title="Chatbot UI", layout="wide")
st.title("Welcome to the Chatbot")

# Apply custom CSS for responsive design
from src.ui_components import apply_responsive_css, privacy_notice
apply_responsive_css()

# Display privacy notice
privacy_notice()