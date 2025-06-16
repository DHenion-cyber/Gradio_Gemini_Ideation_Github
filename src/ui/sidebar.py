"""Creates the sidebar UI for the Streamlit application, including a new chat button and research call counter."""
import streamlit as st
import constants
from src.workflows.registry import WORKFLOWS # Import WORKFLOWS

def create_sidebar():
    st.sidebar.title("Idea Chatbot")

    # Workflow selection dropdown
    workflow_display_names = {
        "value_prop": "Value Proposition",
        "market_analysis": "Market Analysis",
        "business_model": "Business Model",
        "planning_growth": "Planning & Growth",
        "beta_testing": "Beta Testing",
        "pitch_prep": "Pitch Prep"
    }
    # Ensure the order matches the user's request if possible, or a logical one.
    # The WORKFLOWS dict keys from registry.py define the actual items.
    # We can create an ordered list of keys based on the desired display order.
    
    ordered_workflow_keys = [
        "value_prop",
        "market_analysis",
        "business_model",
        "planning_growth",
        "beta_testing",
        "pitch_prep"
    ]
    
    # Create a list of display names in the desired order
    display_options = [workflow_display_names[key] for key in ordered_workflow_keys if key in WORKFLOWS]

    if "selected_workflow_key" not in st.session_state:
        st.session_state.selected_workflow_key = ordered_workflow_keys[0] # Default to the first one

    # Get current selection's display name to set as default for selectbox
    current_display_selection = workflow_display_names.get(st.session_state.selected_workflow_key, display_options[0])

    selected_display_name = st.sidebar.selectbox(
        "Select Workflow:",
        options=display_options,
        index=display_options.index(current_display_selection) # Set current selection
    )

    # Map selected display name back to workflow key
    for key, display_name in workflow_display_names.items():
        if display_name == selected_display_name:
            st.session_state.selected_workflow_key = key
            break
    
    # Display selected workflow (optional, for debugging or confirmation)
    # st.sidebar.caption(f"Current workflow: {st.session_state.selected_workflow_key}")

    st.sidebar.markdown("---") # Separator

    if "perplexity_calls" not in st.session_state:
        st.session_state["perplexity_calls"] = 0
    remaining = constants.MAX_PERPLEXITY_CALLS - st.session_state.perplexity_calls
    st.sidebar.markdown(f"**Research remaining:** {remaining}/{constants.MAX_PERPLEXITY_CALLS}")
    
    st.sidebar.markdown("---") # Separator

    if st.sidebar.button("New Chat"):
        st.session_state["new_chat_triggered"] = True
        st.rerun()