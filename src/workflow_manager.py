import streamlit as st
from src.core.logger import get_logger
from src.analytics import log_event
# Import necessary workflow and phase definitions.
# This will likely need to be more dynamic or comprehensive
# as more workflows are added.
from src.workflows import value_prop as value_prop_workflow_module
# Add other workflow phase imports here:
# from src.workflows import market_analysis as market_analysis_workflow_module

logger = get_logger(__name__)

# Define a registry for workflows and their phases
WORKFLOW_REGISTRY = {
    "value_prop": {
        "display_name": "Value Proposition",
        "module_name": "src.workflows.value_prop", # For potential dynamic loading
        "phases_definition": value_prop_workflow_module.PHASE_ORDER, # List of phase names
        "scratchpad_keys": value_prop_workflow_module.SCRATCHPAD_KEYS, # List of scratchpad keys for this workflow
        "first_phase": value_prop_workflow_module.PHASE_ORDER[0] if value_prop_workflow_module.PHASE_ORDER else None
    },
    # "market_analysis": {
    #     "display_name": "Market Analysis",
    #     "module_name": "src.workflows.market_analysis",
    #     "phases_definition": market_analysis_phases.PHASE_ORDER,
    #     "scratchpad_keys": market_analysis_phases.SCRATCHPAD_KEYS,
    #     "first_phase": market_analysis_phases.PHASE_ORDER[0] if market_analysis_phases.PHASE_ORDER else None
    # },
    # Add other workflows here
}

def get_workflow_names():
    """Returns a list of available workflow slugs."""
    return list(WORKFLOW_REGISTRY.keys())

def get_workflow_display_name(workflow_slug: str):
    """Returns the display name for a given workflow slug."""
    return WORKFLOW_REGISTRY.get(workflow_slug, {}).get("display_name", workflow_slug)


def reset_workflow(workflow_name: str):
    """
    Resets the session state for a new workflow.

    Args:
        workflow_name (str): The slug of the workflow to start (e.g., "value_prop").
    """
    logger.info(f"Resetting workflow to: {workflow_name}")
    log_event("workflow_reset_start", selected_workflow=workflow_name)

    if workflow_name not in WORKFLOW_REGISTRY:
        logger.error(f"Workflow '{workflow_name}' not found in registry.")
        st.error(f"Workflow '{workflow_name}' is not configured.")
        log_event("workflow_reset_failed", error="Workflow not in registry", selected_workflow=workflow_name)
        return

    workflow_config = WORKFLOW_REGISTRY[workflow_name]
    first_phase = workflow_config.get("first_phase")

    if not first_phase:
        logger.error(f"Workflow '{workflow_name}' has no first phase defined.")
        st.error(f"Cannot start workflow '{workflow_name}' as it has no initial phase.")
        log_event("workflow_reset_failed", error="No first phase defined", selected_workflow=workflow_name)
        return

    # Clear all session state keys except Streamlit internals and protected keys
    keys_to_clear = [k for k in st.session_state.keys() if not k.startswith("_streamlit_")]
    # Add any other keys you want to preserve here, e.g. user_id, global settings
    # protected_keys = ["user_id", "app_theme"]
    # keys_to_clear = [k for k in keys_to_clear if k not in protected_keys]

    for key in keys_to_clear:
        del st.session_state[key]
    logger.debug(f"Cleared session state keys: {keys_to_clear}")

    # Initialize new workflow state
    st.session_state.workflow = workflow_name
    st.session_state.phase = first_phase
    st.session_state.history = [] # Initialize chat history
    st.session_state.messages = [] # For Streamlit's st.chat_message

    # Initialize scratchpad keys for the workflow with appropriate prefixes
    st.session_state.scratchpad = {}
    if "scratchpad_keys" in workflow_config:
        for key in workflow_config["scratchpad_keys"]:
            # Prefixing is handled by the phase engine or persona now,
            # but ensure the main scratchpad dict is there.
            # Example: st.session_state.scratchpad[f"{workflow_name}_{key}"] = None
            st.session_state.scratchpad[key] = None # Store unprefixed, prefixing done by consumer
    logger.debug(f"Initialized scratchpad for {workflow_name} with keys: {list(st.session_state.scratchpad.keys())}")


    st.session_state.current_phase_engine = None # Will be initialized by the main app loop

    logger.info(f"Workflow '{workflow_name}' reset. Current phase: '{first_phase}'.")
    log_event("workflow_reset_complete", active_workflow=workflow_name, initial_phase=first_phase)

if __name__ == '__main__':
    # Mock st.session_state for local testing
    class MockSessionState:
        def __init__(self):
            self._session_state = {"_streamlit_internal_key": "some_value"}

        def keys(self):
            return self._session_state.keys()

        def __getitem__(self, key):
            return self._session_state[key]

        def __setitem__(self, key, value):
            self._session_state[key] = value

        def __delitem__(self, key):
            del self._session_state[key]

        def get(self, key, default=None):
            return self._session_state.get(key, default)

    st.session_state = MockSessionState()
    st.session_state.old_key = "should_be_deleted"
    st.session_state.workflow = "old_workflow"
    st.session_state.phase = "old_phase"

    print("Before reset:", dict(st.session_state._session_state))
    reset_workflow("value_prop")
    print("After reset (value_prop):", dict(st.session_state._session_state))

    # Example of how scratchpad keys might be defined in a workflow's phases.py
    # value_prop_phases.py
    # SCRATCHPAD_KEYS = ["problem_statement", "solution_description"]
    # PHASE_ORDER = ["ProblemDefinitionPhase", "SolutionIdeationPhase"]