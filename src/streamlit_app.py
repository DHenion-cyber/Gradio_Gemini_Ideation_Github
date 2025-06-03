import streamlit as st
import sys
import os

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.conversation_manager import (
    initialize_conversation_state, run_intake_flow, get_intake_questions,
    is_out_of_scope, route_conversation, # route_conversation is key for the new flow
     # Kept for commented out sections
)
from src.ui_components import apply_responsive_css, privacy_notice, render_response_with_citations, progress_bar
from ui.sidebar import create_sidebar
from ui.summary_panel import display_summary_panel

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize conversation state
if "conversation_initialized" not in st.session_state:
    try:
        initialize_conversation_state()
        st.session_state["conversation_initialized"] = True
        logging.info("Conversation state initialized successfully.")
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
            st.success("Intake complete. Let's move to ideation!")
            st.rerun()

    elif st.session_state["stage"] == "ideation" or st.session_state.get("phase") in ["exploration", "development", "refinement", "summary"]:
        current_phase = st.session_state.get("phase", "exploration")
        logging.info(f"DEBUG: In ideation/phase-based flow. Current phase: {current_phase}")

        # Display conversation history
        if "conversation_history" in st.session_state:
            for message in st.session_state["conversation_history"]:
                with st.chat_message(message["role"]):
                    citations_for_render = message.get("citations", []) 
                    render_response_with_citations(message["text"], citations_for_render)
        
        # Commented out sections for Actionable Recommendations and Summary Report
        # These can be integrated into the phase logic later if needed.
        # st.subheader("Actionable Recommendations")
        # ...
        if current_phase == "summary":
            display_summary_panel()

        # Chat input for user messages
        user_input = st.chat_input(placeholder="Ask me anything about digital health innovation!")
        if user_input:
            logging.info(f"DEBUG: User input received: {user_input}")
            if is_out_of_scope(user_input):
                logging.info("DEBUG: Input identified as out of scope.")
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