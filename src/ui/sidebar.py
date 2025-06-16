"""Creates the sidebar UI for the Streamlit application, including a new chat button and research call counter."""
import streamlit as st
import constants
from src.workflows.registry import WORKFLOWS # Import WORKFLOWS

def create_sidebar():
    st.sidebar.title("Idea Chatbot")

    # Workflow selection dropdown
    workflow_display_names = {
        None: "Select Topic", # Placeholder
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
        None, # Placeholder first
        "value_prop",
        "market_analysis",
        "business_model",
        "planning_growth",
        "beta_testing",
        "pitch_prep"
    ]
    
    # Create a list of display names in the desired order
    # For None key, directly use its display name. For others, check if they are in WORKFLOWS.
    display_options = [workflow_display_names[key] for key in ordered_workflow_keys if key is None or key in WORKFLOWS]

    if "selected_workflow_key" not in st.session_state:
        st.session_state.selected_workflow_key = None # Default to placeholder

    # Get current selection's display name to set as default for selectbox
    # If selected_workflow_key is None, use "Select Topic". Otherwise, get from dict or default to "Select Topic".
    current_display_selection = workflow_display_names.get(st.session_state.selected_workflow_key, workflow_display_names[None])

    selected_display_name = st.sidebar.selectbox(
        "Select Workflow:",
        options=display_options,
        index=display_options.index(current_display_selection) if current_display_selection in display_options else 0 # Set current selection
    )

    # Map selected display name back to workflow key
    new_selected_key = None # Default to None if "Select Topic" is chosen
    for key, display_name in workflow_display_names.items():
        if display_name == selected_display_name:
            new_selected_key = key
            break
    
    if st.session_state.selected_workflow_key != new_selected_key:
        st.session_state.selected_workflow_key = new_selected_key
        # If the selection changed to a real workflow or to "Select Topic",
        # we might need to reset other parts of the session state.
        # For now, just updating the key. Consider if st.rerun() is needed here.
        # If a new topic is selected (not None), reset stage to 'intake'
        if new_selected_key is not None:
            st.session_state.stage = "intake" # Reset stage for new workflow
            # Potentially reset other workflow-specific states here
        else:
            # If "Select Topic" is chosen, clear relevant session state
            if "stage" in st.session_state:
                del st.session_state.stage
            # Clear other workflow specific states if necessary
            # e.g. st.session_state.messages = []
            #      st.session_state.current_question_index = 0
            #      etc.
        st.rerun() # Rerun to reflect changes immediately
    
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