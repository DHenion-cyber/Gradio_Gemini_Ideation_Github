import streamlit as st
import os # Added for os.environ
import asyncio # Added for asyncio.Future mock
# Removed: from unittest.mock import MagicMock
from src import constants
from src.search_utils import search_perplexity

# mock_streamlit_session_state fixture is auto-used if defined in conftest.py
# and test functions accept it as an argument.

def test_cap_enforced(mock_streamlit_session_state): # monkeypatch removed as not directly used by test
    # mock_streamlit_session_state is the backing dict for the mocked st.session_state
    # The fixture mock_streamlit_session_state already patches st.session_state
    
    # Set the session state to reach the cap using the backing dict
    mock_streamlit_session_state["perplexity_calls"] = constants.MAX_PERPLEXITY_CALLS

    # Call the function and assert it returns the cap reached message
    # search_perplexity will use the mocked st.session_state
    assert search_perplexity("anything") == "RESEARCH_CAP_REACHED"

def test_cap_increment(mock_streamlit_session_state, monkeypatch):
    # mock_streamlit_session_state is the backing dict for the mocked st.session_state
    # The fixture mock_streamlit_session_state already patches st.session_state

    # Ensure initial state is 0 using the backing dict
    mock_streamlit_session_state["perplexity_calls"] = 0

    # Mock the actual search to avoid network calls
    monkeypatch.setattr("src.search_utils.os.environ", {"PERPLEXITY_API_KEY": "mock_key"})
    # Mock _mockable_async_perplexity_search directly to avoid asyncio issues in test
    # The mock needs to be an async function or return an awaitable
    monkeypatch.setattr(
        "src.search_utils._mockable_async_perplexity_search",
        lambda x: asyncio.create_task(asyncio.sleep(0, result=[{"title": "Mock", "url": "http://mock.com", "snippet": "Mock snippet"}]))
    )

    # Call the function
    search_perplexity("test query")

    # Assert the call count incremented using the mocked st.session_state
    assert st.session_state["perplexity_calls"] == 1

    # Call again
    search_perplexity("another test query")
    assert st.session_state["perplexity_calls"] == 2

def test_cap_reset_on_new_idea(mock_streamlit_session_state, monkeypatch):
    # mock_streamlit_session_state is the backing dict for the mocked st.session_state
    # The fixture mock_streamlit_session_state already patches st.session_state
    # including for src.conversation_phases.st.session_state

    from src.conversation_phases import handle_refinement
    
    # Initialize state using the backing dict
    mock_streamlit_session_state["perplexity_calls"] = 2
    mock_streamlit_session_state["scratchpad"] = {"problem": "old idea"} # Simulate existing scratchpad
    # The following 'if' block for scratchpad is no longer needed as the fixture handles st.session_state.scratchpad


    # Mock search_perplexity to avoid actual calls during refinement
    monkeypatch.setattr("src.search_utils.search_perplexity", lambda x: "Mock search result")

    # Trigger new idea
    # handle_refinement will use the mocked st.session_state
    reply, phase = handle_refinement("I want a new idea", {}) # Pass empty dict for scratchpad if that's the original intent for this call
    
    assert st.session_state["perplexity_calls"] == 0
    assert phase == "exploration"
    assert "new idea" in reply

def test_search_perplexity_stub_if_no_key(mock_streamlit_session_state, monkeypatch):
    # mock_streamlit_session_state is the backing dict for the mocked st.session_state
    # The fixture mock_streamlit_session_state already patches st.session_state

    # Ensure API key is not set
    if "PERPLEXITY_API_KEY" in os.environ:
        monkeypatch.delitem(os.environ, "PERPLEXITY_API_KEY") # Use delitem for os.environ
    
    # Ensure perplexity_calls is initialized using the backing dict
    mock_streamlit_session_state["perplexity_calls"] = 0

    # Add a mock for the search function even if it shouldn't be called, to prevent unintended real calls
    monkeypatch.setattr(
        "src.search_utils._mockable_async_perplexity_search",
        lambda x: asyncio.create_task(asyncio.sleep(0, result=[{"title": "Mock", "url": "http://mock.com", "snippet": "Mock snippet"}]))
    )

    # Call the function
    # search_perplexity will use the mocked st.session_state
    result = search_perplexity("test query")

    # Assert it returns the stub message and does not increment calls
    assert result == "STUB_RESPONSE"
    assert st.session_state["perplexity_calls"] == 0 # Should not increment if key is missing and it's a stub