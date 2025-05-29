import streamlit as st
import time
import re

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
    Displays a collapsible warning about not entering personal health information.
    """
    with st.expander("Privacy Notice"):
        st.warning("⚠️ Do not enter personal health information or any other sensitive data.")

def apply_responsive_css():
    """
    Applies custom CSS for responsive design, including scroll-snap for chat histories.
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
        </style>
        """,
        unsafe_allow_html=True
    )

# Call this function in your Streamlit app's main execution block
# apply_responsive_css()