"""Main Streamlit application file for the Digital Health Innovation Chatbot UI."""
import os
import sys
import streamlit as st
import datetime
import logging
import asyncio

# Remove if not needed; can break if cleanup.py is missing or faulty
# import cleanup

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from persistence_utils import ensure_db, save_session
from conversation_manager import (
    initialize_conversation_state, run_intake_flow, get_intake_questions,
    is_out_of_scope, generate_assistant_response,
)
from ui_components import (
    apply_responsive_css, privacy_notice, render_response_with_citations,
    progress_bar, render_general_feedback_trigger, render_final_session_feedback_prompt
)
from ui.sidebar import create_sidebar
from persona_simulation import get_persona_response
# from src.workflows.value_prop import render_value_prop_workflow # Removed incorrect import
from src.workflows.value_prop import ValuePropWorkflow # Added correct class import
from src.personas.coach import CoachPersona # Added persona import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize conversation state (this runs once per session unless new_chat is triggered)
if "conversation_initialized" not in st.session_state or st.session_state.get("new_chat_triggered"):
    try:
        initialize_conversation_state(new_chat=True)
        st.session_state["conversation_initialized"] = True
        st.session_state["new_chat_triggered"] = False
        logging.info("Conversation state initialized successfully (new chat).")
    except Exception as e:
        logging.error(f"Error initializing conversation state: {e}", exc_info=True)
        st.error(f"An error occurred during initialization: {e}")
        st.stop()
else:
    logging.info("Conversation state already initialized.")

SECTIONS = ["Intake questions", "Value Proposition", "Actionable Recommendations", "Session Summary"]

