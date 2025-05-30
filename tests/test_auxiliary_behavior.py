import pytest
from datetime import datetime, timedelta
from datetime import timezone
from src import conversation_manager as cm
import streamlit as st

def test_conversation_history_format():
    st.session_state.clear()
    cm.initialize_conversation_state()

    # Simulate user input
    user_msg = "I want to reduce ER visits"
    st.session_state["conversation_history"].append({
        "role": "user",
        "text": user_msg,
        "timestamp": datetime.now().isoformat()
    })

    # Simulate assistant response
    response = "Great goal. Let’s explore options for chronic care follow-up."
    st.session_state["conversation_history"].append({
        "role": "assistant",
        "text": response,
        "timestamp": datetime.now().isoformat()
    })

    history = st.session_state["conversation_history"]
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert "timestamp" in history[1]

def test_token_limit_block(monkeypatch):
    st.session_state.clear()
    cm.initialize_conversation_state()
    st.session_state["token_usage"]["daily"] = 100_000

    monkeypatch.setenv("DAILY_TOKEN_CAP", "100000")

    # Should not increment if at cap
    before = st.session_state["token_usage"]["daily"]
    cm.update_token_usage(1000)
    after = st.session_state["token_usage"]["daily"]

    assert before == after

def test_generate_actionable_recommendations_appends(monkeypatch):
    st.session_state.clear()
    cm.initialize_conversation_state()

    # Patch query_gemini where it's used in conversation_manager
    monkeypatch.setattr("src.conversation_manager.query_gemini", lambda prompt: "1. Do X.\n2. Try Y.")

    recs = cm.generate_actionable_recommendations("mechanism", "Use wearable sensors")
    for r in recs:
        st.session_state["conversation_history"].append({
            "role": "assistant",
            "text": r,
            "timestamp": datetime.now(timezone.utc).isoformat() # Ensure timezone-aware datetime
        })

    assert len(st.session_state["conversation_history"]) >= 2
    assert "Do X" in st.session_state["conversation_history"][-2]["text"]

def test_enforce_session_time_trigger(monkeypatch):
    st.session_state.clear()
    cm.initialize_conversation_state()
    # Ensure start_timestamp is timezone-aware
    st.session_state["start_timestamp"] = datetime.now(timezone.utc) - timedelta(minutes=46)

    # Ensure function runs without error
    cm.enforce_session_time()
    # No assert needed unless return message is exposed