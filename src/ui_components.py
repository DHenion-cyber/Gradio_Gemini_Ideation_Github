"""
Provides reusable Streamlit UI components for the chatbot application.
Only the components currently used in streamlit_app.py are retained.
"""
import streamlit as st

def render_response_with_citations(response_text, citations):
    """
    Displays the LLM response with clickable citation links.

    Args:
        response_text (str): The main response text from the LLM.
        citations (list): A list of dictionaries, each with 'text' and 'url'.
    """
    st.markdown(response_text)
    if citations:
        st.markdown("---")
        st.markdown("**Citations:**")
        for i, citation in enumerate(citations, start=1):
            st.markdown(f"[{i}] [{citation['text']}]({citation['url']})")

def privacy_notice():
    """
    Displays a small, fixed privacy notice box in the top right of the screen.
    """
    st.markdown(
        """
        <style>
        .privacy-notice-box {
            position: fixed;
            top: 10px;
            right: 10px;
            background-color: #fff3cd; /* Light yellow */
            color: #856404; /* Dark yellow text */
            border: 1px solid #ffeeba;
            border-radius: 5px;
            padding: 8px 12px;
            font-size: 0.8em;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        <div class="privacy-notice-box">
            ⚠️ Do not enter personal health information or any other sensitive data.
        </div>
        """,
        unsafe_allow_html=True
    )

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
            max-height: 70vh;
            overflow-y: auto;
            scroll-snap-type: y mandatory;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
