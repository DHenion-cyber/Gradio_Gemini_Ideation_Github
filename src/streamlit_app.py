import streamlit as st
import sys
import os

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.conversation_manager import initialize_conversation_state, run_intake_flow
from src.ui_components import apply_responsive_css, privacy_notice, render_response_with_citations, progress_bar
from src.llm_utils import format_citations

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize conversation state
try:
    initialize_conversation_state()
    logging.info("Conversation state initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing conversation state: {e}")
    st.error(f"An error occurred during initialization: {e}")
    st.stop() # Stop Streamlit execution if initialization fails

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
        st.subheader("Let's get started!")
        current_question = run_intake_flow()
        if current_question != "Intake complete. Let's move to ideation!":
            user_response = st.text_input(current_question, key=f"intake_q_{st.session_state['intake_index']}")
            if user_response:
                run_intake_flow(user_response)
                st.rerun() # Rerun to display the next question or transition
        else:
            st.success(current_question)
            st.rerun() # Rerun to transition to ideation stage
    elif st.session_state["stage"] == "ideation":
        st.subheader("Ideation Phase")
        st.write("You are now in the ideation phase. Let's brainstorm!")

        from conversation_manager import navigate_value_prop_elements, generate_assistant_response, generate_actionable_recommendations, is_out_of_scope, generate_final_summary_report, build_summary_from_scratchpad
except Exception as e:
    logging.error(f"Error in main application logic: {e}")
    st.error(f"An error occurred: {e}")
    st.stop() # Stop Streamlit execution if an error occurs

    # Display conversation history
    for message in st.session_state["conversation_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])

    # Value Proposition Navigation UI
    st.markdown("---")
    st.subheader("Value Proposition Elements")
    current_element_info = navigate_value_prop_elements()
    
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
            st.session_state["scratchpad"][current_element_info["element_name"]] = user_element_response
            st.success(f"'{current_element_info['element_name'].replace('_', ' ').title()}' updated!")
            st.rerun()
    else:
        st.success(current_element_info["prompt_text"])
        st.info(current_element_info["follow_up"])
        
    st.markdown("---")

    # Actionable Recommendations
    st.subheader("Actionable Recommendations")
    if st.button("Generate Recommendations"):
        # For demonstration, we'll use a placeholder element and context.
        # In a real app, this would be dynamically determined based on conversation.
        element_for_recommendation = st.session_state["scratchpad"].get("problem", "general ideation")
        context_for_recommendation = st.session_state["conversation_history"][-1]["text"] if st.session_state["conversation_history"] else "no specific context"
        
        with st.spinner("Generating recommendations..."):
            recommendations = generate_actionable_recommendations(element_for_recommendation, context_for_recommendation)
            for i, rec in enumerate(recommendations):
                st.markdown(f"**Recommendation {i+1}:** {rec}")
    
    st.markdown("---")

    # Summary Report Generation and Download
    st.subheader("Session Summary")
    if st.button("Generate Final Summary Report"):
        final_report = generate_final_summary_report()
        st.text_area("Final Summary Report", value=final_report, height=300)
        from src.ui_components import download_summary_button
        download_summary_button(st.session_state["scratchpad"])
    
    st.markdown("---")

    # Chat input for user messages
    # Chat input for user messages
    if st.session_state["stage"] == "ideation":
        user_input = st.chat_input("Type your message here...", placeholder="Ask me anything about digital health innovation!")
        if user_input:
            # Check for out-of-scope input
            if is_out_of_scope(user_input):
                st.warning("Your input seems to be out of scope. Please refrain from entering personal health information, market sizing, or financial projections.")
            else:
                # Append user message to conversation history
                st.session_state["conversation_history"].append({"role": "user", "text": user_input})

                # Generate and display assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        assistant_response, search_results = generate_assistant_response(user_input)
                        
                        # Format citations and render response
                        citations_data = []
                        if search_results:
                            citations_data = [{"text": res.get('title', f"Result {i+1}"), "url": res.get('url', '#')} for i, res in enumerate(search_results)]
                        
                        render_response_with_citations(assistant_response, citations_data)
            st.rerun() # Rerun to update conversation history and potentially next element