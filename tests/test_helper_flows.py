import pytest
import streamlit as st
from unittest.mock import MagicMock, patch

from src.conversation_phases import (
    handle_exploration,
    handle_development,
    handle_summary,
    handle_refinement
)
from src.utils.idea_maturity import calculate_maturity, RUBRIC
from src.constants import INITIAL_SCRATCHPAD

# Helper to set up a mock session state
@pytest.fixture(autouse=True)
def mock_st_session_state(monkeypatch):
    mock_session_state_obj = MagicMock()
    
    # Initialize attributes directly on the mock object
    mock_session_state_obj.scratchpad = INITIAL_SCRATCHPAD.copy()
    mock_session_state_obj.perplexity_calls = 0
    mock_session_state_obj.token_usage = {"session": 0, "daily": 0}
    
    # Mock the .get() method for compatibility if used by tested code
    def mock_get(key, default=None):
        if key == "scratchpad":
            return mock_session_state_obj.scratchpad
        elif key == "perplexity_calls":
            return mock_session_state_obj.perplexity_calls
        elif key == "token_usage":
            return mock_session_state_obj.token_usage
        elif hasattr(mock_session_state_obj, key):
            return getattr(mock_session_state_obj, key)
        return default
    
    mock_session_state_obj.get = MagicMock(side_effect=mock_get)

    # Patch streamlit.session_state with our configured mock object
    monkeypatch.setattr(st, 'session_state', mock_session_state_obj)
    
    yield mock_session_state_obj # Test runs here
    # Monkeypatch handles cleanup of st.session_state automatically


def get_scratchpad_with_maturity(target_maturity: int) -> dict:
    """Helper to create a scratchpad that achieves a target maturity score."""
    scratchpad = INITIAL_SCRATCHPAD.copy()
    achieved_score = 0
    
    # Fill elements one by one until target_maturity is met or exceeded
    elements_in_rubric = list(RUBRIC["elements"].keys())
    
    for i, element_key in enumerate(elements_in_rubric):
        if achieved_score >= target_maturity:
            break
        # Add a placeholder value for the element
        scratchpad[element_key] = f"Value for {element_key}"
        current_score, _ = calculate_maturity(scratchpad)
        achieved_score = current_score
        # If we are close and adding the next full element overshoots significantly,
        # try to be more precise if needed, or accept being slightly over.
        # For these tests, slightly over is fine.

    # Ensure all rubric keys exist in the scratchpad, even if empty, for consistency
    for key in RUBRIC["elements"].keys():
        if key not in scratchpad:
            scratchpad[key] = ""
            
    # print(f"Generated scratchpad for target {target_maturity}: {scratchpad}, actual score: {calculate_maturity(scratchpad)[0]}")
    return scratchpad

def test_exploration_to_development_transition():
    """Test that exploration phase transitions to development when maturity >= 20."""
    # Start with a scratchpad that is below 20 maturity
    scratchpad_low_maturity = get_scratchpad_with_maturity(10) # e.g., one element filled (score 15)
    st.session_state.scratchpad = scratchpad_low_maturity
    
    # Simulate a user message that adds enough to cross the threshold
    # Let's assume 'problem' (15) is filled. Adding 'customer_segment' (15) makes it 30.
    user_message_adds_element = "Our target users are tech enthusiasts." # Should fill 'customer_segment'
    
    # Initial state check
    initial_score, _ = calculate_maturity(st.session_state.scratchpad)
    assert initial_score < 20

    assistant_reply, next_phase = handle_exploration(user_message_adds_element, st.session_state.scratchpad)
    
    final_score, _ = calculate_maturity(st.session_state.scratchpad)
    assert final_score >= 20
    assert next_phase == "development"
    assert "move to the development phase" in assistant_reply.lower()
    assert st.session_state.scratchpad.get("customer_segment") # Check extractor worked

