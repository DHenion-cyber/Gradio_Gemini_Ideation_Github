import streamlit as st
import sys
import os

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.conversation_manager import initialize_conversation_state, run_intake_flow
from src.ui_components import apply_responsive_css, privacy_notice, render_response_with_citations
from src.llm_utils import format_citations

# Initialize conversation state
initialize_conversation_state()

st.set_page_config(page_title="Chatbot UI", layout="wide")
st.title("Welcome to the Chatbot")

# Apply custom CSS for responsive design
apply_responsive_css()

# Display privacy notice
privacy_notice()

# Main application logic
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

    from conversation_manager import navigate_value_prop_elements, generate_assistant_response

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

    # Chat input for user messages
    user_input = st.chat_input("Type your message here...")
    if user_input:
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