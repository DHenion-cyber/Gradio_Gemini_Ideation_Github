import streamlit as st
from src import constants

def display_summary_panel():
    st.subheader("Idea Summary")
    scratchpad = st.session_state.get("scratchpad", constants.EMPTY_SCRATCHPAD)

    for key in constants.CANONICAL_KEYS:
        value = scratchpad.get(key)
        if value:
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        else:
            st.write(f"**{key.replace('_', ' ').title()}:** _Not yet defined_")