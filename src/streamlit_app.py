"""
Main Streamlit application file for the Digital Health Innovation Chatbot UI.
Handles UI flow, workflow selection, and chat rendering.
"""
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
                console.log("Feedback submitted:", feedbackText);
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

# --- IMPORTS ---
from src.workflows.registry import WORKFLOWS
from src.persistence_utils import ensure_db, save_session
from src.conversation_manager import (
    initialize_conversation_state, run_intake_flow, get_intake_questions,
    is_out_of_scope, generate_assistant_response,
)
from src.workflows.value_prop import ValuePropWorkflow
from src.personas.coach import CoachPersona
from src.ui_components import (
    apply_responsive_css, privacy_notice, render_response_with_citations
)

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONVERSATION STATE INIT ---
if "conversation_initialized" not in st.session_state or st.session_state.get("new_chat_triggered"):
    try:
        initialize_conversation_state(new_chat=True)
        st.session_state["conversation_initialized"] = True
        st.session_state["new_chat_triggered"] = False
    except Exception as e:
        st.error(f"Initialization error: {e}")
        st.stop()

# --- WORKFLOW NAME FORMATTER ---
def format_workflow_name(name_key):
    if name_key == "value_prop":
        return "Value Proposition"
    return ' '.join(word.capitalize() for word in name_key.split('_'))

# --- SIDEBAR: WORKFLOW SELECTOR & PHASES ---
with st.sidebar:
    # Map user-friendly names → workflow keys
    formatted_workflow_options = {
        format_workflow_name(k): k
        for k in WORKFLOWS.keys()
    }
    placeholder = "Select"
    options = [placeholder] + list(formatted_workflow_options.keys())

    selected_display = st.selectbox(
        "Workflow",
        options,
        index=0,
        key="selected_workflow_display_name"
    )

    if selected_display != placeholder:
        st.session_state.selected_workflow_key = formatted_workflow_options[selected_display]
    else:
        st.session_state.selected_workflow_key = None

    st.markdown("---")

    # ---- PHASE DISPLAY SECTION ----
    key = st.session_state.get("selected_workflow_key")
    logging.info(f"SIDEBAR: Selected workflow key: {key}")

    if key:
        # Ensure workflow instance exists (extend for new workflows)
        workflow_instance_key = f"{key}_workflow_instance"
        persona_instance_key = "coach_persona_instance"  # For value_prop only
        logging.info(f"SIDEBAR: Workflow instance key: {workflow_instance_key}")

        if workflow_instance_key not in st.session_state:
            logging.info(f"SIDEBAR: Creating new workflow instance for {key}")
            # Only create if missing (supports value_prop, extend for more)
            if key == "value_prop":
                if persona_instance_key not in st.session_state:
                    st.session_state[persona_instance_key] = CoachPersona()
                    logging.info(f"SIDEBAR: Created new CoachPersona instance.")
                st.session_state[workflow_instance_key] = ValuePropWorkflow(
                    context={"persona_instance": st.session_state[persona_instance_key]}
                )
                logging.info(f"SIDEBAR: ValuePropWorkflow instance created.")
            else:
                st.session_state[workflow_instance_key] = None  # Placeholder for future workflows
                logging.info(f"SIDEBAR: Placeholder for {key} workflow instance set to None.")
        else:
            logging.info(f"SIDEBAR: Workflow instance for {key} already exists in session_state.")

        workflow_instance = st.session_state.get(workflow_instance_key)
        logging.info(f"SIDEBAR: Retrieved workflow_instance: {workflow_instance}")

        # Only render if workflow has phases
        if workflow_instance and hasattr(workflow_instance, "get_all_phases"):
            logging.info(f"SIDEBAR: workflow_instance has get_all_phases method.")
            phases = workflow_instance.get_all_phases()
            logging.info(f"SIDEBAR: Phases from get_all_phases(): {phases}")
            current_phase = getattr(workflow_instance, "current_phase", None)
            logging.info(f"SIDEBAR: Current phase: {current_phase}")
            if phases:
                for phase in phases:
                    logging.info(f"SIDEBAR: Displaying phase: {phase}")
                    is_current = (phase == current_phase)
                    style = "font-weight:bold; color:#007BFF;" if is_current else "color:#888;"
                    st.markdown(
                        f"- <span style='{style}'>{format_workflow_name(phase)}</span>",
                        unsafe_allow_html=True
                    )
            else:
                logging.info(f"SIDEBAR: No phases to display for {key}.")
        elif workflow_instance:
            logging.warning(f"SIDEBAR: workflow_instance for {key} does NOT have get_all_phases method.")
        else:
            logging.warning(f"SIDEBAR: workflow_instance for {key} is None, cannot display phases.")
    else:
        logging.info("SIDEBAR: No workflow key selected, not displaying phases.")

