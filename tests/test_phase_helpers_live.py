import pytest
from src import constants
import src.conversation_phases as cp

def test_handle_exploration_live():
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    reply, phase = cp.handle_exploration("I want to build an AI RPM tool", scratchpad)
    assert phase in ("development", "exploration")
    assert isinstance(reply, str)
    assert len(reply) > 0

def test_handle_development_live():
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    reply, phase = cp.handle_development("Let's define the core features.", scratchpad)
    assert phase in ("development", "refinement")
    assert isinstance(reply, str)
    assert len(reply) > 0

def test_handle_refinement_live():
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    reply, phase = cp.handle_refinement("What about the user interface?", scratchpad)
    assert phase in ("refinement", "development", "research")
    assert isinstance(reply, str)
    assert len(reply) > 0

def test_handle_research_live():
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    reply, phase = cp.handle_research("Find out about existing AI RPM tools.", scratchpad)
    assert phase in ("research", "development", "refinement")
    assert isinstance(reply, str)
    assert len(reply) > 0

def test_handle_summary_live():
    scratchpad = constants.EMPTY_SCRATCHPAD.copy()
    # Pre-fill scratchpad with all keys to simulate a complete conversation
    for key in constants.EMPTY_SCRATCHPAD.keys():
        scratchpad[key] = f"dummy_value_for_{key}"
    
    reply, phase = cp.handle_summary("Summarize our progress.", scratchpad)
    assert phase == "refinement" # Expect refinement after summary
    assert isinstance(reply, str)
    assert len(reply) > 0