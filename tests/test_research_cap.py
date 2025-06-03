import streamlit as st
import os # Added for os.environ
import asyncio # Added for asyncio.Future mock
from unittest.mock import MagicMock # Added for MagicMock
from src import constants
from src.search_utils import search_perplexity

def test_cap_enforced(monkeypatch):
    # Explicitly mock st.session_state for isolation
    # Use a MagicMock for st.session_state to handle both attribute and dictionary access
    mock_session_state = MagicMock()
    # Ensure the mock behaves like a dictionary for item access
    mock_session_state.__getitem__.side_effect = lambda key: mock_session_state._mock_data.get(key)
    mock_session_state.__setitem__.side_effect = lambda key, value: mock_session_state._mock_data.__setitem__(key, value)
    mock_session_state.get.side_effect = lambda key, default=None: mock_session_state._mock_data.get(key, default) # Explicitly mock .get()
    mock_session_state._mock_data = {} # Internal dictionary to store state

    # Patch st.session_state within the search_utils module directly
    monkeypatch.setattr("src.search_utils.st.session_state", mock_session_state)
    # Also patch the main streamlit.session_state for other modules that might use it
    monkeypatch.setattr(st, "session_state", mock_session_state)
    
    # Set the session state to reach the cap
    mock_session_state["perplexity_calls"] = constants.MAX_PERPLEXITY_CALLS

    # Call the function and assert it returns the cap reached message
    assert search_perplexity("anything") == "RESEARCH_CAP_REACHED"

def test_cap_increment(monkeypatch):
    # Explicitly mock st.session_state for isolation
    # Use a MagicMock for st.session_state to handle both attribute and dictionary access
    mock_session_state = MagicMock()
    mock_session_state.__getitem__.side_effect = lambda key: mock_session_state._mock_data.get(key)
    mock_session_state.__setitem__.side_effect = lambda key, value: mock_session_state._mock_data.__setitem__(key, value)
    mock_session_state.get.side_effect = lambda key, default=None: mock_session_state._mock_data.get(key, default) # Explicitly mock .get()
    mock_session_state._mock_data = {} # Internal dictionary to store state

    # Patch st.session_state within the search_utils module directly
    monkeypatch.setattr("src.search_utils.st.session_state", mock_session_state)
    # Also patch the main streamlit.session_state for other modules that might use it
    monkeypatch.setattr(st, "session_state", mock_session_state)

    # Ensure initial state is 0
    mock_session_state["perplexity_calls"] = 0

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

    # Assert the call count incremented
    assert mock_session_state["perplexity_calls"] == 1

    # Call again
    search_perplexity("another test query")
    assert mock_session_state["perplexity_calls"] == 2

def test_cap_reset_on_new_idea(monkeypatch):
    # Explicitly mock st.session_state for isolation
    # Use a MagicMock for st.session_state to handle both attribute and dictionary access
    mock_session_state = MagicMock()
    mock_session_state.__getitem__.side_effect = lambda key: mock_session_state._mock_data.get(key)
    mock_session_state.__setitem__.side_effect = lambda key, value: mock_session_state._mock_data.__setitem__(key, value)
    mock_session_state.get.side_effect = lambda key, default=None: mock_session_state._mock_data.get(key, default) # Explicitly mock .get()
    mock_session_state._mock_data = {} # Internal dictionary to store state

    # Patch st.session_state within the conversation_phases module directly
    monkeypatch.setattr("src.conversation_phases.st.session_state", mock_session_state)
    # Also patch the main streamlit.session_state for other modules that might use it
    monkeypatch.setattr(st, "session_state", mock_session_state)

    from src.conversation_phases import handle_refinement
    
    mock_session_state["perplexity_calls"] = 2
    mock_session_state["scratchpad"] = {"problem": "old idea"} # Simulate existing scratchpad
    # Ensure 'scratchpad' key exists for handle_refinement if it tries to access st.session_state.scratchpad directly
    # handle_refinement itself uses EMPTY_SCRATCHPAD.copy() so this might not be strictly needed if st.session_state is the mock_session_state
    # but it's safer to ensure the structure is what the tested code might expect.
    if "scratchpad" not in mock_session_state: # Redundant given the line above, but for clarity
        mock_session_state["scratchpad"] = {}


    # Mock search_perplexity to avoid actual calls during refinement
    monkeypatch.setattr("src.search_utils.search_perplexity", lambda x: "Mock search result")

    # Trigger new idea
    reply, phase = handle_refinement("I want a new idea", {})
    
    assert mock_session_state["perplexity_calls"] == 0
    assert phase == "exploration"
    assert "new idea" in reply

def test_search_perplexity_stub_if_no_key(monkeypatch):
    # Explicitly mock st.session_state for isolation
    # Use a MagicMock for st.session_state to handle both attribute and dictionary access
    mock_session_state = MagicMock()
    mock_session_state.__getitem__.side_effect = lambda key: mock_session_state._mock_data.get(key)
    mock_session_state.__setitem__.side_effect = lambda key, value: mock_session_state._mock_data.__setitem__(key, value)
    mock_session_state.get.side_effect = lambda key, default=None: mock_session_state._mock_data.get(key, default) # Explicitly mock .get()
    mock_session_state._mock_data = {} # Internal dictionary to store state

    # Patch st.session_state within the search_utils module directly
    monkeypatch.setattr("src.search_utils.st.session_state", mock_session_state)
    # Also patch the main streamlit.session_state for other modules that might use it
    monkeypatch.setattr(st, "session_state", mock_session_state)

    # Ensure API key is not set
    if "PERPLEXITY_API_KEY" in os.environ:
        monkeypatch.delitem(os.environ, "PERPLEXITY_API_KEY") # Use delitem for os.environ
    
    # Ensure perplexity_calls is initialized
    mock_session_state["perplexity_calls"] = 0

    # Add a mock for the search function even if it shouldn't be called, to prevent unintended real calls
    monkeypatch.setattr(
        "src.search_utils._mockable_async_perplexity_search",
        lambda x: asyncio.create_task(asyncio.sleep(0, result=[{"title": "Mock", "url": "http://mock.com", "snippet": "Mock snippet"}]))
    )

    # Call the function
    result = search_perplexity("test query")

    # Assert it returns the stub message and does not increment calls
    assert result == "STUB_RESPONSE"
    assert mock_session_state["perplexity_calls"] == 0 # Should not increment if key is missing and it's a stub