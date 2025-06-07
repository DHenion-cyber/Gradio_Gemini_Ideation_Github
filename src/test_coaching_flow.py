import streamlit as st
import pytest

from src import conversation_phases
from src.constants import EMPTY_SCRATCHPAD

@pytest.fixture(autouse=True)
def reset_session_state():
    st.session_state.clear()
    st.session_state["scratchpad"] = EMPTY_SCRATCHPAD.copy()
    st.session_state["intake_answers"] = []
    st.session_state["conversation_history"] = []   # <-- add this line
    st.session_state["exploration_turns"] = 0
    st.session_state["development_turns"] = 0
    st.session_state["perplexity_calls"] = 0
    yield
    st.session_state.clear()


def test_intake_to_exploration_transition():
    """After intake, chatbot uses user input to begin idea exploration."""
    # Simulate intake answers
    st.session_state["intake_answers"] = [
        {"text": "I am a nurse."},
        {"text": "I'm interested in patient engagement."},
        {"text": "I have an idea for an AI-powered check-in tool."}
    ]
    # User input triggers exploration
    user_message = "Let's brainstorm my AI-powered check-in tool."
    reply, phase = conversation_phases.handle_exploration(user_message, st.session_state["scratchpad"])
    assert phase == "exploration"
    assert any(kw in reply.lower() for kw in ["explore", "brainstorm", "idea", "directions"])

def test_exploration_to_development_by_user_intent():
    """User intent to move forward triggers transition to development phase."""
    st.session_state["intake_answers"] = [
        {"text": "I have an idea for a medication reminder app."}
    ]
    st.session_state["exploration_turns"] = 4  # Simulate several exploration turns
    user_message = "I'm ready to start planning how it works."
    reply, phase = conversation_phases.handle_exploration(user_message, st.session_state["scratchpad"])
    assert phase == "development"
    assert any(kw in reply.lower() for kw in ["refining", "organizing", "which aspect", "delve"])

def test_exploration_remains_until_user_is_ready():
    """Exploration continues with follow-ups until the user signals readiness."""
    st.session_state["intake_answers"] = [{"text": "Idea: patient scheduling AI"}]
    st.session_state["exploration_turns"] = 2
    user_message = "Maybe it could also help with patient education?"
    reply, phase = conversation_phases.handle_exploration(user_message, st.session_state["scratchpad"])
    assert phase == "exploration"
    assert "explore" in reply.lower() or "brainstorm" in reply.lower()

def test_development_to_summary_on_user_signal():
    """Transition to summary phase when user signals readiness."""
    st.session_state["intake_answers"] = [{"text": "Chronic care chatbot"}]
    st.session_state["development_turns"] = 4
    user_message = "I'm ready for a summary."
    reply, phase = conversation_phases.handle_development(user_message, st.session_state["scratchpad"])
    assert phase == "summary"
    assert "summarize" in reply.lower() or "review" in reply.lower()

def test_development_loop_continues_with_refinement():
    """Development phase loops, refining details with user feedback."""
    st.session_state["intake_answers"] = [{"text": "Diabetes coaching app"}]
    st.session_state["development_turns"] = 2
    user_message = "Let's flesh out features for onboarding."
    reply, phase = conversation_phases.handle_development(user_message, st.session_state["scratchpad"])
    assert phase == "development"
    assert any(kw in reply.lower() for kw in ["flesh", "aspect", "practice", "benefit"])

def test_summary_phase_provides_structured_summary():
    """Summary phase provides an overview and invites next steps."""
    # Simulate filled scratchpad
    scratchpad = {
        "problem": "Missed medications",
        "customer_segment": "Older adults",
        "solution": "SMS reminders",
        "differentiator": "Integrates with pharmacy",
        "impact_metrics": "Improved adherence"
    }
    reply, phase = conversation_phases.handle_summary("Summarize our work.", scratchpad)
    assert phase == "refinement"
    assert "summary" in reply.lower()
    assert "sms reminders" in reply.lower()  # Example from scratchpad

def test_refinement_allows_new_idea_restart():
    """Refinement phase lets user restart with a new idea."""
    st.session_state["perplexity_calls"] = 2
    user_message = "Let's try a new idea."
    reply, phase = conversation_phases.handle_refinement(user_message, st.session_state["scratchpad"])
    assert phase == "exploration"
    assert any(kw in reply.lower() for kw in ["fresh", "new idea", "start"])

def test_refinement_loops_on_normal_input():
    """Refinement continues, allowing more detailed discussion."""
    user_message = "Can we clarify who benefits most?"
    reply, phase = conversation_phases.handle_refinement(user_message, st.session_state["scratchpad"])
    assert phase == "refinement"
    assert "refine" in reply.lower() or "expand" in reply.lower() or "clarify" in reply.lower()
