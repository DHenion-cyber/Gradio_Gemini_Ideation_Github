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
st.title("Welcome to the Chatbot")

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
try:
    if st.session_state["stage"] == "intake":
        logging.info("Entering intake stage.")
        st.subheader("Let's get started!")
        
        intake_questions = get_intake_questions()
        current_intake_index = st.session_state["intake_index"]

        if current_intake_index < len(intake_questions):
            current_question = intake_questions[current_intake_index]
            
            with st.form(key=f"intake_form_{current_intake_index}"):
                st.markdown(current_question) # Display the question verbatim
                user_response_input = st.text_input("Your response:", key=f"intake_q_{current_intake_index}_input") # Use a generic label for the input box
                submitted = st.form_submit_button(label="Submit")

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
    elif st.session_state["stage"] == "ideation":
        logging.info("Entering ideation stage.")
        st.subheader("Ideation Phase")
        st.write("You are now in the ideation phase. Let's brainstorm!")

        from src.conversation_manager import navigate_value_prop_elements, generate_assistant_response, generate_actionable_recommendations, is_out_of_scope, generate_final_summary_report, build_summary_from_scratchpad
except Exception as e:
    logging.error(f"Error in main application logic: {e}")
    st.error(f"An error occurred: {e}")
    st.stop() # Stop Streamlit execution if an error occurs

# The rest of the application logic (ideation phase, chat, etc.) should be outside the try-except block
# and at the same indentation level as the initial 'if st.session_state["stage"] == "intake":' block.

if st.session_state["stage"] == "ideation":
    logging.info("Entering ideation stage.")
    st.subheader("Ideation Phase")
    st.write("You are now in the ideation phase. Let's brainstorm!")

    from src.conversation_manager import navigate_value_prop_elements, generate_assistant_response, generate_actionable_recommendations, is_out_of_scope, generate_final_summary_report, build_summary_from_scratchpad

    # Display conversation history
    for message in st.session_state["conversation_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])

    # Value Proposition Navigation UI
    st.markdown("---")
    st.subheader("Value Proposition Elements")
    logging.info("Calling navigate_value_prop_elements.")
    current_element_info = navigate_value_prop_elements()
    logging.info(f"navigate_value_prop_elements returned: {current_element_info['element_name']}")
    
    if current_element_info["element_name"]:
        st.info(current_element_info["prompt_text"])
        st.caption(current_element_info["follow_up"])
        
        element_input_key = f"element_input_{current_element_info['element_name']}"
        user_element_response = st.text_area(
            f"Refine '{current_element_info['element_name'].replace('_', ' ').title()}'",
            value=st.session_state["scratchpad"].get(current_element_info["element_name"], ""),
            key=element_input_key
        )
        
        if st.button(f"Save {current_element_info['element_name'].replace('_', ' ').title()}", key=f"save_element_{current_element_info['element_name']}"):
            logging.info(f"Saving element: {current_element_info['element_name']}")
            st.session_state["scratchpad"][current_element_info["element_name"]] = user_element_response
            st.success(f"'{current_element_info['element_name'].replace('_', ' ').title()}' updated!")
            logging.info("Element saved. Rerunning.")
            st.rerun()
    else:
        st.success(current_element_info["prompt_text"])
        st.info(current_element_info["follow_up"])
        
    st.markdown("---")

    # Actionable Recommendations
    st.subheader("Actionable Recommendations")
    if st.button("Generate Recommendations"):
        logging.info("Generate Recommendations button clicked.")
        # For demonstration, we'll use a placeholder element and context.
        # In a real app, this would be dynamically determined based on conversation.
        element_for_recommendation = st.session_state["scratchpad"].get("problem", "general ideation")
        context_for_recommendation = st.session_state["conversation_history"][-1]["text"] if st.session_state["conversation_history"] else "no specific context"
        
        with st.spinner("Generating recommendations..."):
            logging.info("Calling generate_actionable_recommendations.")
            recommendations = generate_actionable_recommendations(element_for_recommendation, context_for_recommendation)
            logging.info("generate_actionable_recommendations completed.")
            for i, rec in enumerate(recommendations):
                st.markdown(f"**Recommendation {i+1}:** {rec}")
    
    st.markdown("---")

    # Summary Report Generation and Download
    st.subheader("Session Summary")
    if st.button("Generate Final Summary Report"):
        logging.info("Generate Final Summary Report button clicked.")
        logging.info("Calling generate_final_summary_report.")
        final_report = generate_final_summary_report()
        logging.info("generate_final_summary_report completed.")
        st.text_area("Final Summary Report", value=final_report, height=300)
        from src.ui_components import download_summary_button
        download_summary_button(st.session_state["scratchpad"])
    
    st.markdown("---")

    # Chat input for user messages
    user_input = st.chat_input("Type your message here...", placeholder="Ask me anything about digital health innovation!")
    if user_input:
        logging.info(f"User input received in ideation: {user_input}")
        # Check for out-of-scope input
        if is_out_of_scope(user_input):
            logging.info("Input identified as out of scope.")
            st.warning("Your input seems to be out of scope. Please refrain from entering personal health information, market sizing, or financial projections.")
        else:
            # Append user message to conversation history
            st.session_state["conversation_history"].append({"role": "user", "text": user_input})
            logging.info("User message appended to history.")

            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    logging.info("Calling generate_assistant_response.")
                    assistant_response, search_results = generate_assistant_response(user_input)
                    logging.info("generate_assistant_response completed.")
                    
                    # Format citations and render response
                    citations_data = []
                    if search_results:
                        citations_data = [{"text": res.get('title', f"Result {i+1}"), "url": res.get('url', '#')} for i, res in enumerate(search_results)]
                    
                    render_response_with_citations(assistant_response, citations_data)
            logging.info("Rerunning after user input processing.")
            st.rerun() # Rerun to update conversation history and potentially next element