def render_horizontal_header(current_stage, current_phase):
    st.markdown(
        """
        <style>
        .horizontal-header {
            display: flex;
            justify-content: space-around;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
            margin-bottom: 20px;
        }
        .header-item {
            font-size: 1.1em;
            font-weight: bold;
            color: darkgrey;
            cursor: pointer;
            padding: 5px 10px;
        }
        .header-item.active {
            color: black;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="horizontal-header">', unsafe_allow_html=True)
    for section in SECTIONS:
        is_active = False
        if current_stage == "intake" and section == "Intake questions":
            is_active = True
        elif current_stage == "ideation" and section == "Value Proposition":
            is_active = True
        st.markdown(
            f'<div class="header-item {"active" if is_active else ""}">{section}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

async def main():
    st.set_page_config(page_title="Chatbot UI", layout="wide")
    st.title("Digital Health Innovation Chats")
    apply_responsive_css()
    privacy_notice()
    create_sidebar()

    selected_workflow = st.session_state.get("selected_workflow_key")
    current_stage_before_logic = st.session_state.get("stage")

    # If no workflow is selected, ensure stage is None and UI is minimal
    if selected_workflow is None:
        if st.session_state.get("stage") is not None:
            st.session_state.stage = None
            # Clear other relevant states if needed
            st.session_state.pop("conversation_history", None)
            st.session_state.pop("intake_answers", None)
            st.session_state.pop("intake_index", None) # Cleared here
            logging.info(f"No workflow selected. Stage explicitly set to None. Cleared related states.")
            st.rerun() # Rerun to clear UI
    elif selected_workflow == "value_prop":
        current_stage = st.session_state.get("stage")
        # Valid post-intake stages for value_prop. Add more if they exist.
        valid_post_intake_stages = ["ideation", "summary"]

        # If value_prop is selected, and we are NOT in a valid post-intake stage for it,
        # then we should be in 'intake'. Initialize intake_index if needed.
        if current_stage not in valid_post_intake_stages:
            if current_stage != "intake" or "intake_index" not in st.session_state:
                st.session_state.stage = "intake"
                st.session_state.intake_index = 0 # Initialize/Reset intake index
                logging.info(f"Workflow '{selected_workflow}': Stage set to 'intake'. Intake index initialized/reset to 0.")
                st.rerun() # Rerun if we made a change to stage or intake_index
        # If current_stage IS one of valid_post_intake_stages, this block is skipped,
        # preventing the intake from restarting.
    # For other workflows (not value_prop and not None), we might not need a stage or a different logic.
    # For now, if a non-value-prop workflow is selected, and stage was previously set (e.g. from value_prop), clear it.
    elif selected_workflow is not None and selected_workflow != "value_prop":
        if st.session_state.get("stage") is not None:
            st.session_state.stage = None
            logging.info(f"Workflow '{selected_workflow}': Stage was '{current_stage_before_logic}'. Stage explicitly set to None.")
            st.rerun()


    st.sidebar.subheader("Session Metrics")
    st.sidebar.write(f"Tokens Used (Session): {st.session_state.get('token_usage', {}).get('session', 0)}")
    st.sidebar.write(f"Tokens Used (Daily): {st.session_state.get('token_usage', {}).get('daily', 0)}")
    progress_bar(st.session_state.get("turn_count", 0))

    try:
        # Only render header and workflow specific UI if a workflow is selected
        if selected_workflow:
            render_horizontal_header(st.session_state.get("stage"), st.session_state.get("phase"))

            # --- Intake Stage Logic (Common for workflows that use it) ---
            if st.session_state.get("stage") == "intake":
                logging.info(f"DEBUG: Entering intake stage for workflow: {selected_workflow}.")
                # Assuming get_intake_questions might be workflow-specific in the future,
                # but for now, it's generic.
                intake_questions = get_intake_questions() # Removed workflow_key
                current_intake_index = st.session_state.get("intake_index", 0)

                if current_intake_index < len(intake_questions):
                    current_question = intake_questions[current_intake_index]
                    # Use selected_workflow in form key to ensure unique keys if multiple workflows use this intake
                    form_key_suffix = selected_workflow if selected_workflow else "default"
                    with st.form(key=f"intake_form_{form_key_suffix}_{current_intake_index}"):
                        st.markdown(current_question)
                        user_response_input = st.text_input("Your response:", key=f"intake_q_{form_key_suffix}_{current_intake_index}_input")
                        submitted = st.form_submit_button(label="Submit")
                    if submitted:
                        if user_response_input:
                            # run_intake_flow might also need to be workflow-aware
                            run_intake_flow(user_response_input) # Removed workflow_key
                            st.rerun()
                        else:
                            st.warning("Please enter a response to proceed.")
                else: # Intake complete
                    logging.info(f"Intake complete for {selected_workflow}. Transitioning to ideation stage and exploration phase.")
                    st.session_state["stage"] = "ideation" # Or next stage defined by workflow
                    st.session_state["phase"] = "exploration" # Default phase for ideation
                    st.session_state["conversation_history"] = [] # Clear for new phase
                    st.session_state.pop("intake_answers", None) # Clear intake answers
                    if "user_id" in st.session_state:
                        save_session(st.session_state["user_id"], dict(st.session_state))
                    st.rerun()

            # --- Ideation Stage Logic (Specific to Value Proposition workflow) ---
            elif selected_workflow == "value_prop" and st.session_state.get("stage") == "ideation":
                logging.info("DEBUG: Entering ideation stage for Value Proposition workflow.")

                # Initialize Persona and Workflow if not already done
                if "coach_persona_instance" not in st.session_state:
                    st.session_state.coach_persona_instance = CoachPersona()
                
                if "value_prop_workflow_instance" not in st.session_state or st.session_state.get("current_workflow_type") != "value_prop":
                    st.session_state.value_prop_workflow_instance = ValuePropWorkflow(
                        context={"persona_instance": st.session_state.coach_persona_instance}
                    )
                    st.session_state.current_workflow_type = "value_prop"
                    # Ensure conversation history is clean for a new workflow instance start
                    st.session_state.conversation_history = []
                    logging.info("ValuePropWorkflow instance created and conversation history reset.")

                workflow_instance = st.session_state.value_prop_workflow_instance

                # Get initial message from workflow if conversation history is empty
                if not st.session_state.get("conversation_history"):
                    logging.info("ValuePropWorkflow: Conversation history empty, attempting to get initial prompt.")
                    # Pass empty string to process_user_input to get initial greeting/prompt
                    initial_assistant_prompt = workflow_instance.process_user_input("")
                    if initial_assistant_prompt:
                        st.session_state.conversation_history.append({"role": "assistant", "text": initial_assistant_prompt})
                        logging.info(f"ValuePropWorkflow: Initial prompt received: {initial_assistant_prompt}")
                        st.rerun() # Rerun to display the initial message
                    else:
                        logging.warning("ValuePropWorkflow: process_user_input with empty string did not return an initial prompt.")
                
                # Display conversation history
                if "conversation_history" in st.session_state:
                    for i, message in enumerate(st.session_state["conversation_history"]):
                        with st.chat_message(message["role"]):
                            citations_for_render = message.get("citations", [])
                            render_response_with_citations(message["text"], citations_for_render)
                
                # Handle user input
                user_input = st.chat_input(placeholder="What are your thoughts on the value proposition?")

                if user_input:
                    st.session_state.conversation_history.append({"role": "user", "text": user_input})
                    with st.chat_message("assistant"):
                        with st.spinner("Coach is thinking..."):
                            assistant_response = workflow_instance.process_user_input(user_input)
                            if assistant_response is None:
                                logging.error("ValuePropWorkflow.process_user_input returned None. User input: %s", user_input)
                                assistant_response = "I'm sorry, I encountered an issue and couldn't generate a response. Please try again."
                            st.session_state.conversation_history.append({"role": "assistant", "text": assistant_response})
                            render_response_with_citations(assistant_response, [])
                    st.rerun()

            # Placeholder for other workflows if they have an "ideation" or other stages
            elif selected_workflow != "value_prop" and st.session_state.get("stage") == "ideation":
                st.info(f"Ideation stage for '{selected_workflow}' workflow is not yet implemented.")
                # Potentially render a generic chat interface or workflow-specific UI here

            elif st.session_state.get("stage") is not None: # Some other stage for a selected workflow
                 st.info(f"Workflow '{selected_workflow}' is at stage '{st.session_state.get('stage')}'. UI for this stage is not yet fully implemented.")

        else: # No workflow selected
            st.info("Please select a topic from the sidebar to begin.")
    except Exception as e:
        logging.error(f"Error in main application logic: {e}", exc_info=True)
        st.error(f"A critical error occurred: {e}")
        st.stop()
    finally:
        st.markdown("---")
        general_feedback_text = render_general_feedback_trigger()
        if general_feedback_text:
            st.session_state["general_session_feedback"] = general_feedback_text
            st.session_state["general_session_feedback_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if "user_id" in st.session_state:
                save_session(st.session_state["user_id"], dict(st.session_state))

if __name__ == "__main__":
    asyncio.run(main())
