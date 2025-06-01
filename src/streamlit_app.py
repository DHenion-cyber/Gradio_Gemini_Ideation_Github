import streamlit as st
import sys
import os

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.conversation_manager import initialize_conversation_state, run_intake_flow, get_intake_questions
from src.ui_components import apply_responsive_css, privacy_notice, render_response_with_citations, progress_bar
from src.llm_utils import format_citations

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

# Display token usage and session time
st.sidebar.subheader("Session Metrics")
st.sidebar.write(f"Tokens Used (Session): {st.session_state['token_usage']['session']}")
st.sidebar.write(f"Tokens Used (Daily): {st.session_state['token_usage']['daily']}")
progress_bar(st.session_state["turn_count"])

# Main application logic
# Define the sections for the horizontal header
SECTIONS = ["Intake questions", "Value Proposition", "Actionable Recommendations", "Session Summary"]

def render_horizontal_header(current_stage):
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
        # Determine if the current section is active based on the stage
        is_active = False
        if current_stage == "intake" and section == "Intake questions":
            is_active = True
        elif current_stage == "ideation" and section == "Value Proposition":
            is_active = True
        # Add more conditions for other stages/sections as needed

        st.markdown(
            f'<div class="header-item {"active" if is_active else ""}">{section}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

try:
    render_horizontal_header(st.session_state["stage"]) # Render the header at the top

    if st.session_state["stage"] == "intake":
        logging.info("DEBUG: Entering intake stage.")
        # st.subheader("Let's get started!") # Removed, now part of horizontal header
        
        intake_questions = get_intake_questions()
        current_intake_index = st.session_state["intake_index"]

        if current_intake_index < len(intake_questions):
            current_question = intake_questions[current_intake_index]
            
            with st.form(key=f"intake_form_{current_intake_index}"):
                st.markdown(current_question) # Display the question verbatim
                user_response_input = st.text_input("Your response:", key=f"intake_q_{current_intake_index}_input") # Use a generic label for the input box
                submitted = st.form_submit_button(label="Submit") # Changed label back to "Submit"

            # Process form submission outside the form block
            if submitted:
                logging.info(f"DEBUG: Form submitted. user_response_input='{user_response_input}'")
                if user_response_input:
                    logging.info(f"User response received in intake form: {user_response_input}")
                    logging.info("Calling run_intake_flow with user response.")
                    run_intake_flow(user_response_input)
                    logging.info("run_intake_flow with user response completed. Rerunning.")
                    st.rerun() # Rerun to display the next question or transition
                else:
                    logging.warning("Submit button clicked but user_response is empty.")
                    st.warning("Please enter a response to proceed.")
        else:
            logging.info("Intake complete. Transitioning to ideation stage. Rerunning.")
            st.success("Intake complete. Let's move to ideation!")
            st.rerun() # Rerun to transition to ideation stage

        from src.conversation_manager import navigate_value_prop_elements, generate_assistant_response, generate_actionable_recommendations, is_out_of_scope, generate_final_summary_report, build_summary_from_scratchpad
    elif st.session_state["stage"] == "ideation":
        logging.info("DEBUG: Entering ideation stage.")
        # st.subheader("Intake questions") # Removed, now part of horizontal header
        # st.write("This phase is now complete!") # Removed, now part of horizontal header
        # st.subheader("Value Proposition") # Removed, now part of horizontal header
        # st.write("Let's begin!") # Removed, now part of horizontal header

        from src.conversation_manager import navigate_value_prop_elements, generate_assistant_response, generate_actionable_recommendations, is_out_of_scope, generate_final_summary_report, build_summary_from_scratchpad

        logging.info("DEBUG: Calling navigate_value_prop_elements.")
        current_element_info = navigate_value_prop_elements()
        logging.info(f"DEBUG: navigate_value_prop_elements returned: {current_element_info['element_name']}")
        
        if current_element_info["element_name"]:
            st.info(current_element_info["prompt_text"])
            st.caption(current_element_info["follow_up"])
            
            element_input_key = f"element_input_{current_element_info['element_name']}"
            user_element_response = st.text_area(
                "", # Removed "[user input text box]"
                value=st.session_state["scratchpad"].get(current_element_info["element_name"], ""),
                key=element_input_key
            )
            
            if st.button(f"Save {current_element_info['element_name'].replace('_', ' ').title()}", key=f"save_element_{current_element_info['element_name']}"):
                logging.info(f"DEBUG: Saving element: {current_element_info['element_name']}")
                st.session_state["scratchpad"][current_element_info["element_name"]] = user_element_response
                st.success(f"'{current_element_info['element_name'].replace('_', ' ').title()}' updated!")
                logging.info("DEBUG: Element saved. Rerunning.")
                st.rerun()
        else:
            st.success(current_element_info["prompt_text"])
            st.info(current_element_info["follow_up"])

        st.markdown("---") # Re-add this line for visual separation

        # Actionable Recommendations (Temporarily hidden as per user request for consistent dialogue)
        # st.subheader("Actionable Recommendations")
        # if st.button("Generate Recommendations"):
        #     logging.info("DEBUG: Generate Recommendations button clicked.")
        #     element_for_recommendation = st.session_state["scratchpad"].get("problem", "general ideation")
        #     context_for_recommendation = st.session_state["conversation_history"][-1]["text"] if st.session_state["conversation_history"] else "no specific context"
            
        #     with st.spinner("Generating recommendations..."):
        #         logging.info("DEBUG: Calling generate_actionable_recommendations.")
        #         recommendations = generate_actionable_recommendations(element_for_recommendation, context_for_recommendation)
        #         logging.info("DEBUG: generate_actionable_recommendations completed.")
        #         for i, rec in enumerate(recommendations):
        #             st.markdown(f"**Recommendation {i+1}:** {rec}")
        
        # st.markdown("---")
    
        # Summary Report Generation and Download (Temporarily hidden as per user request for consistent dialogue)
        # st.subheader("Session Summary")
        # if st.button("Generate Final Summary Report"):
        #     logging.info("DEBUG: Generate Final Summary Report button clicked.")
        #     logging.info("DEBUG: Calling generate_final_summary_report.")
        #     final_report = generate_final_summary_report()
        #     logging.info("DEBUG: generate_final_summary_report completed.")
        #     st.text_area("Final Summary Report", value=final_report, height=300)
        #     from src.ui_components import download_summary_button
        #     download_summary_button(st.session_state["scratchpad"])
        
        # st.markdown("---")

        # Chat input for user messages
        logging.info("DEBUG: About to render st.chat_input")
        user_input = st.chat_input(placeholder="Ask me anything about digital health innovation!")
        if user_input:
            logging.info(f"DEBUG: User input received in ideation: {user_input}")
            # Check for out-of-scope input
            if is_out_of_scope(user_input):
                logging.info("DEBUG: Input identified as out of scope.")
                st.warning("Your input seems to be out of scope. Please refrain from entering personal health information, market sizing, or financial projections.")
            else:
                # Append user message to conversation history
                st.session_state["conversation_history"].append({"role": "user", "text": user_input})
                logging.info("DEBUG: User message appended to history.")

                # Generate and display assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        logging.info("DEBUG: Calling generate_assistant_response.")
                        assistant_response, search_results = generate_assistant_response(user_input)
                        logging.info("DEBUG: generate_assistant_response completed.")
                        
                        # Format citations and render response
                        citations_data = []
                        if search_results:
                            citations_data = [{"text": res.get('title', f"Result {i+1}"), "url": res.get('url', '#')} for i, res in enumerate(search_results)]
                        
                        render_response_with_citations(assistant_response, citations_data)
                logging.info("DEBUG: Rerunning after user input processing.")
                st.rerun() # Rerun to update conversation history and potentially next element
except Exception as e:
    logging.error(f"Error in main application logic: {e}")
    st.error(f"An error occurred: {e}")
    st.stop() # Stop Streamlit execution if an error occurs