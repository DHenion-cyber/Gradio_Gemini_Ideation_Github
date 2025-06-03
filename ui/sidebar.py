import streamlit as st
from src import constants

def create_sidebar():
    st.sidebar.title("Idea Chatbot")
    if "perplexity_calls" not in st.session_state:
        st.session_state["perplexity_calls"] = 0
    remaining = constants.MAX_PERPLEXITY_CALLS - st.session_state.perplexity_calls
    st.sidebar.markdown(f"**Research remaining:** {remaining}/{constants.MAX_PERPLEXITY_CALLS}")