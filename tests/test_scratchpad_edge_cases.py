from src import conversation_manager as cm
from src.constants import EMPTY_SCRATCHPAD

def test_summary_builder_incomplete_fields():
    incomplete_scratchpad = EMPTY_SCRATCHPAD.copy()
    incomplete_scratchpad.update({
        "problem": "High readmission rates",
        "customer_segment": "", # Explicitly empty
        "solution": "Remote monitoring",
        # Other canonical keys remain empty as per EMPTY_SCRATCHPAD
    })

    summary = cm.build_summary_from_scratchpad(incomplete_scratchpad)
    assert "Problem Statement" in summary
    assert "High readmission rates" in summary
    assert "Customer Segment" in summary  # Should still render section header, using the canonical-derived term

def test_recommendations_empty_context(monkeypatch):
    monkeypatch.setattr("src.conversation_manager.query_gemini", lambda prompt: "1. Do something\n2. Try another thing")

    recs = cm.generate_actionable_recommendations("problem", "")
    assert isinstance(recs, list)
    assert len(recs) == 2