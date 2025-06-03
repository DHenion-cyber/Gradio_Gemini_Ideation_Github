import pytest
import streamlit as st
from unittest.mock import MagicMock, patch

# Adjust the import path based on your project structure
from src.conversation_manager import route_conversation, initialize_conversation_state
from src.constants import MAX_PERPLEXITY_CALLS # Moved to constants.py
from src import conversation_phases # To allow mocking its functions

# Initialize session state for testing
def mock_initialize_session_state():
    """Initializes a mock session state for testing."""
    st.session_state = MagicMock()

    # Set initial attributes that will be the source of truth
    st.session_state.phase = "exploration"
    st.session_state.scratchpad = {}  # Assuming this is mostly read or replaced wholesale
    st.session_state.user_id = "test_user"
    st.session_state.perplexity_calls = 0

    # Configure .get() to read from the mock's attributes
    def _get_from_attribute(key, default=None):
        return getattr(st.session_state, key, default)
    st.session_state.get = MagicMock(side_effect=_get_from_attribute)

    # Configure item assignment to set attributes on the mock
    def _set_attribute_from_item(key, value):
        setattr(st.session_state, key, value)
    st.session_state.__setitem__ = MagicMock(side_effect=_set_attribute_from_item)
    
    # Configure .to_dict() to dynamically create a dict from current attributes
    st.session_state.to_dict = MagicMock(side_effect=lambda: {
        "phase": st.session_state.phase,
        "scratchpad": st.session_state.scratchpad,
        "user_id": st.session_state.user_id,
        "perplexity_calls": st.session_state.perplexity_calls
        # Add any other keys that save_session might expect from the dict
    })


@pytest.fixture(autouse=True)
def reset_mocks_and_state():
    """Reset Streamlit session state and mocks before each test."""
    mock_initialize_session_state()
    # If conversation_phases functions are complex, mock them here
    # For this test, we are testing the routing logic within route_conversation
    # and the specific keyword detection in handle_exploration.

@patch('src.conversation_manager.save_session') # Mock save_session to avoid file I/O
def test_exploration_to_development_on_keyword(mock_save_session):
    """
    Ensure conversation transitions from exploration to development
    when an idea keyword is detected.
    """
    mock_initialize_session_state() # Ensure fresh state
    st.session_state.phase = "exploration"
    
    user_message_with_keyword = "I want to build a new app."
    
    # Since handle_exploration is called directly by route_conversation,
    # we are effectively testing its keyword detection logic through route_conversation.
    assistant_reply, next_phase = route_conversation(user_message_with_keyword, st.session_state.scratchpad)
    
    assert next_phase == "development", "Phase should transition to development"
    assert st.session_state.phase == "development", "Session state phase should be updated to development"
    assert "Great! It sounds like you're ready to start developing this idea" in assistant_reply
    mock_save_session.assert_called_once()

@patch('src.conversation_manager.save_session')
@patch('src.conversation_manager.conversation_phases.handle_exploration')
def test_route_to_exploration(mock_handle_exploration, mock_save_session):
    """Test routing to handle_exploration."""
    mock_initialize_session_state()
    st.session_state.phase = "exploration"
    mock_handle_exploration.return_value = ("Exploration reply", "exploration")
    
    user_message = "Tell me more about exploration."
    assistant_reply, next_phase = route_conversation(user_message, st.session_state.scratchpad)
    
    mock_handle_exploration.assert_called_once_with(user_message, st.session_state["scratchpad"])
    assert assistant_reply == "Exploration reply"
    assert next_phase == "exploration"
    assert st.session_state.phase == "exploration"
    mock_save_session.assert_called_once()

@patch('src.conversation_manager.save_session')
@patch('src.conversation_manager.conversation_phases.handle_development')
def test_route_to_development(mock_handle_development, mock_save_session):
    """Test routing to handle_development."""
    mock_initialize_session_state()
    st.session_state.phase = "development"
    mock_handle_development.return_value = ("Development reply", "development")
    
    user_message = "Let's develop this feature."
    assistant_reply, next_phase = route_conversation(user_message, st.session_state.scratchpad)
    
    mock_handle_development.assert_called_once_with(user_message, st.session_state["scratchpad"])
    assert assistant_reply == "Development reply"
    assert next_phase == "development"
    assert st.session_state.phase == "development"
    mock_save_session.assert_called_once()

@patch('src.conversation_manager.save_session')
@patch('src.conversation_manager.conversation_phases.handle_refinement')
def test_route_to_refinement(mock_handle_refinement, mock_save_session):
    """Test routing to handle_refinement."""
    mock_initialize_session_state()
    st.session_state.phase = "refinement"
    mock_handle_refinement.return_value = ("Refinement reply", "refinement")
    
    user_message = "Let's refine this idea."
    assistant_reply, next_phase = route_conversation(user_message, st.session_state.scratchpad)
    
    mock_handle_refinement.assert_called_once_with(user_message, st.session_state["scratchpad"])
    assert assistant_reply == "Refinement reply"
    assert next_phase == "refinement"
    assert st.session_state.phase == "refinement"
    mock_save_session.assert_called_once()

@patch('src.conversation_manager.save_session')
@patch('src.conversation_manager.conversation_phases.handle_summary')
def test_route_to_summary(mock_handle_summary, mock_save_session):
    """Test routing to handle_summary."""
    mock_initialize_session_state()
    st.session_state.phase = "summary"
    mock_handle_summary.return_value = ("Summary reply", "summary")
    
    user_message = "Let's summarize."
    assistant_reply, next_phase = route_conversation(user_message, st.session_state.scratchpad)
    
    mock_handle_summary.assert_called_once_with(user_message, st.session_state["scratchpad"])
    assert assistant_reply == "Summary reply"
    assert next_phase == "summary"
    assert st.session_state.phase == "summary"
    mock_save_session.assert_called_once()

@patch('src.conversation_manager.save_session')
def test_route_unknown_phase_resets_to_exploration(mock_save_session):
    """Test that an unknown phase resets to exploration."""
    mock_initialize_session_state()
    st.session_state.phase = "unknown_phase_xyz" # Set an invalid phase
    
    user_message = "This should reset."
    assistant_reply, next_phase = route_conversation(user_message, st.session_state.scratchpad)
    
    assert "Debug: Unknown phase 'unknown_phase_xyz'. Resetting to exploration." in assistant_reply
    assert next_phase == "exploration"
    assert st.session_state.phase == "exploration" # Ensure session state is also updated
    mock_save_session.assert_called_once()

# Example of how to test the perplexity call limit if it were in route_conversation
# For now, this logic is in phase handlers, so tests would be in test_conversation_phases.py
# @patch('src.conversation_manager.save_session')
# @patch('src.conversation_phases.handle_exploration') # Assuming exploration might call search
# def test_perplexity_limit_in_phase_handler(mock_handle_exploration, mock_save_session):
#     mock_initialize_session_state()
#     st.session_state.phase = "exploration"
#     st.session_state.perplexity_calls = MAX_PERPLEXITY_CALLS
    
#     # Configure mock_handle_exploration to simulate hitting the limit
#     # This requires handle_exploration to actually implement the check
#     mock_handle_exploration.return_value = (
#         "I've reached the three-search limit...", 
#         "exploration"
#     )
    
#     user_message = "Search for something." # A message that would trigger search
#     assistant_reply, next_phase = route_conversation(user_message, st.session_state.scratchpad)
    
#     assert "I've reached the three-search limit" in assistant_reply
#     assert st.session_state.perplexity_calls == MAX_PERPLEXITY_CALLS # Should not increment further
#     mock_save_session.assert_called_once()