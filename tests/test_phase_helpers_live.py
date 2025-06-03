from src import constants
import src.conversation_phases as cp
import src.search_utils as su
import pytest
from unittest.mock import patch
import os

# Fixture to mock st.session_state for each test
@pytest.fixture(autouse=True)
def mock_st_session_state():
    with patch('src.conversation_phases.st.session_state', new={
        "scratchpad": constants.EMPTY_SCRATCHPAD.copy(),
        "perplexity_calls": 0,
        "token_usage": {"daily": 0, "session": 0}
    }) as mock_state:
        yield mock_state

# Helper to create a scratchpad with a specific maturity score
def create_scratchpad_with_maturity(score_percentage: float):
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    num_filled_keys = int(len(constants.CANONICAL_KEYS) * (score_percentage / 100.0))
    for i in range(num_filled_keys):
        scratchpad[constants.CANONICAL_KEYS[i]] = f"value_for_{constants.CANONICAL_KEYS[i]}"
    return scratchpad

def test_handle_exploration_live_keyword_transition(mock_st_session_state):
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    user_msg = "I want to build an AI RPM tool"
    reply, phase = cp.handle_exploration(user_msg, scratchpad)
    assert "Great! It sounds like you're ready to start developing this idea" in reply
    assert phase == "development"
    # The scratchpad is updated by the extractor, so we need to assert against the updated state
    # We don't assert the exact scratchpad content here as it's handled by the extractor's internal logic.
    # The primary goal is to verify phase transition and assistant reply.

def test_handle_exploration_live_maturity_transition(mock_st_session_state):
    scratchpad = create_scratchpad_with_maturity(25) # Maturity >= 20
    scratchpad[constants.CANONICAL_KEYS[2]] = "AI RPM tool" # Set solution for reply
    user_msg = "Let's think about the problem."
    reply, phase = cp.handle_exploration(user_msg, scratchpad)
    assert "Great progress! Your idea for 'AI RPM tool' has reached a maturity of" in reply
    assert "Let's move to the development phase." in reply
    assert phase == "development"
    # The scratchpad is updated by the extractor, so we don't assert its exact content here.

def test_handle_exploration_live_stay_exploration(mock_st_session_state):
    scratchpad = create_scratchpad_with_maturity(10) # Maturity < 20
    user_msg = "Tell me more about the problem space."
    reply, phase = cp.handle_exploration(user_msg, scratchpad)
    assert "Exploring further based on:" in reply
    assert "Current idea maturity:" in reply
    assert "Let's focus on strengthening:" in reply
    assert phase == "exploration"
    # The scratchpad is updated by the extractor, so we don't assert its exact content here.

def test_handle_development_live_maturity_transition_to_summary(mock_st_session_state):
    scratchpad = create_scratchpad_with_maturity(65) # Maturity >= 60
    scratchpad[constants.CANONICAL_KEYS[2]] = "AI RPM tool" # Set solution for reply
    user_msg = "We've defined most features."
    reply, phase = cp.handle_development(user_msg, scratchpad)
    assert "Excellent! The idea 'AI RPM tool' has a strong maturity of" in reply
    assert "Let's generate a summary." in reply
    assert phase == "summary"
    # The scratchpad is updated by the extractor, so we don't assert its exact content here.

def test_handle_development_live_stay_development(mock_st_session_state):
    scratchpad = create_scratchpad_with_maturity(40) # Maturity < 60
    scratchpad[constants.CANONICAL_KEYS[2]] = "AI RPM tool" # Set solution for reply
    user_msg = "What about the user experience?"
    reply, phase = cp.handle_development(user_msg, scratchpad)
    assert "Developing 'AI RPM tool'. Current maturity:" in reply
    assert "We can still improve:" in reply
    assert phase == "development"
    # The scratchpad is updated by the extractor, so we don't assert its exact content here.

def test_handle_summary_live(mock_st_session_state):
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    # Pre-fill scratchpad with some keys to simulate a complete conversation
    scratchpad["problem"] = "Lack of affordable unicorn rides"
    scratchpad["solution"] = "App-based unicorn sharing"
    scratchpad["revenue_model"] = "Subscription"
    
    user_msg = "Summarize our progress."
    reply, phase = cp.handle_summary(user_msg, scratchpad)
    assert "Here's a summary of your idea:" in reply
    assert '"problem": "Lack of affordable unicorn rides"' in reply
    assert '"solution": "App-based unicorn sharing"' in reply
    assert '"revenue_model": "Subscription"' in reply
    assert "We can now refine this further." in reply
    assert phase == "refinement"
    # The scratchpad is updated by the extractor, so we don't assert its exact content here.

