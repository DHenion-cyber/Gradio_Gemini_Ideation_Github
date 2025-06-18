"""
Main Streamlit application file for the Digital Health Innovation Chatbot UI.
Handles UI flow, workflow selection, and chat rendering.
"""
import os
import sys
import streamlit as st
import importlib # For dynamic module loading
import asyncio
import inspect # Added for line number logging

# Ensure project root is in sys.path for consistent imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.logger import get_logger # Roo: Added
from src.workflow_manager import WORKFLOW_REGISTRY, reset_workflow, get_workflow_display_name, get_workflow_names # Roo: Modified
from src.analytics import log_event # Roo: Added
# from src.workflows.registry import WORKFLOWS # Roo: Replaced by workflow_manager
from src.persistence_utils import ensure_db, save_session
# from src.conversation_manager import ( # Roo: Will evaluate if these are still needed or replaced by PhaseEngine logic
#     initialize_conversation_state, run_intake_flow, get_intake_questions,
#     is_out_of_scope, generate_assistant_response,
# )
# from src.workflows.value_prop import ValuePropWorkflow # Roo: Removed, will use dynamic loading
# from src.personas.coach import CoachPersona # Roo: Removed, will use workflow-specific personas
from src.ui_components import (
    apply_responsive_css, privacy_notice, render_response_with_citations
)
# Roo: Specific persona import for now, ideally this becomes dynamic too
from src.workflows.value_prop.persona import ValuePropCoachPersona


