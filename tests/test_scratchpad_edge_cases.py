import pytest
from src import conversation_manager as cm
import streamlit as st

def test_navigate_empty_scratchpad():
    st.session_state.clear()
    cm.initialize_conversation_state()

    # Ensure all fields are blank
    for key in st.session_state["scratchpad"]:
        st.session_state["scratchpad"][key] = ""

    result = cm.navigate_value_prop_elements()
    assert isinstance(result, dict)
    assert result["element_name"] in st.session_state["scratchpad"]
    assert result["prompt_text"]
    assert result["follow_up"]

def test_summary_builder_incomplete_fields():
    incomplete_scratchpad = {
        "problem": "High readmission rates",
        "customer_segment": "",
        "solution_approach": "Remote monitoring",
        "mechanism": "",
        "unique_benefit": "",
        "high_level_competitive_view": "",
        "revenue_hypotheses": "",
        "compliance_snapshot": "",
        "top_3_risks_and_mitigations": ""
    }

    summary = cm.build_summary_from_scratchpad(incomplete_scratchpad)
    assert "Problem Statement" in summary
    assert "High readmission rates" in summary
    assert "Target User" in summary  # Should still render section header

def test_recommendations_empty_context(monkeypatch):
    monkeypatch.setattr("src.conversation_manager.query_gemini", lambda prompt: "1. Do something\n2. Try another thing")

    recs = cm.generate_actionable_recommendations("problem", "")
    assert isinstance(recs, list)
    assert len(recs) == 2