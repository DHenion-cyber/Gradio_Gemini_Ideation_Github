"""Tests for the conversation_manager module, covering state initialization, response generation, and flow control."""
import pytest
import datetime
from src import conversation_manager as cm
from src.constants import EMPTY_SCRATCHPAD # Import for tests
import streamlit as st
from unittest.mock import patch # Added for save_session mocking

# The reset_session_state fixture is now in conftest.py and will be auto-used.

def test_initialize_conversation_state():
    # initialize_conversation_state is called by the fixture
    state = st.session_state
    assert state["stage"] == "intake"
    assert state["turn_count"] == 0
    assert isinstance(state["scratchpad"], dict)
    assert state["scratchpad"] == EMPTY_SCRATCHPAD # Check against EMPTY_SCRATCHPAD
    assert isinstance(state["conversation_history"], list)
    assert state["intake_answers"] == [] # Check for intake_answers initialization
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

@pytest.mark.llm_mocked
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

@pytest.mark.parametrize(
    "text_input, expected_output",
    [
        ("Tell me about your diabetes records", True),
        ("How large is the TAM?", True),
        ("Can you share PII?", True), # Example of another out-of-scope
        ("What's your privacy policy regarding health data?", True), # Example
        ("How do I improve engagement?", False),
        ("What are some good business ideas?", False), # Example of in-scope
        ("Let's talk about value proposition.", False), # Example
    ],
)
def test_is_out_of_scope(text_input, expected_output):
    assert cm.is_out_of_scope(text_input) == expected_output

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

@pytest.mark.llm_mocked
def test_generate_actionable_recommendations(monkeypatch):
    cm.initialize_conversation_state() # Ensure full state is initialized
    # Mock the query_openai function within the conversation_manager's namespace
    monkeypatch.setattr(cm, "query_openai", lambda prompt, **kwargs: "1. Try this idea.\n2. Consider that approach.")

    result = cm.generate_actionable_recommendations("problem", "Chronic illness management")
    assert isinstance(result, list)
    assert len(result) == 2
    assert all("Try" in r or "Consider" in r for r in result)

@patch('src.conversation_manager.save_session') # Mock save_session for run_intake_flow
def test_run_intake_flow_modifies_intake_answers_and_scratchpad(mock_save_session):
    cm.initialize_conversation_state() # Ensure clean state
    st.session_state["conversation_history"] = [] # Explicitly empty for this test
    st.session_state["intake_answers"] = []
    st.session_state["intake_index"] = 0
    st.session_state["scratchpad"] = cm.EMPTY_SCRATCHPAD.copy()

    questions = cm.get_intake_questions()
    
    # Answer first question
    user_input_1 = "Test response 1"
    cm.run_intake_flow(user_input_1)
    assert len(st.session_state["conversation_history"]) == 0
    assert len(st.session_state["intake_answers"]) == 1
    assert st.session_state["intake_answers"][0]["text"] == user_input_1
    assert st.session_state["intake_answers"][0]["meta"] == "intake"
    assert st.session_state["intake_index"] == 1
    # No direct scratchpad update for question 0 in current logic

    # Answer second question (index 1 - "Problems interested in")
    user_input_2 = "Test problem"
    cm.run_intake_flow(user_input_2)
    assert len(st.session_state["conversation_history"]) == 0
    assert len(st.session_state["intake_answers"]) == 2
    assert st.session_state["intake_answers"][1]["text"] == user_input_2
    assert st.session_state["scratchpad"]["problem"] == user_input_2
    assert st.session_state["intake_index"] == 2

    # Answer third question (index 2 - "Areas of orientation")
    user_input_3 = "Patient Impact"
    cm.run_intake_flow(user_input_3)
    assert len(st.session_state["conversation_history"]) == 0
    assert len(st.session_state["intake_answers"]) == 3
    assert st.session_state["intake_answers"][2]["text"] == user_input_3
    assert st.session_state["scratchpad"]["solution"] == user_input_3 # Mapped to 'solution'
    assert st.session_state["intake_index"] == 3
    
    mock_save_session.assert_called() # Ensure state is saved

@patch('src.conversation_manager.save_session') # Mock save_session
@patch('src.conversation_manager.get_intake_questions')
def test_intake_completion_transitions_to_ideation(mock_get_intake_questions, mock_save_session):
    # Mock get_intake_questions to return a small, controlled list
    mock_questions = [
        "Mock Question 1: Experience?",
        "Mock Question 2: Problems?"
    ]
    mock_get_intake_questions.return_value = mock_questions

    cm.initialize_conversation_state() # Start with a fresh state
    st.session_state["conversation_history"] = [] # Ensure it starts empty
    st.session_state["intake_answers"] = []

    # Simulate answering all mock intake questions
    for i, question in enumerate(mock_questions):
        user_response = f"Answer to mock question {i+1}"
        cm.run_intake_flow(user_response)
        assert st.session_state["intake_answers"][-1]["text"] == user_response
        assert st.session_state["conversation_history"] == [] # History should remain empty

    # After all questions are answered
    assert st.session_state["stage"] == "ideation"
    assert st.session_state["conversation_history"] == [] # Verify again, crucial for the test
    assert len(st.session_state["intake_answers"]) == len(mock_questions)
    
    # Ensure save_session was called after each intake step and potentially at the end
    assert mock_save_session.call_count >= len(mock_questions)