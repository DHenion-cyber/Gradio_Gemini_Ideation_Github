"""Creates the sidebar UI for the Streamlit application, including a new chat button and research call counter."""
import streamlit as st
import constants

def create_sidebar():
    st.sidebar.title("Idea Chatbot")
    if "perplexity_calls" not in st.session_state:
        st.session_state["perplexity_calls"] = 0
    remaining = constants.MAX_PERPLEXITY_CALLS - st.session_state.perplexity_calls
    st.sidebar.markdown(f"**Research remaining:** {remaining}/{constants.MAX_PERPLEXITY_CALLS}")

    if st.sidebar.button("New Chat"):
        st.session_state["new_chat_triggered"] = True
        st.rerun()