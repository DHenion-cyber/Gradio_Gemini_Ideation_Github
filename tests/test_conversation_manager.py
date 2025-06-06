import pytest
import datetime
from src import conversation_manager as cm
from src.constants import EMPTY_SCRATCHPAD # Import for tests
import streamlit as st
from unittest.mock import patch # Added for save_session mocking

@pytest.fixture(autouse=True)
def reset_session_state():
    st.session_state.clear()
    # Mock st.query_params before it's accessed at the module level in conversation_manager
    if not hasattr(st, 'query_params'):
        st.query_params = {}
    cm.initialize_conversation_state() # Re-initialize with defaults
    # Ensure user_id is explicitly set for tests that might rely on it before full init
    st.session_state["user_id"] = cm.generate_uuid()
    yield
    st.session_state.clear()

def test_initialize_conversation_state():
    # initialize_conversation_state is called by the fixture
    state = st.session_state
    assert state["stage"] == "intake"
    assert state["turn_count"] == 0
    assert isinstance(state["scratchpad"], dict)
    assert state["scratchpad"] == EMPTY_SCRATCHPAD # Check against EMPTY_SCRATCHPAD
    assert isinstance(state["conversation_history"], list)
    assert isinstance(state["user_id"], str)
    assert state["token_usage"]["daily"] == 0

def test_generate_uuid_uniqueness():
    ids = {cm.generate_uuid() for _ in range(100)}
    assert len(ids) == 100

def test_build_summary_from_scratchpad():
    scratchpad = EMPTY_SCRATCHPAD.copy()
    scratchpad["problem"] = "Test Problem"
    scratchpad["customer_segment"] = "Students"
    scratchpad["solution"] = "AI assistant"
    scratchpad["differentiator"] = "Faster support"
    scratchpad["impact_metrics"] = "Reduced study time"
    scratchpad["revenue_model"] = "SaaS subscription"
    scratchpad["channels"] = "University partnerships"
    scratchpad["competitive_moat"] = "Proprietary algorithm"

    summary = cm.build_summary_from_scratchpad(scratchpad)
    assert "Problem Statement:\nTest Problem" in summary
    assert "\nCustomer Segment:\nStudents" in summary
    assert "\nSolution:\nAI assistant" in summary
    assert "\nDifferentiator:\nFaster support" in summary
    assert "\nImpact Metrics:\nReduced study time" in summary
    assert "\nRevenue Model:\nSaaS subscription" in summary
    assert "\nChannels:\nUniversity partnerships" in summary
    assert "\nCompetitive Moat:\nProprietary algorithm" in summary

@pytest.mark.asyncio
@patch('src.conversation_manager.save_session') # Mock save_session
@patch('src.search_utils.perform_search') # Mock perform_search
async def test_generate_assistant_response(mock_perform_search, mock_save_session, monkeypatch):
    mock_perform_search.return_value = [{"title": "Mocked Search Result", "url": "http://example.com/mock"}]
    monkeypatch.setattr(cm, "query_openai", lambda prompt, **kwargs: "Mocked Gemini response.")

    st.session_state["scratchpad"] = EMPTY_SCRATCHPAD.copy() # Use EMPTY_SCRATCHPAD
    st.session_state["conversation_history"] = []
    st.session_state["summaries"] = []
    st.session_state["phase"] = "exploration" # Ensure phase is set

    response_text, search_results = await cm.generate_assistant_response("User input")
    assert "Mocked Gemini" in response_text
    assert isinstance(search_results, list)
    assert st.session_state["conversation_history"][-1]["role"] == "assistant"

def test_trim_conversation_history():
    cm.initialize_conversation_state() # Ensure full state is initialized
    st.session_state["summaries"] = ["s"] * 21
    st.session_state["conversation_history"] = [{"role": "user", "text": f"msg{i}"} for i in range(100)]
    cm.trim_conversation_history()
    assert len(st.session_state["conversation_history"]) < 100

def test_is_out_of_scope():
    assert cm.is_out_of_scope("Tell me about your diabetes records")
    assert cm.is_out_of_scope("How large is the TAM?")
    assert not cm.is_out_of_scope("How do I improve engagement?")

def test_update_token_usage(monkeypatch):
    cm.initialize_conversation_state() # Ensure full state is initialized
    st.session_state["token_usage"] = {"session": 0, "daily": 90_000}
    monkeypatch.setenv("DAILY_TOKEN_CAP", "100000")
    cm.update_token_usage(5000)
    assert st.session_state["token_usage"]["daily"] == 95_000

def test_enforce_session_time(monkeypatch):
    st.session_state["start_timestamp"] = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=46) # Use offset-aware datetime
    # Mock st.warning to prevent Streamlit runtime issues in tests
    monkeypatch.setattr(st, "warning", lambda *args, **kwargs: None)
    # Should not raise error; just return a warning message in actual use
    cm.enforce_session_time()

def test_generate_actionable_recommendations(monkeypatch):
    cm.initialize_conversation_state() # Ensure full state is initialized
    # Mock the query_openai function within the conversation_manager's namespace
    monkeypatch.setattr(cm, "query_openai", lambda prompt, **kwargs: "1. Try this idea.\n2. Consider that approach.")

    result = cm.generate_actionable_recommendations("problem", "Chronic illness management")
    assert isinstance(result, list)
    assert len(result) == 2
    assert all("Try" in r or "Consider" in r for r in result)