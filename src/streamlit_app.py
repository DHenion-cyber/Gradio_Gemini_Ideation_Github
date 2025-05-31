import streamlit as st

from src.conversation_manager import initialize_conversation_state, run_intake_flow
from src.ui_components import apply_responsive_css, privacy_notice

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

    # Display conversation history
    for message in st.session_state["conversation_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])

    # Placeholder for chat input in ideation phase
    # This will be implemented in a later step.