def test_exploration_stays_if_below_threshold():
    """Test that exploration phase stays if maturity < 20."""
    scratchpad_very_low_maturity = INITIAL_SCRATCHPAD.copy() # Score 0
    st.session_state.scratchpad = scratchpad_very_low_maturity
    
    user_message_minimal = "I have an idea." # Unlikely to fill any specific element strongly
    
    assistant_reply, next_phase = handle_exploration(user_message_minimal, st.session_state.scratchpad)
    
    final_score, _ = calculate_maturity(st.session_state.scratchpad)
    assert final_score < 20
    assert next_phase == "exploration"
    assert "exploring further" in assistant_reply.lower()

def test_development_to_summary_transition():
    """Test that development phase transitions to summary when maturity >= 60."""
    # Start with a scratchpad that is above 20 but below 60
    # e.g., 3 elements * 15 = 45
    scratchpad_mid_maturity = get_scratchpad_with_maturity(45)
    st.session_state.scratchpad = scratchpad_mid_maturity

    initial_score, _ = calculate_maturity(st.session_state.scratchpad)
    assert 20 <= initial_score < 60

    # Simulate a user message that adds enough to cross the 60 threshold
    # If we have 3 elements (45), adding one more (15) makes it 60.
    # Let's say 'problem', 'customer_segment', 'solution' are filled. Add 'differentiator'.
    user_message_adds_element = "Our key differentiator is superior AI."
    
    assistant_reply, next_phase = handle_development(user_message_adds_element, st.session_state.scratchpad)
    
    final_score, _ = calculate_maturity(st.session_state.scratchpad)
    assert final_score >= 60
    assert next_phase == "summary"
    assert "generate a summary" in assistant_reply.lower()
    assert st.session_state.scratchpad.get("differentiator")

def test_development_stays_if_below_threshold():
    """Test that development phase stays if maturity < 60."""
    scratchpad_dev_low_maturity = get_scratchpad_with_maturity(30) # e.g. 2 elements
    st.session_state.scratchpad = scratchpad_dev_low_maturity

    initial_score, _ = calculate_maturity(st.session_state.scratchpad)
    assert 20 <= initial_score < 60
    
    user_message_progress = "We are working on the prototype." # General progress, might not add a new rubric item
    
    assistant_reply, next_phase = handle_development(user_message_progress, st.session_state.scratchpad)
    
    final_score, _ = calculate_maturity(st.session_state.scratchpad)
    assert final_score < 60 # Assuming the message didn't add a new weighted element
    assert next_phase == "development"
    assert "developing" in assistant_reply.lower()


def test_summary_phase_output_and_transition():
    """Test summary phase output and transition to refinement."""
    scratchpad_ready_for_summary = get_scratchpad_with_maturity(75) # e.g. 5 elements
    scratchpad_ready_for_summary["solution"] = "Test Solution for Summary" # Ensure a key item is present
    st.session_state.scratchpad = scratchpad_ready_for_summary
    
    user_message = "Okay, show me the summary." # User message might be simple confirmation
    
    assistant_reply, next_phase = handle_summary(user_message, st.session_state.scratchpad)
    
    assert next_phase == "refinement"
    assert "summary of your idea" in assistant_reply.lower()
    assert "```json" in assistant_reply # Check for JSON block
    assert "Test Solution for Summary" in assistant_reply
    assert "refine this further" in assistant_reply.lower()

def test_refinement_loop():
    """Test refinement phase stays in refinement with normal input."""
    scratchpad_for_refinement = get_scratchpad_with_maturity(80)
    st.session_state.scratchpad = scratchpad_for_refinement
    
    user_message = "Let's tweak the customer segment."
    
    assistant_reply, next_phase = handle_refinement(user_message, st.session_state.scratchpad)
    
    assert next_phase == "refinement"
    assert "refining the idea" in assistant_reply.lower()
    assert "tweak the customer segment" in assistant_reply # Check user message is reflected
    # Check if scratchpad was updated (mock update_scratchpad or check a specific field if possible)
    # For this test, we assume update_scratchpad works; its own tests cover its details.
    # We can check that the maturity score might have changed if the message was effective.
    # For simplicity, just checking the phase and reply content is primary here.

