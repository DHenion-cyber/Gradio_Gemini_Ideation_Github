import streamlit as st
import sys
import os
import datetime # Added for feedback timestamp

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.conversation_manager import (
    initialize_conversation_state, run_intake_flow, get_intake_questions,
    is_out_of_scope, route_conversation, # route_conversation is key for the new flow
     # Kept for commented out sections
)
from src.persistence_utils import save_session # Added for saving feedback
from src.ui_components import apply_responsive_css, privacy_notice, render_response_with_citations, progress_bar, render_feedback_box # Added render_feedback_box
from ui.sidebar import create_sidebar
from ui.summary_panel import display_summary_panel

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize conversation state
if "conversation_initialized" not in st.session_state or st.session_state.get("new_chat_triggered"):
    try:
        initialize_conversation_state(new_chat=True)
        st.session_state["conversation_initialized"] = True
        st.session_state["new_chat_triggered"] = False # Reset the flag
        logging.info("Conversation state initialized successfully (new chat).")
    except Exception as e:
        logging.error(f"Error initializing conversation state: {e}")
        st.error(f"An error occurred during initialization: {e}")
        st.stop() # Stop Streamlit execution if initialization fails
else:
    logging.info("Conversation state already initialized.")

st.set_page_config(page_title="Chatbot UI", layout="wide")
st.title("Digital Health Innovation Chats")

# Apply custom CSS for responsive design
apply_responsive_css()

# Display privacy notice
privacy_notice()

# Create the sidebar content
create_sidebar()

# Display token usage and session time
st.sidebar.subheader("Session Metrics")
st.sidebar.write(f"Tokens Used (Session): {st.session_state['token_usage']['session']}")
st.sidebar.write(f"Tokens Used (Daily): {st.session_state['token_usage']['daily']}")
progress_bar(st.session_state["turn_count"])

