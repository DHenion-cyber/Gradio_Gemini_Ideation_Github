import pytest
import datetime
from src import conversation_manager as cm
import streamlit as st

@pytest.fixture(autouse=True)
def reset_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()

def test_initialize_conversation_state():
    cm.initialize_conversation_state()
    state = st.session_state
    assert state["stage"] == "intake"
    assert state["turn_count"] == 0
    assert isinstance(state["scratchpad"], dict)
    assert "problem" in state["scratchpad"]
    assert isinstance(state["conversation_history"], list)
    assert isinstance(state["user_id"], str)
    assert state["token_usage"]["daily"] == 0

def test_generate_uuid_uniqueness():
    ids = {cm.generate_uuid() for _ in range(100)}
    assert len(ids) == 100

def test_build_summary_from_scratchpad():
    scratchpad = {
        "problem": "Test Problem",
        "customer_segment": "Students",
        "solution_approach": "AI assistant",
        "mechanism": "Chatbot",
        "unique_benefit": "Faster support",
        "high_level_competitive_view": "None known",
        "revenue_hypotheses": "SaaS subscription",
        "compliance_snapshot": "No PHI",
        "top_3_risks_and_mitigations": "Low adoption - pilot first"
    }
    summary = cm.build_summary_from_scratchpad(scratchpad)
    assert "Problem Statement" in summary
    assert "Students" in summary

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_generate_assistant_response(monkeypatch):
    cm.initialize_conversation_state() # Ensure full state is initialized
    # Mock the query_gemini function within the conversation_manager's namespace
    monkeypatch.setattr(cm, "query_gemini", lambda prompt, **kwargs: "Mocked Gemini response.")

    st.session_state["scratchpad"] = {"problem": "Test", "customer_segment": "", "solution_approach": "", "mechanism": "", "unique_benefit": "", "high_level_competitive_view": "", "revenue_hypotheses": "", "compliance_snapshot": "", "top_3_risks_and_mitigations": ""}
    st.session_state["conversation_history"] = []
    st.session_state["summaries"] = [] # Explicitly initialize summaries for this test

    response_text, search_results = await cm.generate_assistant_response("What is the main issue?")
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

def test_navigate_value_prop_elements_all_empty():
    cm.initialize_conversation_state()
    result = cm.navigate_value_prop_elements()
    assert isinstance(result, dict)
    assert "element_name" in result
    assert "prompt_text" in result
    assert "follow_up" in result
    assert result["element_name"] in cm.st.session_state["scratchpad"]

def test_navigate_value_prop_elements_partial_fill():
    cm.initialize_conversation_state()
    cm.st.session_state["scratchpad"]["problem"] = "Defined already"
    result = cm.navigate_value_prop_elements()
    assert result["element_name"] != "problem"

def test_generate_actionable_recommendations(monkeypatch):
    cm.initialize_conversation_state() # Ensure full state is initialized
    # Mock the query_gemini function within the conversation_manager's namespace
    monkeypatch.setattr(cm, "query_gemini", lambda prompt, **kwargs: "1. Try this idea.\n2. Consider that approach.")

    result = cm.generate_actionable_recommendations("problem", "Chronic illness management")
    assert isinstance(result, list)
    assert len(result) == 2
    assert all("Try" in r or "Consider" in r for r in result)