def test_refinement_to_exploration_on_new_idea():
    """Test refinement transitions to exploration on 'new idea'."""
    scratchpad_for_refinement = get_scratchpad_with_maturity(80)
    scratchpad_for_refinement["problem"] = "Old problem"
    st.session_state.scratchpad = scratchpad_for_refinement
    st.session_state.perplexity_calls = 2 # Simulate some calls made
    
    user_message = "Actually, I have a new idea."
    
    assistant_reply, next_phase = handle_refinement(user_message, st.session_state.scratchpad)
    
    assert next_phase == "exploration"
    assert "exploring a new idea" in assistant_reply.lower()
    assert st.session_state.scratchpad == {} # Scratchpad should be reset
    assert st.session_state.perplexity_calls == 0 # Perplexity calls reset

@patch('src.conversation_phases.update_scratchpad')
def test_scratchpad_updated_in_exploration(mock_update_scratchpad):
    """Ensure update_scratchpad is called in exploration."""
    mock_update_scratchpad.return_value = {"problem": "test problem from mock"}
    st.session_state.scratchpad = INITIAL_SCRATCHPAD.copy()
    user_message = "The problem is complex."
    
    handle_exploration(user_message, st.session_state.scratchpad)
    
    mock_update_scratchpad.assert_called_once_with(user_message, INITIAL_SCRATCHPAD.copy())
    assert st.session_state.scratchpad == {"problem": "test problem from mock"}

@patch('src.conversation_phases.update_scratchpad')
def test_scratchpad_updated_in_development(mock_update_scratchpad):
    """Ensure update_scratchpad is called in development."""
    mock_update_scratchpad.return_value = {"solution": "test solution from mock"}
    # Simulate a scratchpad that would keep it in development phase
    st.session_state.scratchpad = get_scratchpad_with_maturity(30) 
    initial_scratchpad_copy = st.session_state.scratchpad.copy()
    user_message = "The solution is innovative."
    
    handle_development(user_message, st.session_state.scratchpad)
    
    mock_update_scratchpad.assert_called_once_with(user_message, initial_scratchpad_copy)
    assert st.session_state.scratchpad == {"solution": "test solution from mock"}

@patch('src.conversation_phases.update_scratchpad')
def test_scratchpad_updated_in_summary(mock_update_scratchpad):
    """Ensure update_scratchpad is called in summary."""
    mock_update_scratchpad.return_value = {"summary_confirmation": "yes"}
    st.session_state.scratchpad = get_scratchpad_with_maturity(70)
    initial_scratchpad_copy = st.session_state.scratchpad.copy()
    user_message = "Looks good."
    
    handle_summary(user_message, st.session_state.scratchpad)
    
    mock_update_scratchpad.assert_called_once_with(user_message, initial_scratchpad_copy)
    assert st.session_state.scratchpad == {"summary_confirmation": "yes"}

@patch('src.conversation_phases.update_scratchpad')
def test_scratchpad_updated_in_refinement(mock_update_scratchpad):
    """Ensure update_scratchpad is called in refinement (if not 'new idea')."""
    mock_update_scratchpad.return_value = {"refinement_detail": "more details"}
    st.session_state.scratchpad = get_scratchpad_with_maturity(80)
    initial_scratchpad_copy = st.session_state.scratchpad.copy()
    user_message = "Add more details to the plan."
    
    handle_refinement(user_message, st.session_state.scratchpad)
    
    mock_update_scratchpad.assert_called_once_with(user_message, initial_scratchpad_copy)
    assert st.session_state.scratchpad == {"refinement_detail": "more details"}

@patch('src.conversation_phases.update_scratchpad')
def test_scratchpad_not_updated_in_refinement_for_new_idea(mock_update_scratchpad):
    """Ensure update_scratchpad is NOT called in refinement if 'new idea'."""
    st.session_state.scratchpad = get_scratchpad_with_maturity(80)
    user_message = "I have a new idea."
    
    handle_refinement(user_message, st.session_state.scratchpad)
    
    mock_update_scratchpad.assert_not_called()
    assert st.session_state.scratchpad == {} # Verifies reset