# Main application logic
# Define the sections for the horizontal header
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
        # "Value Proposition" section is active if stage is "ideation" (which covers all new phases)
        elif current_stage == "ideation" and section == "Value Proposition":
            is_active = True
        # Potentially add more specific active states based on current_phase for other sections if needed
        
        st.markdown(
            f'<div class="header-item {"active" if is_active else ""}">{section}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

try:
    render_horizontal_header(st.session_state["stage"], st.session_state.get("phase"))

    if st.session_state["stage"] == "intake":
        logging.info("DEBUG: Entering intake stage.")
        intake_questions = get_intake_questions()
        current_intake_index = st.session_state["intake_index"]

        if current_intake_index < len(intake_questions):
            current_question = intake_questions[current_intake_index]
            with st.form(key=f"intake_form_{current_intake_index}"):
                st.markdown(current_question)
                user_response_input = st.text_input("Your response:", key=f"intake_q_{current_intake_index}_input")
                submitted = st.form_submit_button(label="Submit")

            if submitted:
                if user_response_input:
                    run_intake_flow(user_response_input)
                    st.rerun()
                else:
                    st.warning("Please enter a response to proceed.")
        else: # Intake complete
            logging.info("Intake complete. Transitioning to ideation stage and exploration phase.")
            st.session_state["stage"] = "ideation" # Set stage for the new phase-based flow
            st.session_state["phase"] = "exploration" # Initialize to the first phase
            logging.info(f"DEBUG: Before clearing history. Length: {len(st.session_state.get('conversation_history', []))}")
            st.session_state["conversation_history"] = [] # Clear history to hide intake answers
            st.session_state.pop("intake_answers", None) # Optional cleanup of intake_answers
            logging.info(f"DEBUG: After clearing history and popping intake_answers. History Length: {len(st.session_state.get('conversation_history', []))}")
            # Save the session state AFTER clearing history and before rerun
            from src.persistence_utils import save_session # Ensure save_session is available
            if "user_id" in st.session_state:
                save_session(st.session_state["user_id"], dict(st.session_state))
                logging.info(f"DEBUG: Session saved after clearing history for user {st.session_state['user_id']}.")
            else:
                logging.warning("DEBUG: user_id not found in session state, cannot save session after clearing history.")
            # st.session_state["_just_cleared_for_ideation"] = True # REMOVE FLAG
            st.rerun()

    elif st.session_state["stage"] == "ideation": # Simplified condition for this block
        # Defense-in-depth: Remove any messages with meta=="intake" from conversation_history
        if "conversation_history" in st.session_state:
            st.session_state["conversation_history"] = [
                msg for msg in st.session_state["conversation_history"]
                if msg.get("meta") != "intake"
            ]
        logging.info(f"DEBUG: Entered ideation block. History length after intake meta check: {len(st.session_state.get('conversation_history', []))}")
        # Explicitly ensure phase is correct if just transitioned to ideation or if phase is unexpected
        expected_ideation_phases = ["exploration", "development", "refinement", "summary"]
        if st.session_state.get("phase") not in expected_ideation_phases:
            logging.warning(f"Ideation stage entered with unexpected phase '{st.session_state.get('phase')}'. Resetting to 'exploration'.")
            st.session_state["phase"] = "exploration"
        
        current_phase = st.session_state.get("phase", "exploration") # Default to exploration if somehow still not set
        
        logging.info(f"DEBUG: Before initial prompt check. History length: {len(st.session_state.get('conversation_history', []))}, Current phase: {current_phase}")
        # If it's the start of ideation (e.g. no conversation history yet in this stage), ensure phase is exploration
        if not st.session_state.get("conversation_history"):
            if current_phase != "exploration":
                logging.warning(f"DEBUG: Ideation start detected (empty history) with phase '{current_phase}'. Forcing to 'exploration'.")
                current_phase = "exploration"
                st.session_state["phase"] = "exploration" # Persist this change
            
            # If it's the true start of exploration (empty history), get an initial prompt from the assistant.
            # The inner check `if not st.session_state.get("conversation_history")` is redundant if the outer one is true,
            # but kept for safety during debugging.
            if not st.session_state.get("conversation_history"):
                logging.info("DEBUG: Exploration phase started with empty history (triggering initial prompt). Getting initial assistant prompt.")
                initial_assistant_prompt, next_phase_after_init = route_conversation("", st.session_state.scratchpad)
                if initial_assistant_prompt:
                    st.session_state["conversation_history"].append({"role": "assistant", "text": initial_assistant_prompt})
                    logging.info(f"DEBUG: Initial assistant prompt for exploration: {initial_assistant_prompt}. New phase: {st.session_state.get('phase')}. History length: {len(st.session_state.get('conversation_history', []))}")
                    st.rerun() # Rerun to display the initial assistant message

        logging.info(f"DEBUG: In ideation/phase-based flow. Current phase: {current_phase}. History length: {len(st.session_state.get('conversation_history', []))}")

        # Display conversation history
        if "conversation_history" in st.session_state:
            for i, message in enumerate(st.session_state["conversation_history"]):
                with st.chat_message(message["role"]):
                    citations_for_render = message.get("citations", [])
                    render_response_with_citations(message["text"], citations_for_render)

                    if message["role"] == "assistant" and "feedback" not in message: # Only show if no feedback yet
                        feedback_key_prefix = f"feedback_msg_{i}"
                        feedback_text = render_feedback_box(feedback_key_prefix)
                        if feedback_text:
                            # Ensure message is a dictionary and can be updated
                            if isinstance(st.session_state["conversation_history"][i], dict):
                                st.session_state["conversation_history"][i]["feedback"] = feedback_text
                                st.session_state["conversation_history"][i]["feedback_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                                if "user_id" in st.session_state:
                                    save_session(st.session_state["user_id"], dict(st.session_state))
                                    logging.info(f"Feedback saved for message {i} by user {st.session_state['user_id']}.")
                                    st.caption("Thank you for your feedback!") # Give user confirmation
                                    st.rerun() # Rerun to hide the input box and show caption
                                else:
                                    logging.warning("user_id not found, cannot save feedback.")
                            else:
                                logging.error(f"Message at index {i} is not a dictionary, cannot save feedback.")
                    elif message["role"] == "assistant" and "feedback" in message:
                        st.caption(f"Feedback received: \"{message['feedback']}\"")

        # Commented out sections for Actionable Recommendations and Summary Report
        # These can be integrated into the phase logic later if needed.
        # st.subheader("Actionable Recommendations")
        # ...
        logging.info(f"DEBUG: Just before summary/chat_input block. Current phase: {current_phase}, Stage: {st.session_state['stage']}")
        
        # Render summary panel ONLY if current_phase is "summary"
        if current_phase == "summary":
            # display_summary_panel() # Intentionally commented out for debugging
            logging.info(f"DEBUG: display_summary_panel() would have been called because current_phase is 'summary' (but it is commented out).")

        # Render chat input ONLY if current_phase is NOT "summary"
        # And only if there's already an assistant message to respond to, or it's not the very start.
        if current_phase != "summary":
            logging.info(f"DEBUG: Attempting to render chat_input because current_phase is '{current_phase}'.")
            # st.error("EXPLORATION PHASE IS ACTIVE - CHAT INPUT SHOULD BE BELOW") # REMOVED DEBUGGING
            user_input = st.chat_input(placeholder="Your response")
            if user_input:
                logging.info(f"DEBUG: User input received: {user_input}")
                if user_input.lower() == "/new idea":
                    initialize_conversation_state(new_chat=True)
                    st.session_state["new_chat_triggered"] = False # Reset the flag
                    st.rerun()
                elif is_out_of_scope(user_input):
                    logging.info("DEBUG: Input identified as out of scope.") # Corrected indentation
                    st.warning("Your input seems to be out of scope. Please refrain from entering personal health information, market sizing, or financial projections.")
                    # Display the out-of-scope warning as an assistant message in history
                    st.session_state["conversation_history"].append({
                        "role": "assistant",
                        "text": "Your input seems to be out of scope. Please refrain from entering personal health information, market sizing, or financial projections."
                    })
                    st.rerun() # Rerun to show the warning in chat
                else:
                    st.session_state["conversation_history"].append({"role": "user", "text": user_input})
                    logging.info("DEBUG: User message appended to history.")

                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            logging.info(f"DEBUG: Calling route_conversation for phase {st.session_state.get('phase')}.")
                            assistant_response, next_phase = route_conversation(user_input, st.session_state.scratchpad)
                            # route_conversation already updates st.session_state["phase"]
                            logging.info(f"DEBUG: route_conversation completed. Assistant response received. New phase: {st.session_state.get('phase')}")
                            
                            st.session_state["conversation_history"].append({"role": "assistant", "text": assistant_response})
                            logging.info("DEBUG: Assistant message appended to history.")
                            
                            # Citations are not directly returned by route_conversation in this setup.
                            # If individual phase handlers generate citations, they'd need to be stored and retrieved.
                            render_response_with_citations(assistant_response, [])
                    logging.info("DEBUG: Rerunning after user input processing.")
                    st.rerun()
except Exception as e:
    logging.error(f"Error in main application logic: {e}", exc_info=True) # Added exc_info for better debugging
    st.error(f"An critical error occurred: {e}")
    # Consider if st.stop() is always appropriate or if more graceful error handling is needed
    st.stop()