"""
Main Streamlit application file for the Digital Health Innovation Chatbot UI.
This file is responsible for managing the overall UI flow and specifically handles
the detailed stage transitions for workflows like Value Proposition. It updates
st.session_state['stage'] to reflect granular phases such as 'intake', 'ideation',
'recommendation', 'iteration', and 'summary' for the Value Proposition workflow,
ensuring the UI syncs with the current phase of user interaction.
"""
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

def render_horizontal_header(current_stage, current_phase): # current_phase is not strictly used now but kept for signature consistency
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
        elif current_stage in ["ideation", "recommendation", "iteration"] and section == "Value Proposition":
            is_active = True
        elif current_stage == "summary" and section == "Session Summary": # Assuming "summary" stage maps to "Session Summary" header
            is_active = True
        # Note: "Actionable Recommendations" section might need its own stage if it's a distinct part of the flow
        # For now, it's not directly tied to the value_prop stages being added.
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
        # Valid post-intake stages for value_prop.
        valid_post_intake_stages = ["ideation", "recommendation", "iteration", "summary"]

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
                    logging.info(f"Intake complete for {selected_workflow}. Transitioning to ideation stage.")
                    # Enforce: Intake MUST transition to ideation.
                    assert st.session_state.get("stage") == "intake", "Stage must be 'intake' before transitioning to 'ideation'."
                    st.session_state["stage"] = "ideation"
                    st.session_state["conversation_history"] = [
                        {"role": "assistant", "text": "Great! We've completed the intake. Now, let's move on to crafting your Value Proposition. What are your initial thoughts or ideas for the value proposition?"}
                    ]
                    st.session_state.pop("intake_answers", None) # Clear intake answers
                    if "user_id" in st.session_state:
                        save_session(st.session_state["user_id"], dict(st.session_state))
                    st.rerun()

            # --- Value Proposition Workflow Stages ---
            elif selected_workflow == "value_prop" and st.session_state.get("stage") in ["ideation", "recommendation", "iteration", "summary"]:
                current_vp_stage = st.session_state.get("stage")
                logging.info(f"DEBUG: Entering Value Proposition workflow, stage: {current_vp_stage}.")

                # Initialize Persona and Workflow if not already done
                if "coach_persona_instance" not in st.session_state:
                    st.session_state.coach_persona_instance = CoachPersona()
                
                if "value_prop_workflow_instance" not in st.session_state or st.session_state.get("current_workflow_type") != "value_prop":
                    st.session_state.value_prop_workflow_instance = ValuePropWorkflow(
                        context={"persona_instance": st.session_state.coach_persona_instance}
                    )
                    st.session_state.current_workflow_type = "value_prop"
                    # Ensure conversation history is clean for a new workflow instance start, unless already populated by intake transition
                    if not st.session_state.get("conversation_history"):
                        st.session_state.conversation_history = []
                    logging.info("ValuePropWorkflow instance created/verified.")

                workflow_instance = st.session_state.value_prop_workflow_instance

                # Display conversation history (common for ideation, recommendation, iteration)
                if current_vp_stage in ["ideation", "recommendation", "iteration"]:
                    if "conversation_history" in st.session_state:
                        for i, message in enumerate(st.session_state["conversation_history"]):
                            with st.chat_message(message["role"]):
                                citations_for_render = message.get("citations", [])
                                render_response_with_citations(message["text"], citations_for_render)
                
                # --- Ideation Stage ---
                if current_vp_stage == "ideation":
                    user_input = st.chat_input(placeholder="What are your thoughts on the value proposition?")
                    if user_input:
                        st.session_state.conversation_history.append({"role": "user", "text": user_input})
                        with st.chat_message("assistant"):
                            with st.spinner("Coach is thinking..."):
                                assistant_response = workflow_instance.process_user_input(user_input)
                                if assistant_response is None:
                                    assistant_response = "I'm sorry, I encountered an issue. Please try again."
                                st.session_state.conversation_history.append({"role": "assistant", "text": assistant_response})
                                render_response_with_citations(assistant_response, [])
                        st.rerun()
                    
                    if st.button("Proceed to Recommendation Phase"):
                        # Enforce: Ideation MUST transition to recommendation.
                        assert st.session_state.get("stage") == "ideation", "Stage must be 'ideation' before transitioning to 'recommendation'."
                        st.session_state["stage"] = "recommendation"
                        st.session_state.conversation_history.append({
                            "role": "assistant",
                            "text": "Okay, let's move to the recommendation phase. Based on our discussion, I'll provide some targeted recommendations for your value proposition."
                        })
                        # Potentially call a workflow method to generate initial recommendations here
                        # For now, just transition and let the user prompt or workflow handle next steps.
                        if "user_id" in st.session_state: save_session(st.session_state["user_id"], dict(st.session_state))
                        st.rerun()

                # --- Recommendation Stage ---
                elif current_vp_stage == "recommendation":
                    user_input = st.chat_input(placeholder="What do you think of these recommendations? Or ask for more.")
                    if user_input:
                        st.session_state.conversation_history.append({"role": "user", "text": user_input})
                        with st.chat_message("assistant"):
                            with st.spinner("Coach is thinking..."):
                                # Assuming process_user_input handles being in recommendation phase
                                assistant_response = workflow_instance.process_user_input(user_input)
                                if assistant_response is None:
                                    assistant_response = "I'm sorry, I encountered an issue. Please try again."
                                st.session_state.conversation_history.append({"role": "assistant", "text": assistant_response})
                                render_response_with_citations(assistant_response, [])
                        st.rerun()

                    if st.button("Proceed to Iteration Phase"):
                        # Enforce: Recommendation MUST transition to iteration.
                        assert st.session_state.get("stage") == "recommendation", "Stage must be 'recommendation' before transitioning to 'iteration'."
                        st.session_state["stage"] = "iteration"
                        st.session_state.conversation_history.append({
                            "role": "assistant",
                            "text": "Great! Now let's iterate on these ideas. Feel free to suggest changes, ask for refinements, or explore alternatives."
                        })
                        if "user_id" in st.session_state: save_session(st.session_state["user_id"], dict(st.session_state))
                        st.rerun()
                
                # --- Iteration Stage ---
                elif current_vp_stage == "iteration":
                    user_input = st.chat_input(placeholder="How would you like to refine the value proposition?")
                    if user_input:
                        st.session_state.conversation_history.append({"role": "user", "text": user_input})
                        with st.chat_message("assistant"):
                            with st.spinner("Coach is thinking..."):
                                assistant_response = workflow_instance.process_user_input(user_input)
                                if assistant_response is None:
                                    assistant_response = "I'm sorry, I encountered an issue. Please try again."
                                st.session_state.conversation_history.append({"role": "assistant", "text": assistant_response})
                                render_response_with_citations(assistant_response, [])
                        st.rerun()

                    if st.button("Finalize and Proceed to Summary"):
                        # Enforce: Iteration MUST transition to summary.
                        assert st.session_state.get("stage") == "iteration", "Stage must be 'iteration' before transitioning to 'summary'."
                        st.session_state["stage"] = "summary"
                        # Generate a pre-summary message or let the summary stage handle it.
                        st.session_state.conversation_history.append({
                            "role": "assistant",
                            "text": "Excellent! We've iterated on the value proposition. Let's now move to the summary of our work."
                        })
                        if "user_id" in st.session_state: save_session(st.session_state["user_id"], dict(st.session_state))
                        st.rerun()

                # --- Summary Stage ---
                elif current_vp_stage == "summary":
                    st.subheader("Value Proposition Summary")
                    # final_summary = workflow_instance.generate_final_summary() # Assuming this method exists
                    # For now, let's use a placeholder or a generic summary from conversation_manager
                    from conversation_manager import generate_final_summary_report # Import if not already
                    final_summary_text = generate_final_summary_report() # Uses scratchpad
                    
                    st.markdown(final_summary_text if final_summary_text else "No summary could be generated at this time.")
                    
                    # Display conversation history for context if desired, or just the summary.
                    # For brevity, we'll omit full history here but it could be an option.

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Restart Value Proposition Workflow"):
                            st.session_state.stage = "intake"
                            st.session_state.intake_index = 0
                            st.session_state.conversation_history = [] # Clear history for restart
                            # Potentially clear value_prop_workflow_instance or re-initialize
                            st.session_state.pop("value_prop_workflow_instance", None)
                            st.session_state.pop("current_workflow_type", None)
                            logging.info("Value Proposition workflow restarted by user.")
                            if "user_id" in st.session_state: save_session(st.session_state["user_id"], dict(st.session_state))
                            st.rerun()
                    with col2:
                        if st.button("Choose Another Workflow / Exit"):
                            st.session_state.selected_workflow_key = None # This will trigger sidebar selection
                            st.session_state.stage = None # Clear stage
                            st.session_state.conversation_history = []
                            st.session_state.pop("value_prop_workflow_instance", None)
                            st.session_state.pop("current_workflow_type", None)
                            logging.info("User opted to choose another workflow or exit after summary.")
                            if "user_id" in st.session_state: save_session(st.session_state["user_id"], dict(st.session_state))
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
