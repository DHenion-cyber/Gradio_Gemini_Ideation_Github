"""Provides reusable Streamlit UI components for the chatbot application."""
import streamlit as st
import time

def progress_bar(turn_count):
    """
    Visualizes progress toward a 40-minute session cap using a progress bar.

    Args:
        turn_count (int): The current turn count in the conversation.
    """
    max_turns = 40  # Assuming 1 turn = 1 minute for simplicity
    progress = min(turn_count / max_turns, 1.0)
    st.progress(progress, text=f"Session Progress: {turn_count} / {max_turns} minutes")

def show_spinner(status_msg):
    """
    Wraps st.spinner to display a dynamic status message, especially for async operations.

    Args:
        status_msg (str): The message to display in the spinner.
    """
    with st.spinner(status_msg):
        time.sleep(0.1) # Small delay to ensure spinner shows

def render_response_with_citations(response_text, citations):
    """
    Displays the LLM response with clickable citation links.

    Args:
        response_text (str): The main response text from the LLM.
        citations (list): A list of dictionaries, where each dictionary contains
                          'text' and 'url' for the citation.
    """
    st.markdown(response_text)
    if citations:
        st.markdown("---")
        st.markdown("**Citations:**")
        for i, citation in enumerate(citations):
            st.markdown(f"[{i+1}] [{citation['text']}]({citation['url']})")

def download_summary_button(scratchpad):
    """
    Builds and provides a download button for a .txt report of the conversation summary.

    Args:
        scratchpad (dict): A dictionary containing conversation data, including headings
                           and their content in the correct order.
    """
    summary_content = ""
    for heading, content in scratchpad.items():
        summary_content += f"## {heading}\n{content}\n\n"

    st.download_button(
        label="Download Summary Report",
        data=summary_content,
        file_name="conversation_summary.txt",
        mime="text/plain"
    )

def privacy_notice():
    """
    Displays a small, fixed privacy notice box in the top right of the screen.
    """
    st.markdown(
        """
        <div class="privacy-notice-box">
            ⚠️ Do not enter personal health information or any other sensitive data.
        </div>
        """,
        unsafe_allow_html=True
    )

def apply_responsive_css():
    """
    Applies custom CSS for responsive design, including scroll-snap for chat histories
    and styling for the privacy notice.
    """
    st.markdown(
        """
        <style>
        .stChatMessage {
            scroll-snap-align: start;
        }
        .stChatFloatingInputContainer {
            max-height: 70vh; /* Adjust as needed */
            overflow-y: auto;
            scroll-snap-type: y mandatory;
        }
        .privacy-notice-box {
            position: fixed;
            top: 10px;
            right: 10px;
            background-color: #fff3cd; /* Light yellow for warning */
            color: #856404; /* Dark yellow text */
            border: 1px solid #ffeeba;
            border-radius: 5px;
            padding: 10px;
            font-size: 0.8em;
            z-index: 1000; /* Ensure it's on top */
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Call this function in your Streamlit app's main execution block
# apply_responsive_css()

# Commenting out the old render_feedback_box as it's replaced by general feedback mechanisms
# def render_feedback_box(message_key_prefix: str):
#     """
#     Renders a text input and a button to collect feedback for a specific message.
#
#     Args:
#         message_key_prefix (str): A unique prefix for the streamlit widget keys
#                                   to avoid collisions, e.g., "feedback_for_msg_1".
#     """
#     feedback_text = st.text_area(
#         "Share your feedback on this response:",
#         key=f"{message_key_prefix}_text_area",
#         height=100
#     )
#     submit_feedback = st.button(
#         "Submit Feedback",
#         key=f"{message_key_prefix}_button"
#     )
#     if submit_feedback and feedback_text:
#         return feedback_text
#     elif submit_feedback and not feedback_text:
#         st.caption("Please enter some feedback before submitting.")
#     return None

def render_general_feedback_trigger():
    """
    Renders an expander that allows users to submit general feedback at any time.
    Returns the feedback text if submitted, otherwise None.
    """
    with st.expander("💬 Share General Feedback"):
        feedback_text = st.text_area(
            "Your thoughts on the session or chatbot:",
            key="general_feedback_text_area",
            height=150
        )
        submit_general_feedback = st.button(
            "Submit General Feedback",
            key="general_feedback_button"
        )
        if submit_general_feedback and feedback_text:
            st.caption("Thank you for your general feedback!")
            return feedback_text
        elif submit_general_feedback and not feedback_text:
            st.caption("Please enter some feedback before submitting.")
    return None

def render_final_session_feedback_prompt():
    """
    Renders a prompt for final session feedback.
    Returns the feedback text if submitted, otherwise None.
    """
    st.markdown("---")
    st.markdown("### Your feedback matters to me!")
    st.markdown("Before you go, would you like to share any overall thoughts on this session?")
    
    feedback_text = st.text_area(
        "Overall session feedback:",
        key="final_session_feedback_text_area",
        height=150
    )
    submit_final_feedback = st.button(
        "Submit Final Feedback",
        key="final_session_feedback_button"
    )

    if submit_final_feedback and feedback_text:
        st.success("Thank you! Your final feedback has been recorded.")
        return feedback_text
    elif submit_final_feedback and not feedback_text:
        st.warning("Please enter some feedback or close this section if you're done.")
    return None