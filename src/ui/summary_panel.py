"""Displays the idea summary panel using the ValuePropWorkflow's summary generation."""
import streamlit as st
from src.workflows.value_prop import ValuePropWorkflow # Import ValuePropWorkflow
from src.constants import EMPTY_SCRATCHPAD # Import for default scratchpad if needed

def display_summary_panel():
    st.subheader("Idea Summary")

    # Reconstruct the ValuePropWorkflow instance from session_state
    # This mirrors how it's done in conversation_manager.py for consistency
    vp_workflow_scratchpad = st.session_state.get("vp_workflow_scratchpad", EMPTY_SCRATCHPAD.copy())
    
    # Create a ValuePropWorkflow instance.
    # We don't need to pass context if we're just using its scratchpad for summary.
    # However, to call generate_summary, it's better to initialize it fully.
    vp_workflow = ValuePropWorkflow() # Create a new instance
    vp_workflow.scratchpad = vp_workflow_scratchpad # Assign the scratchpad from session state
    # We don't strictly need current_step or completed status for generate_summary,
    # as it primarily relies on the scratchpad content.

    # Generate the summary using the workflow's method
    # This method now returns the full, formatted summary string.
    summary_output = vp_workflow.generate_summary()

    st.markdown(summary_output) # Use markdown to render bolding and newlines correctly