# --- MAIN APP LOGIC ---
async def main():
    apply_responsive_css()
    privacy_notice()

    selected_workflow = st.session_state.get("selected_workflow_key")
    if selected_workflow is None:
        st.info("Please select a workflow from the sidebar to begin.")
        return

    # Ensure workflow instance exists (value_prop example)
    if selected_workflow == "value_prop":
        if "value_prop_workflow_instance" not in st.session_state:
            st.session_state.coach_persona_instance = CoachPersona()
            st.session_state.value_prop_workflow_instance = ValuePropWorkflow(
                context={"persona_instance": st.session_state.coach_persona_instance}
            )
        workflow_instance = st.session_state.value_prop_workflow_instance
    else:
        workflow_instance = None  # Extend logic for other workflows

    # Intake phase logic (for value_prop workflow)
    if selected_workflow == "value_prop" and st.session_state.get("stage") not in ["ideation", "recommendation", "iteration", "summary"]:
        st.session_state.stage = "intake"
        st.session_state.intake_index = st.session_state.get("intake_index", 0)

    # -- Intake logic --
    if selected_workflow == "value_prop" and st.session_state.get("stage") == "intake":
        intake_questions = get_intake_questions()
        idx = st.session_state.get("intake_index", 0)
        if idx < len(intake_questions):
            question = intake_questions[idx]
            form_key = f"intake_form_{selected_workflow}_{idx}"
            with st.form(key=form_key):
                st.markdown(question)
                user_response_input = st.text_area(
                    label="",
                    placeholder="Please provide your detailed response here...",
                    key=f"intake_q_{selected_workflow}_{idx}_input",
                    height=100
                )
                col1, col2 = st.columns([9, 1])
                with col2:
                    submitted = st.form_submit_button(label="➤")
            if submitted:
                if user_response_input:
                    run_intake_flow(user_response_input)
                    st.rerun()
                else:
                    st.warning("Please enter a response to proceed.")
            return  # Prevent further UI rendering
        else:
            # Intake complete, transition
            st.session_state.stage = "ideation"
            st.rerun()

    # --- Chat stages ---
    if selected_workflow == "value_prop" and st.session_state.get("stage") in ["ideation", "recommendation", "iteration", "summary"]:
        workflow_instance = st.session_state.value_prop_workflow_instance
        # Chat message history
        if "history" not in st.session_state:
            st.session_state.history = []
        if "conversation_history" in st.session_state and st.session_state.conversation_history and not st.session_state.history:
            # Migrate old to new format if needed
            for msg_old in st.session_state.conversation_history:
                role = msg_old.get("role")
                content = msg_old.get("text")
                if role and content:
                    st.session_state.history.append({"role": role, "content": content})

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
                            st.write(content)

        # Chat input logic
        current_stage = st.session_state.get("stage")
        chat_input_placeholder = {
            "ideation": "What are your thoughts on the value proposition?",
            "recommendation": "What do you think of these recommendations? Or ask for more.",
            "iteration": "How would you like to refine the value proposition?",
        }.get(current_stage, "Type your message...")

        user_input = st.chat_input(chat_input_placeholder)
        if user_input:
            st.session_state.history.append({"role": "user", "content": user_input})
            if workflow_instance and hasattr(workflow_instance, 'process_user_input'):
                with st.spinner("Coach is thinking..."):
                    response_data = workflow_instance.process_user_input(user_input)
                    assistant_content = ""
                    assistant_citations = []
                    if isinstance(response_data, str):
                        assistant_content = response_data
                    elif isinstance(response_data, dict):
                        assistant_content = response_data.get("text", "I'm sorry, I encountered an issue processing that.")
                        assistant_citations = response_data.get("citations", [])
                    else:
                        assistant_content = "I'm sorry, I encountered an unexpected response format. Please try again."
                    st.session_state.history.append({
                        "role": "assistant",
                        "content": assistant_content,
                        "citations": assistant_citations
                    })
            else:
                st.session_state.history.append({"role": "assistant", "content": "Error: Workflow not available to process input."})
            st.rerun()

        # Stage transition buttons (same as before)
        if current_stage == "ideation":
            if st.button("Proceed to Recommendation Phase"):
                st.session_state["stage"] = "recommendation"
                st.session_state.history.append({
                    "role": "assistant",
                    "content": "Okay, let's move to the recommendation phase. Based on our discussion, I'll provide some targeted recommendations for your value proposition."
                })
                st.rerun()
        elif current_stage == "recommendation":
            if st.button("Proceed to Iteration Phase"):
                st.session_state["stage"] = "iteration"
                st.session_state.history.append({
                    "role": "assistant",
                    "content": "Great! Now let's iterate on these ideas. Feel free to suggest changes, ask for refinements, or explore alternatives."
                })
                st.rerun()
        elif current_stage == "iteration":
            if st.button("Finalize and Proceed to Summary"):
                st.session_state["stage"] = "summary"
                st.session_state.history.append({
                    "role": "assistant",
                    "content": "Excellent! We've iterated on the value proposition. Let's now move to the summary of our work."
                })
                st.rerun()
        elif current_stage == "summary":
            st.subheader("Value Proposition Summary")
            # You may want to add your summary report logic here
            st.markdown("Summary generation not yet implemented.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Restart Value Proposition Workflow"):
                    st.session_state.stage = "intake"
                    st.session_state.intake_index = 0
                    st.session_state.history = []
                    st.session_state.pop("value_prop_workflow_instance", None)
                    st.rerun()
            with col2:
                if st.button("Choose Another Workflow / Exit"):
                    st.session_state.selected_workflow_key = None
                    st.session_state.stage = None
                    st.session_state.history = []
                    st.session_state.pop("value_prop_workflow_instance", None)
                    st.rerun()

if __name__ == "__main__":
    asyncio.run(main())
