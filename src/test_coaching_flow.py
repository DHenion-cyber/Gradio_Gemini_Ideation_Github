import streamlit as st
import pytest

# from src import conversation_phases # Removed
from src.workflows.value_prop import ValuePropWorkflow
from src.personas.coach import CoachPersona
from src.constants import EMPTY_SCRATCHPAD
# from src import llm_utils # If direct mocking of query_openai is needed

@pytest.fixture(autouse=True)
def reset_session_state_fixture(): # Renamed to avoid conflict if a test is named reset_session_state
    st.session_state.clear()
    st.session_state["scratchpad"] = EMPTY_SCRATCHPAD.copy()
    st.session_state["intake_answers"] = []
    st.session_state["conversation_history"] = []
    st.session_state["exploration_turns"] = 0 # May become obsolete
    st.session_state["development_turns"] = 0 # May become obsolete
    st.session_state["perplexity_calls"] = 0
    st.session_state["vp_intake_complete"] = False # For ValuePropWorkflow logic
    yield
    st.session_state.clear()

@pytest.fixture
def coach_persona_instance():
    return CoachPersona()

@pytest.fixture
def value_prop_workflow_instance(coach_persona_instance):
    # ValuePropWorkflow uses its own scratchpad initially but syncs with st.session_state["scratchpad"]
    # The reset_session_state_fixture ensures st.session_state["scratchpad"] is clean.
    workflow = ValuePropWorkflow(persona_instance=coach_persona_instance)
    return workflow

def test_intake_to_exploration_transition(value_prop_workflow_instance):
    """After intake, chatbot uses user input to begin idea exploration."""
    workflow = value_prop_workflow_instance
    # Simulate intake answers (though ValuePropWorkflow doesn't directly use st.session_state["intake_answers"])
    st.session_state["intake_answers"] = [
        {"text": "I am a nurse."},
        {"text": "I'm interested in patient engagement."},
        {"text": "I have an idea for an AI-powered check-in tool."}
    ]
    # User input triggers exploration
    user_message = "Let's brainstorm my AI-powered check-in tool."
    # The workflow's process_user_input now handles this.
    # It uses its own scratchpad, which is EMPTY_SCRATCHPAD initially.
    # current_step is "problem".
    reply = workflow.process_user_input(user_message)
    
    # The "phase" is now an internal step of the workflow.
    # After initial exploration, the step should ideally still be "problem"
    # as the LLM asks a question to define it.
    assert workflow.get_step() == "problem" # Or the next step if exploration filled it
    assert any(kw in reply.lower() for kw in ["explore", "brainstorm", "idea", "problem", "what problem"]) # Check for exploration-like keywords

# def test_exploration_to_development_by_user_intent(value_prop_workflow_instance):
#     """User intent to move forward triggers transition to development phase."""
#     # This test is difficult to adapt directly as "development phase" is not an explicit
#     # return of ValuePropWorkflow. ValuePropWorkflow moves through defined steps.
#     # "value_prop_confirmed" logic is likely handled by ConversationManager or LLM response.
#     # Commenting out for now.
#     # workflow = value_prop_workflow_instance
#     # st.session_state["intake_answers"] = [
#     #     {"text": "I have an idea for a medication reminder app."}
#     # ]
#     # # Simulate that exploration has occurred and value prop might be confirmed by user
#     # # This would typically be managed by ConversationManager
#     # # For this test, we might assume workflow.scratchpad is somewhat filled.
#     # workflow.scratchpad["problem"] = "Patients forget medication"
#     # workflow.scratchpad["target_customer"] = "Elderly patients"
#     # workflow.scratchpad["solution"] = "Reminder app"
#     # workflow.scratchpad["main_benefit"] = "Better adherence"
#     # # workflow.scratchpad["value_prop_confirmed"] = True # This flag was on st.session_state.scratchpad
#     # Kvality # This line seems to be a typo, removing
#     user_message = "I'm ready to start planning how it works." # This implies moving past VP definition
#     reply = workflow.process_user_input(user_message)
#     # Assert that the workflow is now asking for the next logical step or has completed.
#     # This depends on how ValuePropWorkflow handles completion or transition.
#     # For now, this test is too complex to adapt without more info on ConversationManager.
#     pass


def test_exploration_remains_until_user_is_ready(value_prop_workflow_instance):
    """Exploration continues with follow-ups until the user signals readiness."""
    workflow = value_prop_workflow_instance
    st.session_state["intake_answers"] = [{"text": "Idea: patient scheduling AI"}]
    
    user_message = "Tell me more about defining the problem."
    reply = workflow.process_user_input(user_message)
    assert workflow.get_step() == "problem" # Should still be on problem or guided by LLM
    assert "problem" in reply.lower() or "explore" in reply.lower()

    user_message_2 = "Maybe it could also help with patient education?" # User provides more exploratory input
    reply_2 = workflow.process_user_input(user_message_2)
    # The step might still be problem, or LLM might have guided based on input.
    # The key is that the conversation continues in an exploratory/value-prop definition manner.
    assert "patient education" in workflow.scratchpad.get(workflow.get_step(),"") or "problem" in reply_2.lower() or "solution" in reply_2.lower()
    assert "explore" in reply_2.lower() or "brainstorm" in reply_2.lower() or "value proposition" in reply_2.lower()


# def test_development_to_summary_on_user_signal(value_prop_workflow_instance):
#     """Transition to summary phase when user signals readiness."""
#     # `handle_development` is gone. ValuePropWorkflow manages steps.
#     # A user asking for a summary would be processed by `process_user_input`
#     # or a dedicated `generate_summary` call.
#     # Commenting out as "development phase" and "summary phase" transitions are implicit now.
#     pass

# def test_development_loop_continues_with_refinement(value_prop_workflow_instance):
#     """Development phase loops, refining details with user feedback."""
#     # `handle_development` is gone. `process_user_input` handles step-by-step refinement.
#     # Commenting out.
#     pass

def test_summary_generation_from_workflow(value_prop_workflow_instance):
    """Workflow can generate a summary of its current scratchpad."""
    workflow = value_prop_workflow_instance
    workflow.scratchpad = {
        "problem": "Missed medications",
        "target_customer": "Older adults",
        "solution": "SMS reminders",
        "main_benefit": "Ensures medication adherence",
        "differentiator": "Integrates with pharmacy",
        "use_case": "Daily reminders sent before meal times.",
        "research_requests": []
    }
    st.session_state["scratchpad"] = workflow.scratchpad # Ensure session state is in sync for persona
    
    summary = workflow.generate_summary() # Calls persona's generate_value_prop_summary
    
    assert "Missed medications" in summary
    assert "Older adults" in summary
    assert "SMS reminders" in summary
    assert "Ensures medication adherence" in summary
    assert "Integrates with pharmacy" in summary
    assert "Daily reminders sent before meal times" in summary

# def test_refinement_allows_new_idea_restart(value_prop_workflow_instance):
#     """Refinement phase lets user restart with a new idea."""
#     # `handle_refinement` is gone. "New idea" logic is likely a ConversationManager task
#     # (e.g., creating a new workflow instance).
#     # Commenting out.
#     pass

# def test_refinement_loops_on_normal_input(value_prop_workflow_instance):
#     """Refinement continues, allowing more detailed discussion."""
#     # `handle_refinement` is gone. `process_user_input` handles this.
#     # This is covered by general step processing of ValuePropWorkflow.
#     # Commenting out.
#     pass
