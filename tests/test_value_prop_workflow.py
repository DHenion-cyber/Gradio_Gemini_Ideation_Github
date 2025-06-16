import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
from src.workflows.value_prop import ValuePropWorkflow
from src.personas.coach import CoachPersona
from src.constants import EMPTY_SCRATCHPAD

# Fixture to reset Streamlit's session_state for each test
@pytest.fixture(autouse=True)
def reset_session_state():
    """Resets Streamlit's session_state before each test."""
    st.session_state.clear()
    # Initialize minimal session state for workflow to function
    st.session_state["conversation_history"] = []
    st.session_state["scratchpad"] = EMPTY_SCRATCHPAD.copy()
    st.session_state["selected_workflow_name"] = "value_prop"
    st.session_state["selected_persona_name"] = "coach"
    st.session_state["current_workflow_instance"] = None
    st.session_state["current_persona_instance"] = None
    st.session_state["stage"] = "intake" # Initial stage for the app
    st.session_state["intake_index"] = 0
    st.session_state["intake_answers"] = []
    yield
    st.session_state.clear()

@pytest.fixture
def mock_persona():
    """Mocks the CoachPersona for testing."""
    mock = MagicMock(spec=CoachPersona)
    mock.greet_and_explain_value_prop_process.return_value = "Hello, let's start!"
    mock.get_intake_to_ideation_transition_message.return_value = "Great, let's ideate!"
    mock.get_step_intro_message.side_effect = lambda step, scratchpad: f"Tell me about your {step.replace('_', ' ')}."
    mock.detect_user_stance.return_value = "decided" # Default to decided for testing progression
    mock.coach_on_decision.return_value = "Understood."
    mock.paraphrase_user_input.return_value = "Okay, let's explore that."
    mock.capture_spirit_of_value_prop_conversation.return_value = "A productive session."
    mock.get_reflection_prompt.return_value = " What are your thoughts?"
    mock.get_prompt_for_empty_input.return_value = "Please provide input."
    return mock

@pytest.fixture
def value_prop_workflow(mock_persona):
    """Initializes ValuePropWorkflow with a mocked persona."""
    st.session_state.coach_persona_instance = mock_persona
    workflow = ValuePropWorkflow(context={"persona_instance": mock_persona})
    st.session_state.value_prop_workflow_instance = workflow
    st.session_state.current_workflow_type = "value_prop"
    return workflow

@patch('src.llm_utils.query_openai', return_value="Mocked LLM response for scratchpad update.")
@patch('src.conversation_manager.save_session')
def test_value_prop_workflow_full_phase_progression(mock_save_session, mock_query_openai, value_prop_workflow, mock_persona):
    """
    Tests the full, sequential progression through all Value Proposition workflow phases,
    ensuring no phases are skipped and 'decided' input still requires ideation steps.
    """
    workflow = value_prop_workflow
    
    # 1. Intake Phase (simulated by setting stage and then processing first input)
    st.session_state.stage = "intake"
    st.session_state.intake_index = 0
    
    # Simulate initial user input that would typically come after intake questions
    # In real app, intake questions are handled by run_intake_flow in conversation_manager
    # Here, we directly simulate the transition logic within process_user_input
    workflow.process_user_input("My initial idea is a health app.")
    assert workflow.get_phase() == "ideation"
    assert "Great, let's ideate!" in st.session_state.conversation_history[-1]["text"]
    assert st.session_state.stage == "ideation" # UI stage should also update

    # 2. Ideation Phase - Must go through all steps
    # Simulate user being "decided" for each step, but still requiring input for each.
    ideation_steps = workflow.IDEATION_STEPS # ["problem", "target_customer", "solution", "main_benefit", "differentiator", "use_case"]

    for i, step in enumerate(ideation_steps):
        st.session_state.stage = "ideation" # Ensure UI stage is ideation
        assert workflow.get_phase() == "ideation"
        
        # Simulate user input for the current ideation step
        user_input = f"My {step.replace('_', ' ')} is: {step} detail."
        
        # Mock persona to always return "decided" stance
        mock_persona.detect_user_stance.return_value = "decided"
        
        response = workflow.process_user_input(user_input)
        
        # Assert scratchpad is updated
        assert workflow.scratchpad.get(step) == user_input
        
        # Assert that we remain in ideation until all fields are filled
        if i < len(ideation_steps) - 1:
            assert workflow.get_phase() == "ideation"
            assert st.session_state.stage == "ideation"
            assert f"Tell me about your {ideation_steps[i+1].replace('_', ' ')}." in response # Expect prompt for next step
        else:
            # After the last ideation step, it should transition to recommendation
            assert workflow.get_phase() == "recommendation"
            assert st.session_state.stage == "recommendation"
            assert "Great! We've filled out the core aspects of your value proposition. Let's move on to recommendations." in response

    # 3. Recommendation Phase
    st.session_state.stage = "recommendation"
    assert workflow.get_phase() == "recommendation"
    
    # Simulate user input to trigger recommendations (or just let it generate on first entry)
    response = workflow.process_user_input("Show me recommendations.")
    assert "Now, let's look at some recommendations based on your value proposition." in response
    assert "What would you like to do next? We can iterate on these points, revisit other areas of your value proposition, or move to a summary." in response
    
    # Simulate user choosing to iterate
    response = workflow.process_user_input("Let's iterate.")
    assert workflow.get_phase() == "iteration"
    assert st.session_state.stage == "iteration"
    assert "Okay, let's iterate on your value proposition." in response

    # 4. Iteration Phase
    st.session_state.stage = "iteration"
    assert workflow.get_phase() == "iteration"

    # Simulate user choosing to re-run recommendations (cycle back)
    response = workflow.process_user_input("Rerun recommendations.")
    assert workflow.get_phase() == "recommendation"
    assert st.session_state.stage == "recommendation"
    assert "Alright, I'll prepare a new set of recommendations based on the current state of your value proposition." in response

    # Simulate user choosing to go to iteration again
    response = workflow.process_user_input("Back to iteration.")
    assert workflow.get_phase() == "iteration"
    assert st.session_state.stage == "iteration"
    assert "We are now in the iteration phase." in response # Initial iteration prompt

    # Simulate user choosing to go to summary
    response = workflow.process_user_input("Proceed to summary.")
    assert workflow.get_phase() == "summary"
    assert st.session_state.stage == "summary"
    assert "Great! Let's move to the final summary of your value proposition." in response
    assert workflow.completed is True

    # 5. Summary Phase
    st.session_state.stage = "summary"
    assert workflow.get_phase() == "summary"
    assert workflow.completed is True
    
    # Simulate asking for summary again
    response = workflow.process_user_input("Show summary again.")
    assert "Here is your summary again" in response
    assert workflow.completed is True

    mock_save_session.assert_called() # Ensure sessions were saved throughout