# --- PAGE CONFIG & HEADER ---
st.set_page_config(page_title="Chatbot UI", layout="wide")
st.markdown("""
<style>
#page-title {
    color: #007BFF;
    font-size: 2rem;
    font-weight: 400;
    text-align: center;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div id="page-title">Digital Innovation Chats</div>', unsafe_allow_html=True)

# --- FEEDBACK BUTTON (unchanged) ---
st.markdown("""
<style>
    #fb-button {position: fixed; bottom: 16px; right: 16px; background: #f1f1f1; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 0.85em; z-index: 1001;}
    #fb-panel {position: fixed; bottom: 48px; right: 16px; width: 320px; max-width: 90%; display: none; background: white; border: 1px solid #ddd; border-radius: 4px; padding: 8px; z-index: 1000; box-shadow: 0px 0px 10px rgba(0,0,0,0.1);}
</style>
""", unsafe_allow_html=True)
st.markdown("<div id='fb-button'>💬 Feedback</div>", unsafe_allow_html=True)
st.markdown(
    "<div id='fb-panel'>"
    "<textarea id='fb-textarea' placeholder='Share feedback…' style='width:100%;height:80px;border:1px solid #ccc;border-radius:4px;padding:4px;'></textarea>"
    "<button id='fb-submit' style='margin-top:4px;padding:4px 8px;font-size:0.9em;'>Send</button>"
    "</div>",
    unsafe_allow_html=True
)
st.components.v1.html("""
<script>
    const fbButton = document.getElementById('fb-button');
    const fbPanel = document.getElementById('fb-panel');
    const fbTextarea = document.getElementById('fb-textarea');
    const fbSubmit = document.getElementById('fb-submit');
    if (fbButton && fbPanel) {
        fbButton.onclick = function() {
            fbPanel.style.display = (fbPanel.style.display === 'block') ? 'none' : 'block';
        };
    }
    if (fbSubmit && fbTextarea && fbPanel) {
        fbSubmit.onclick = function() {
            const feedbackText = fbTextarea.value;
            if (feedbackText.trim() !== "") {
                console.log("Feedback submitted:", feedbackText); // Roo: Will change to logger if accessible from JS
                alert("Feedback submitted (logged to console for now). Thank you!");
                fbTextarea.value = "";
                fbPanel.style.display = 'none';
            } else {
                alert("Please enter some feedback before sending.");
            }
        };
    }
</script>
""", height=0)


logger = get_logger(__name__) # Roo: Added

# --- CONVERSATION STATE INIT ---
# Roo: Simplified initialization, reset_workflow will handle detailed setup
if "workflow" not in st.session_state:
    st.session_state.workflow = None
    st.session_state.phase = None
    st.session_state.history = []
    st.session_state.messages = [] # For st.chat_message if used
    st.session_state.scratchpad = {}
    st.session_state.current_phase_engine = None
    st.session_state.coach_persona_instance = None
    st.session_state["_force_re_enter_current_phase"] = False # Initialize flag
    logger.info("Initial session state initialized.")

if "conversation_initialized" not in st.session_state or st.session_state.get("new_chat_triggered"): # Roo: This block might be redundant now
    pass # Roo: Placeholder, review if this entire block is needed. reset_workflow handles init.

# --- WORKFLOW NAME FORMATTER (can be simplified if display names are in WORKFLOW_REGISTRY) ---
def format_phase_name(name_key: str):
    """Formats a phase slug into a displayable name."""
    return ' '.join(word.capitalize() for word in name_key.split('_'))

# --- SIDEBAR: WORKFLOW SELECTOR & PHASES ---
with st.sidebar:
    st.header("Workflow Control")
    available_workflows = get_workflow_names()
    
    workflow_display_options = {
        get_workflow_display_name(k): k for k in available_workflows
    }
    placeholder_text = "Select a Workflow"
    options_list = [placeholder_text] + list(workflow_display_options.keys())

    # Get current workflow display name if one is active
    current_workflow_slug = st.session_state.get("workflow")
    current_display_name = None
    if current_workflow_slug:
        current_display_name = get_workflow_display_name(current_workflow_slug)
    
    # Determine index for selectbox
    current_selection_index = 0
    if current_display_name and current_display_name in options_list:
        current_selection_index = options_list.index(current_display_name)

    selected_display_workflow = st.selectbox(
        "Choose Workflow:",
        options_list,
        index=current_selection_index, # Set index based on current workflow
        key="sb_selected_workflow_display"
    )

    newly_selected_workflow_key = None
    if selected_display_workflow != placeholder_text:
        newly_selected_workflow_key = workflow_display_options[selected_display_workflow]

    if newly_selected_workflow_key and newly_selected_workflow_key != st.session_state.get("workflow"):
        logger.info(f"Workflow selection changed to: {newly_selected_workflow_key}. Resetting workflow state.")
        reset_workflow(newly_selected_workflow_key)
        # Initialize persona for the new workflow (example for value_prop)
        if newly_selected_workflow_key == "value_prop":
            st.session_state.coach_persona_instance = ValuePropCoachPersona(workflow_name="value_prop")
            logger.info("ValuePropCoachPersona initialized for value_prop workflow.")
        else:
            st.session_state.coach_persona_instance = None # Placeholder for other personas
            logger.warning(f"No specific coach persona defined for workflow: {newly_selected_workflow_key}")
        st.rerun() # Rerun to reflect the new workflow state immediately

    st.markdown("---")

    # ---- PHASE DISPLAY SECTION & DEBUG BANNER ----
    active_workflow_slug = st.session_state.get("workflow")
    active_phase_slug = st.session_state.get("phase")

    if active_workflow_slug and active_phase_slug:
        wf_display = get_workflow_display_name(active_workflow_slug)
        ph_display = format_phase_name(active_phase_slug)
        st.info(f"🧠 Workflow: {wf_display} | Phase: {ph_display}") # PRD Requirement
        
        workflow_config = WORKFLOW_REGISTRY.get(active_workflow_slug)
        if workflow_config:
            phases_in_order = workflow_config.get("phases_definition", [])
            st.markdown("**Workflow Phases:**")
            for phase_item_slug in phases_in_order:
                is_current = (phase_item_slug == active_phase_slug)
                style = "font-weight:bold; color:#007BFF;" if is_current else "color:#555;"
                phase_item_display = format_phase_name(phase_item_slug)
                st.markdown(f"- <span style='{style}'>{phase_item_display}</span>", unsafe_allow_html=True)
        else:
            logger.warning(f"No config found for active workflow {active_workflow_slug} in WORKFLOW_REGISTRY")
    elif active_workflow_slug:
        st.info(f"Workflow: {get_workflow_display_name(active_workflow_slug)} selected. Initializing...")
    else:
        st.markdown("No workflow selected.")
        st.info("Please select a workflow from the sidebar to begin.") # Roo: Added info message

# --- Helper to get PhaseEngine class ---
def get_phase_engine_instance(workflow_slug: str, phase_slug: str, coach_persona_instance):
    """Dynamically imports and instantiates a PhaseEngine class."""
    try:
        # Construct module and class names based on convention
        # e.g., workflow 'value_prop', phase 'problem' -> src.workflows.value_prop.phases.problem.ProblemPhase
        module_path = f"src.workflows.{workflow_slug}.phases.{phase_slug}"
        class_name_parts = [part.capitalize() for part in phase_slug.split('_')]
        class_name = "".join(class_name_parts) + "Phase"
        
        logger.debug(f"Attempting to load PhaseEngine: module='{module_path}', class='{class_name}'")
        
        phase_module = importlib.import_module(module_path)
        phase_class = getattr(phase_module, class_name)
        
        # Instantiate with coach_persona and workflow_name
        return phase_class(coach_persona=coach_persona_instance, workflow_name=workflow_slug)
    except ModuleNotFoundError:
        logger.error(f"Phase module not found: {module_path}")
    except AttributeError:
        logger.error(f"Phase class '{class_name}' not found in module '{module_path}'")
    except Exception as e:
        logger.error(f"Error loading phase engine for {workflow_slug}/{phase_slug}: {e}", exc_info=True)
    return None

# --- MAIN APP LOGIC ---
async def main():
    apply_responsive_css()
    # privacy_notice() # Roo: Assuming this is still desired, keeping it.

    active_workflow_slug = st.session_state.get("workflow")
    active_phase_slug = st.session_state.get("phase")
    coach_persona = st.session_state.get("coach_persona_instance")

    if not active_workflow_slug or not active_phase_slug:
        # This case is handled by the sidebar select info message if no workflow is ever selected.
        # If a workflow was selected but phase is somehow None, it's an issue reset_workflow should prevent.
        logger.debug("Main: No active workflow or phase. Waiting for selection.")
        return

    if not coach_persona and active_workflow_slug == "value_prop": # Ensure persona for value_prop
        logger.warning("Value Proposition workflow active but no coach persona found. Re-initializing.")
        st.session_state.coach_persona_instance = ValuePropCoachPersona(workflow_name="value_prop")
        coach_persona = st.session_state.coach_persona_instance
        # Potentially rerun if this state is critical and was unexpected
        # st.rerun()
    
    if not coach_persona:
        st.error(f"Coach persona not available for workflow '{active_workflow_slug}'. Cannot proceed.")
        logger.error(f"Coach persona missing for workflow {active_workflow_slug}.")
        return

    # Instantiate current phase engine
    current_phase_engine = get_phase_engine_instance(active_workflow_slug, active_phase_slug, coach_persona)
    st.session_state.current_phase_engine = current_phase_engine # Store for access if needed elsewhere

    if not current_phase_engine:
        st.error(f"Could not load phase engine for {active_workflow_slug} / {active_phase_slug}. Please check logs.")
        return

    # --- Phase Entry Logic: Call enter() if new phase or if phase needs to re-prompt ---
    if not st.session_state.history or st.session_state.get("_force_re_enter_current_phase", False):
        if st.session_state.get("_force_re_enter_current_phase", False):
            logger.info(f"Force re-entering phase '{active_phase_slug}' for new prompt.")
        else: # History is empty, meaning it's a new phase entry
            logger.info(f"Entering new phase '{active_phase_slug}'. Getting intro message.")
        
        st.session_state["_force_re_enter_current_phase"] = False # Consume the flag

        if current_phase_engine: # Ensure engine is loaded
            log_event("phase_engine_enter_start", workflow=active_workflow_slug, phase=active_phase_slug)
            try:
                with st.spinner("Coach is preparing..."):
                    intro_message = current_phase_engine.enter()
                
                st.session_state.history.append({"role": "assistant", "content": intro_message, "citations": []})
                log_event("phase_engine_enter_success", workflow=active_workflow_slug, phase=active_phase_slug, message_length=len(intro_message))
                st.rerun() 
            except Exception as e:
                logger.error(f"Error during phase_engine.enter(): {e}", exc_info=True)
                st.session_state.history.append({"role": "assistant", "content": f"Error entering phase: {e}", "citations": []})
                log_event("phase_engine_enter_failed", workflow=active_workflow_slug, phase=active_phase_slug, error=str(e))
                st.rerun() # Rerun even on error to display the error message
        else:
            logger.error(f"Attempted to call enter() but current_phase_engine for '{active_phase_slug}' is None.")


    # --- Display Intake Header (if applicable) ---
    # This needs to be before the chat history container to appear above all conversational elements.
    if active_phase_slug == "intake":
        intake_header_text = st.session_state.get("current_phase_header")
        if intake_header_text:
            st.markdown(f"### {intake_header_text}")

    # --- Display chat history ---
    chat_col = st.container()
    with chat_col:
        for msg in st.session_state.history:
            role = msg.get("role")
            content = msg.get("content")
            if role and content:
                with st.chat_message(role):
                    citations = msg.get("citations", [])
                    if citations:
                        render_response_with_citations(content, citations)
                    else:
                        st.write(content) # Use st.markdown for better formatting if content has markdown

    # --- Chat input ---
    chat_input_placeholder_default = f"Your response for {format_phase_name(active_phase_slug)}..."
    chat_input_placeholder = chat_input_placeholder_default

    # Intake UI Enhancements (Placeholder part)
    if active_phase_slug == "intake":
        # Header is handled above. Placeholder is handled here.
        intake_placeholder = st.session_state.get("current_phase_placeholder")
        if intake_placeholder:
            chat_input_placeholder = intake_placeholder
        else:
            # Fallback if placeholder not set for some reason during intake
            chat_input_placeholder = "Please provide your input for the current question..."
            logger.warning("Intake phase active, but 'current_phase_placeholder' not found in session_state.")
    
    user_input = st.chat_input(chat_input_placeholder, key=f"chat_input_{active_workflow_slug}_{active_phase_slug}")

    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        logger.debug(f"User input: {user_input}")
        log_event("user_input_submitted", workflow=active_workflow_slug, phase=active_phase_slug, input_length=len(user_input))

        with st.spinner("Coach is thinking..."):
            try:
                response_dict = current_phase_engine.handle_response(user_input)
                assistant_reply = response_dict.get("reply", "I'm not sure how to respond to that.")
                next_phase_candidate = response_dict.get("next_phase") # Phase engine can suggest next phase

                st.session_state.history.append({"role": "assistant", "content": assistant_reply, "citations": []}) # Assuming no citations from phase engines for now
                log_event("phase_engine_response", workflow=active_workflow_slug, phase=active_phase_slug, reply_length=len(assistant_reply), next_phase_suggestion=next_phase_candidate)

                # --- Phase Transition Logic ---
                should_transition_to_new_phase = False
                new_phase_target = None

                if next_phase_candidate and next_phase_candidate != active_phase_slug:
                    # Case 1: Engine explicitly suggests a *different* next phase.
                    new_phase_target = next_phase_candidate
                    should_transition_to_new_phase = True
                    logger.info(f"Engine suggested transition from '{active_phase_slug}' to '{new_phase_target}'. Phase complete status from engine: {current_phase_engine.complete}")
                
                elif current_phase_engine.complete: # current_phase_engine.complete is True
                    # Case 2: Current phase marked itself complete.
                    # If next_phase_candidate was None (engine wants to stay or has no opinion for next), auto-advance.
                    # If next_phase_candidate was current phase (engine wants to stay), also auto-advance because it's complete.
                    log_event("phase_marked_complete", workflow=active_workflow_slug, phase=active_phase_slug, next_candidate_from_engine=next_phase_candidate)
                    
                    workflow_config = WORKFLOW_REGISTRY.get(active_workflow_slug)
                    phases_in_order = workflow_config.get("phases_definition", [])
                    try:
                        current_idx = phases_in_order.index(active_phase_slug)
                        if current_idx + 1 < len(phases_in_order):
                            new_phase_target = phases_in_order[current_idx + 1]
                            should_transition_to_new_phase = True
                            logger.info(f"Phase '{active_phase_slug}' completed. Auto-advancing to: '{new_phase_target}'.")
                        else: # Last phase completed
                            logger.info(f"Workflow '{active_workflow_slug}' completed (last phase '{active_phase_slug}' finished).")
                            st.success(f"Workflow '{get_workflow_display_name(active_workflow_slug)}' completed!")
                            log_event("workflow_completed", workflow=active_workflow_slug)
                            # No actual phase transition, workflow ends.
                    except ValueError:
                        logger.error(f"Current phase '{active_phase_slug}' not found in its workflow's phase order. Cannot auto-advance after completion.")
                
                # If we decided to transition:
                if should_transition_to_new_phase and new_phase_target:
                    st.session_state.phase = new_phase_target
                    st.session_state.history = [] # Clear history for the new phase
                    st.session_state["_force_re_enter_current_phase"] = False # New phase will trigger enter via empty history
                elif next_phase_candidate is None and not current_phase_engine.complete:
                    # Case 3: Engine wants to stay (None) AND current phase is NOT complete (e.g., Intake has more questions).
                    st.session_state["_force_re_enter_current_phase"] = True
                    logger.info(f"Phase '{active_phase_slug}' is not complete and wants to stay (returned None). Setting _force_re_enter_current_phase = True.")
                # Else: No transition, no forced re-entry.

            except Exception as e:
                logger.error(f"Error during phase_engine.handle_response(): {e}", exc_info=True)
                st.session_state.history.append({"role": "assistant", "content": f"Error processing your response: {e}", "citations": []})
                log_event("phase_engine_response_failed", workflow=active_workflow_slug, phase=active_phase_slug, error=str(e))
        
        st.rerun() # Rerun to display new messages and reflect potential phase changes

    # Remove old stage transition buttons as phase engines now control flow.
    # Workflow completion / restart options can be added based on the final phase's state.
    # Example: if st.session_state.phase == "summary" and current_phase_engine.complete:
    #    if st.button("Restart Workflow"): reset_workflow(active_workflow_slug); st.rerun()

if __name__ == "__main__":
    asyncio.run(main())
