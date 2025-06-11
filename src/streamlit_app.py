import os
import sys
import streamlit as st
import datetime # Added for feedback timestamp
import cleanup # Assuming cleanup.py is in the same directory or PYTHONPATH

# Add the project root to the Python path to enable absolute imports
# This allows 'from src.module import ...'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.persistence_utils import ensure_db, save_session # Import ensure_db
from src.conversation_manager import (
    initialize_conversation_state, run_intake_flow, get_intake_questions,
    is_out_of_scope, route_conversation,
)
from src.ui_components import (
    apply_responsive_css, privacy_notice, render_response_with_citations,
    progress_bar, render_general_feedback_trigger, render_final_session_feedback_prompt
)
from ui.sidebar import create_sidebar
# from ui.summary_panel import display_summary_panel # display_summary_panel is commented out in main logic
from src.persona_simulation import get_persona_response

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize conversation state (this runs once per session unless new_chat is triggered)
if "conversation_initialized" not in st.session_state or st.session_state.get("new_chat_triggered"):
    try:
        # ensure_db() is called within initialize_conversation_state and at module level in persistence_utils
        initialize_conversation_state(new_chat=True) # This will also call ensure_db()
        st.session_state["conversation_initialized"] = True
        st.session_state["new_chat_triggered"] = False # Reset the flag
        logging.info("Conversation state initialized successfully (new chat).")
    except Exception as e:
        logging.error(f"Error initializing conversation state: {e}", exc_info=True)
        st.error(f"An error occurred during initialization: {e}")
        st.stop() # Stop Streamlit execution if initialization fails
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

def main():
    st.set_page_config(page_title="Chatbot UI", layout="wide")

    # Debug prints moved here
    print("DEBUG_STREAMLIT_APP_MAIN_FUNCTION_START")
    sys.stdout.flush()
    print("DEBUG: Does /data exist?", os.path.exists("/data"))
    sys.stdout.flush()
    print("DEBUG: Is /data a directory?", os.path.isdir("/data"))
    sys.stdout.flush()
    if os.path.exists("/data"):
        print("DEBUG: /data permissions (octal):", oct(os.stat("/data").st_mode))
        sys.stdout.flush()
        try:
            testfile = "/data/test_can_write_main.txt"
            with open(testfile, "w") as f:
                f.write("write test from main")
            print("DEBUG: Able to write to /data from main.")
            sys.stdout.flush()
            os.remove(testfile)
        except Exception as e:
            print("DEBUG: Unable to write to /data from main:", e)
            sys.stdout.flush()
    else:
        print("DEBUG: /data does not exist at main function start!")
        sys.stdout.flush()

    st.title("Digital Health Innovation Chats")

    apply_responsive_css()
    privacy_notice()
    create_sidebar()

    st.sidebar.subheader("Session Metrics")
    st.sidebar.write(f"Tokens Used (Session): {st.session_state.get('token_usage', {}).get('session', 0)}")
    st.sidebar.write(f"Tokens Used (Daily): {st.session_state.get('token_usage', {}).get('daily', 0)}")
    progress_bar(st.session_state.get("turn_count", 0))

    try:
        render_horizontal_header(st.session_state.get("stage"), st.session_state.get("phase"))

        if st.session_state.get("stage") == "intake":
            logging.info("DEBUG: Entering intake stage.")
            intake_questions = get_intake_questions()
            current_intake_index = st.session_state.get("intake_index", 0)

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
            else:
                logging.info("Intake complete. Transitioning to ideation stage and exploration phase.")
                st.session_state["stage"] = "ideation"
                st.session_state["phase"] = "exploration"
                st.session_state["conversation_history"] = []
                st.session_state.pop("intake_answers", None)
                if "user_id" in st.session_state:
                    save_session(st.session_state["user_id"], dict(st.session_state))
                st.rerun()

        elif st.session_state.get("stage") == "ideation":
            if "conversation_history" in st.session_state:
                st.session_state["conversation_history"] = [
                    msg for msg in st.session_state["conversation_history"]
                    if msg.get("meta") != "intake"
                ]

            current_phase = st.session_state.get("phase", "exploration")
            expected_ideation_phases = ["exploration", "development", "refinement", "summary"]
            if current_phase not in expected_ideation_phases:
                st.session_state["phase"] = "exploration"
                current_phase = "exploration"

            if not st.session_state.get("conversation_history"):
                if current_phase != "exploration":
                    st.session_state["phase"] = "exploration"
                    current_phase = "exploration"
                logging.info("DEBUG: Exploration phase started with empty history. Getting initial assistant prompt.")
                initial_assistant_prompt, _ = route_conversation("", st.session_state.get("scratchpad", {}))
                if initial_assistant_prompt:
                    st.session_state["conversation_history"].append({"role": "assistant", "text": initial_assistant_prompt})
                    st.rerun()

            if "conversation_history" in st.session_state:
                for i, message in enumerate(st.session_state["conversation_history"]):
                    with st.chat_message(message["role"]):
                        citations_for_render = message.get("citations", [])
                        render_response_with_citations(message["text"], citations_for_render)

            if current_phase == "summary":
                logging.info(f"DEBUG: display_summary_panel() would be called (commented out).")
                if not st.session_state.get("final_feedback_submitted_this_session", False):
                    final_feedback_text = render_final_session_feedback_prompt()
                    if final_feedback_text:
                        st.session_state["general_session_feedback"] = final_feedback_text
                        st.session_state["general_session_feedback_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        st.session_state["final_feedback_submitted_this_session"] = True
                        if "user_id" in st.session_state:
                            save_session(st.session_state["user_id"], dict(st.session_state))
                else:
                    st.success("Thank you! Your final feedback has been recorded for this session.")

            if current_phase != "summary":
                # --- Persona Example Button Integration ---
                phase = st.session_state.get("phase", "intake")
                if st.button("Example"):
                    persona_msg = get_persona_response(phase, st.session_state.get("scratchpad"))
                    st.session_state["conversation_history"].append({"role": "user", "text": persona_msg})
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            assistant_response, _ = route_conversation(persona_msg, st.session_state.get("scratchpad", {}))
                            st.session_state["conversation_history"].append({"role": "assistant", "text": assistant_response})
                            render_response_with_citations(assistant_response, [])
                    st.rerun()
                # --- End Persona Example Button Integration ---

                user_input = st.chat_input(placeholder="Your response")

                if user_input:
                    if user_input.lower() == "/new idea":
                        initialize_conversation_state(new_chat=True)
                        st.rerun()
                    elif is_out_of_scope(user_input):
                        st.warning("Your input seems to be out of scope. Please refrain from entering personal health information, market sizing, or financial projections.")
                        st.session_state["conversation_history"].append({
                            "role": "assistant",
                            "text": "Your input seems to be out of scope. Please refrain from entering personal health information, market sizing, or financial projections."
                        })
                        st.rerun()
                    else:
                        st.session_state["conversation_history"].append({"role": "user", "text": user_input})
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking..."):
                                assistant_response, _ = route_conversation(user_input, st.session_state.get("scratchpad", {}))
                                st.session_state["conversation_history"].append({"role": "assistant", "text": assistant_response})
                                render_response_with_citations(assistant_response, [])
                        st.rerun()
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
