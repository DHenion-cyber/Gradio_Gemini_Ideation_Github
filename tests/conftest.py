"""Pytest configuration file for shared fixtures and hooks."""
import pytest
import streamlit as st
from unittest.mock import MagicMock

@pytest.fixture
def mock_streamlit_session_state(monkeypatch):
    """
    Mocks streamlit.session_state and related modules' session_state
    with a MagicMock object.
    """
    mock_session_state = MagicMock()
    # Configure the mock to behave like a dictionary for item access
    # and also allow attribute access if that's how it's used.
    mock_session_state_data = {}

    def get_item(key):
        return mock_session_state_data.get(key)

    def set_item(key, value):
        mock_session_state_data[key] = value

    def get_attr(key, default=None): # For .get() method
        return mock_session_state_data.get(key, default)

    def setdefault_item(key, default_value):
        if key not in mock_session_state_data:
            mock_session_state_data[key] = default_value
        return mock_session_state_data[key]

    def contains_item(key):
        return key in mock_session_state_data

    mock_session_state.__getitem__.side_effect = get_item
    mock_session_state.__setitem__.side_effect = set_item
    mock_session_state.get.side_effect = get_attr # Handles st.session_state.get('key', default_value)
    mock_session_state.setdefault.side_effect = setdefault_item
    mock_session_state.__contains__.side_effect = contains_item

    # Add to_dict mock to return the underlying serializable dictionary
    def to_dict_method():
        return mock_session_state_data
    mock_session_state.to_dict = MagicMock(side_effect=to_dict_method)

    # Patch st.session_state where it's directly used
    monkeypatch.setattr(st, "session_state", mock_session_state)

    # Patch st.session_state in modules where it might be imported and used
    # This ensures that 'from streamlit import session_state' or 'st.session_state'
    # in those modules get the mock.
    try:
        # Assuming 'src.search_utils' and 'src.conversation_phases' are modules
        # that might use 'st.session_state'. Add others if necessary.
        import src.search_utils
        monkeypatch.setattr(src.search_utils, "st", st) # Ensure 'st' itself is patched if they use 'search_utils.st.session_state'
        monkeypatch.setattr(src.search_utils.st, "session_state", mock_session_state)
    except ImportError:
        pass # Module might not exist or is not relevant for all tests

    try:
        import src.conversation_manager
        monkeypatch.setattr(src.conversation_manager, "st", st)
        monkeypatch.setattr(src.conversation_manager.st, "session_state", mock_session_state)
    except ImportError:
        pass

    try:
        import src.conversation_phases
        monkeypatch.setattr(src.conversation_phases, "st", st)
        monkeypatch.setattr(src.conversation_phases.st, "session_state", mock_session_state)
    except ImportError:
        pass
    
    try:
        import src.llm_utils
        monkeypatch.setattr(src.llm_utils, "st", st)
        monkeypatch.setattr(src.llm_utils.st, "session_state", mock_session_state)
    except ImportError:
        pass

    # Yield the mock_session_state_data so tests can manipulate the underlying store directly if needed
    # or just use st.session_state as they normally would.
    yield mock_session_state_data # Tests can use this to set initial state values

    # Teardown: clear the mock data after test if necessary, though monkeypatch handles unpatching.
    mock_session_state_data.clear()
import datetime
from src import conversation_manager as cm

@pytest.fixture(autouse=True)
def reset_session_state(mock_streamlit_session_state): # Add mock_streamlit_session_state dependency
    """
    Autouse fixture to reset and initialize Streamlit session state for each test.
    Relies on mock_streamlit_session_state to ensure st.session_state is mocked.
    """
    # mock_streamlit_session_state (the underlying dict) is cleared by its own teardown.
    # st.session_state is the MagicMock. We can clear it if necessary,
    # but initialize_conversation_state will overwrite it.
    # Using st.session_state.clear() might be problematic if the MagicMock doesn't support it well.
    # Instead, rely on initialize_conversation_state to set fresh values.
    # The mock_streamlit_session_state fixture yields the backing dict, which is cleared.
    # So, st.session_state (the MagicMock) will effectively be "cleared" as its backing store is empty.

    # Mock st.query_params before it's accessed at the module level in conversation_manager
    # st should be the one patched by mock_streamlit_session_state
    if not hasattr(st, 'query_params'):
        st.query_params = {} # This sets it on the mocked 'st' module object.
    
    # Re-initialize with defaults. This will populate the mocked st.session_state
    cm.initialize_conversation_state() 
    
    # Ensure user_id is explicitly set for tests that might rely on it before full init
    # This also uses the mocked st.session_state
    st.session_state["user_id"] = cm.generate_uuid() 
    
    yield
    
    # The mock_streamlit_session_state fixture already handles clearing its backing data,
    # so st.session_state will be effectively empty for the next test.
    # No explicit st.session_state.clear() needed here if mock_streamlit_session_state handles teardown.