def test_handle_refinement_live_new_idea(mock_st_session_state):
    mock_st_session_state["scratchpad"] = {"problem": "old idea", "solution": "old solution"} # Simulate existing scratchpad
    mock_st_session_state["perplexity_calls"] = 2 # Simulate existing calls
    user_msg = "I want to start a new idea"
    reply, phase = cp.handle_refinement(user_msg, mock_st_session_state["scratchpad"])
    assert "Okay, let's start exploring a new idea! What's on your mind?" in reply
    assert phase == "exploration"
    assert mock_st_session_state["scratchpad"] == constants.EMPTY_SCRATCHPAD
    assert mock_st_session_state["perplexity_calls"] == 0

@patch.dict(os.environ, {"PERPLEXITY_API_KEY": ""})
def test_handle_refinement_live_research_stub_response(mock_st_session_state):
    mock_st_session_state["perplexity_calls"] = 0 # Reset calls for this test
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    user_msg = "research existing AI RPM tools"
    with patch('src.search_utils.search_perplexity', return_value="STUB_RESPONSE") as mock_search_perplexity:
        reply, phase = cp.handle_refinement(user_msg, scratchpad)
        mock_search_perplexity.assert_called_once_with(user_msg)
    assert "Live web search isn’t configured." in reply
    assert "You can paste external findings here and I’ll integrate them." in reply
    assert phase == "refinement"
    assert mock_st_session_state["perplexity_calls"] == 0 # Should not increment if API key is missing

def test_handle_refinement_live_research_cap_reached(mock_st_session_state):
    mock_st_session_state["perplexity_calls"] = constants.MAX_PERPLEXITY_CALLS # Simulate cap reached
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    user_msg = "research more about AI RPM tools"
    with patch('src.search_utils.search_perplexity', return_value="RESEARCH_CAP_REACHED") as mock_search_perplexity:
        reply, phase = cp.handle_refinement(user_msg, scratchpad)
        mock_search_perplexity.assert_called_once_with(user_msg) # Ensure it was called
    assert "I’ve reached the three‑search limit." in reply
    assert "Feel free to explore externally and bring info back!" in reply
    assert phase == "refinement"
    assert mock_st_session_state["perplexity_calls"] == constants.MAX_PERPLEXITY_CALLS # Should not increment further

@patch.dict(os.environ, {"PERPLEXITY_API_KEY": "dummy_key"})
def test_handle_refinement_live_research_success(mock_st_session_state):
    mock_st_session_state["perplexity_calls"] = 0 # Reset calls for this test
    mock_search_results = [
        {"title": "Tool A", "url": "http://tool-a.com", "snippet": "Snippet A"},
        {"title": "Tool B", "url": "http://tool-b.com", "snippet": "Snippet B"}
    ]
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    user_msg = "research AI RPM tools"
    with patch('src.search_utils.search_perplexity', side_effect=lambda q: (mock_st_session_state.update({"perplexity_calls": mock_st_session_state["perplexity_calls"] + 1}), mock_search_results)[1]) as mock_search_perplexity:
        reply, phase = cp.handle_refinement(user_msg, scratchpad)
        mock_search_perplexity.assert_called_once_with(user_msg)
    assert "Result 1: Tool A" in reply
    assert "URL: http://tool-a.com" in reply
    assert "Snippet: Snippet A" in reply
    assert "Result 2: Tool B" in reply
    assert "URL: http://tool-b.com" in reply
    assert "Snippet: Snippet B" in reply
    assert phase == "refinement"
    assert mock_st_session_state["perplexity_calls"] == 1 # Should increment after successful search

def test_handle_refinement_live_regular_message(mock_st_session_state):
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    scratchpad["problem"] = "Lack of good coffee"
    user_msg = "Let's refine the problem statement."
    reply, phase = cp.handle_refinement(user_msg, scratchpad)
    assert "Refining the idea. You mentioned:" in reply
    assert "Let's refine the problem statement." in reply
    assert "Current maturity:" in reply
    assert "We could still focus on:" in reply
    assert phase == "refinement"
    # The scratchpad is updated by the extractor, so we don't assert its exact content here.

# handle_research is an alias for handle_refinement, so its tests are covered by refinement tests.
# We can add a simple test to confirm the alias works as expected.
def test_handle_research_live_alias(mock_st_session_state):
    mock_st_session_state["perplexity_calls"] = 0
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    user_msg = "research new coffee beans"
    # This will hit the "research" branch in handle_refinement
    mock_search_results = [{"title": "Coffee Research", "url": "http://coffee.com", "snippet": "Coffee snippet"}]
    with patch('src.search_utils.search_perplexity', side_effect=lambda q: (mock_st_session_state.update({"perplexity_calls": mock_st_session_state["perplexity_calls"] + 1}), mock_search_results)[1]) as mock_search_perplexity:
        reply, phase = cp.handle_research(user_msg, scratchpad)
        mock_search_perplexity.assert_called_once_with(user_msg)
    assert "Result 1: Coffee Research" in reply
    assert phase == "refinement"
    assert mock_st_session_state["perplexity_calls"] == 1