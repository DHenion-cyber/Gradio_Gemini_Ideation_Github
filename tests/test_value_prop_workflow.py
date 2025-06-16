import pytest
from unittest.mock import MagicMock, patch, call
import streamlit as st # Import for patching

from src.personas.coach import CoachPersona
from src.workflows.value_prop import ValuePropWorkflow # Corrected import

# Define constants for phases and ideation steps for clarity in tests
PHASES = ["intake", "ideation", "recommendation", "iteration", "summary"]
IDEATION_STEPS = ["problem", "target_customer", "solution", "main_benefit", "differentiator", "use_case"]

@pytest.fixture
def workflow_components():
    """Set up common test objects for ValuePropWorkflow tests."""
    mock_persona = MagicMock() # spec=CoachPersona REMOVED as per plan
    # Configure return values for persona methods to prevent TypeErrors
    mock_persona.greet_and_explain_value_prop_process.return_value = "Hello! Let's start with your value proposition. What problem are you solving?"
    mock_persona.active_listening.return_value = "Okay, I understand."
    mock_persona.get_intake_to_ideation_transition_message.return_value = "Great start! Now let's move to ideation."
    mock_persona.get_step_intro_message.return_value = "Let's talk about the problem."
    mock_persona.get_reflection_prompt.return_value = "What are your thoughts?"
    mock_persona.detect_user_cues.return_value = "neutral" # Generic default
    mock_persona.coach_on_decision.return_value = "That's a good decision." # Generic default
    mock_persona.paraphrase_user_input.return_value = "So you're saying..." # Generic default
    mock_persona.offer_reflective_summary.return_value = "Reflecting on our progress..." # Generic default
    mock_persona.communicate_next_step.return_value = "Let's move to the next step." # Generic default
    mock_persona.present_recommendations_and_ask_next.return_value = "Here are recommendations. Next?" # Generic default
    mock_persona.prompt_after_recommendations.return_value = "Recommendations shown. What now?" # Generic default
    mock_persona.introduce_iteration_phase.return_value = "Welcome to iteration." # Generic default
    mock_persona.ask_which_part_to_revise.return_value = "Which part would you like to revise?" # As per plan
    mock_persona.ask_iteration_next_action.return_value = "What would you like to do next in iteration?" # As per plan
    mock_persona.present_existing_summary.return_value = "Here is the existing summary." # As per plan
    mock_persona.get_prompt_for_empty_input.return_value = "Could you please provide some input for this step?" # Added mock
    mock_persona.generate_value_prop_summary.return_value = "This is a generated summary from persona." # Added mock

    initial_scratchpad_content = {step: "" for step in IDEATION_STEPS} | {"research_requests": []}
    # This dictionary will be used as st.session_state by the workflow during the test
    mock_st_session_state_dict = {"scratchpad": initial_scratchpad_content}

    # Patch streamlit.session_state globally for the scope of this test execution
    # so that when ValuePropWorkflow accesses st.session_state, it gets mock_st_session_state_dict.
    with patch("streamlit.session_state", new=mock_st_session_state_dict):
        workflow = ValuePropWorkflow(context={'persona_instance': mock_persona})
        # ValuePropWorkflow.__init__ will interact with mock_st_session_state_dict.
        # Any changes the workflow makes to st.session_state will be reflected in mock_st_session_state_dict.
        # Any reads the workflow does from st.session_state will come from mock_st_session_state_dict.
        yield workflow, mock_persona, mock_st_session_state_dict

@patch('src.utils.scratchpad_extractor.update_scratchpad') # Corrected patch target
@patch('streamlit.write') # Patch st.write if it's used directly and needs to be ignored
class TestValuePropositionWorkflow:

    def test_initialization(self, mock_st_write, mock_update_scratchpad, workflow_components):
        """Test that the workflow initializes correctly."""
        workflow, mock_persona, mock_session_state = workflow_components
        assert workflow is not None
        assert workflow.persona == mock_persona
        assert workflow.current_phase == PHASES[0]  # "intake"
        assert workflow.current_ideation_step == IDEATION_STEPS[0] # "problem"
        # Check that workflow.scratchpad has the same content as the one in mock_session_state
        # and that mock_session_state (which is st.session_state) actually has 'scratchpad'
        assert "scratchpad" in mock_session_state, "scratchpad key missing from mock_session_state"
        assert workflow.scratchpad == mock_session_state['scratchpad']
        assert workflow.scratchpad == {
            "problem": "", "target_customer": "", "solution": "",
            "main_benefit": "", "differentiator": "", "use_case": "",
            "research_requests": []
        }
        assert not workflow.completed

    def test_initial_greeting_in_intake_phase(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test the initial greeting when no user input is provided in the intake phase."""
        workflow, mock_persona, mock_session_state = workflow_components
        response = workflow.process_user_input("")
        
        mock_persona.greet_and_explain_value_prop_process.assert_called_once()
        expected_response = "Hello! Let's start with your value proposition. What problem are you solving?"
        assert response == expected_response
        assert workflow.current_phase == PHASES[0] # Still "intake"

    def test_intake_to_ideation_transition_on_first_input(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transition from intake to ideation upon receiving the first user input."""
        workflow, mock_persona, mock_session_state = workflow_components
        
        # Mock update_scratchpad to return an updated scratchpad
        initial_scratchpad = workflow.scratchpad.copy() # Use workflow.scratchpad
        updated_scratchpad_after_input = initial_scratchpad.copy()
        updated_scratchpad_after_input["problem"] = "Initial user idea" # Simulate scratchpad update
        mock_update_scratchpad.return_value = updated_scratchpad_after_input

        user_input = "I have an idea for a new app."

        response = workflow.process_user_input(user_input)

        mock_update_scratchpad.assert_called_once_with(user_input, initial_scratchpad)
        mock_persona.active_listening.assert_called_once_with(user_input)
        mock_persona.get_intake_to_ideation_transition_message.assert_called_once()
        
        # After transition, current_phase is "ideation", current_ideation_step is "problem"
        mock_persona.get_step_intro_message.assert_called_once_with(IDEATION_STEPS[0], updated_scratchpad_after_input)

        assert workflow.current_phase == PHASES[1]  # "ideation"
        assert workflow.scratchpad == updated_scratchpad_after_input # workflow.scratchpad is updated
        
        expected_response_parts = [
            "Okay, I understand.", # from active_listening
            # "Great start! Now let's move to ideation.", # This part was removed from the response
            "Let's talk about the problem." # from get_step_intro_message
        ]
        # The reflection prompt " What are your thoughts?" is added if the response doesn't end with "?"
        expected_response = "Okay, I understand. Let's talk about the problem. What are your thoughts?"
        assert response == expected_response
        assert mock_session_state["scratchpad"] == updated_scratchpad_after_input
        assert mock_session_state.get(f"vp_intro_{IDEATION_STEPS[0]}") is True

    def test_ideation_step_intro_if_no_input(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test that the intro for an ideation step is shown if no user input is provided."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[1] # "ideation"
        workflow.current_ideation_step = IDEATION_STEPS[0] # "problem"
        mock_persona.get_step_intro_message.return_value = "Let's define the problem you're solving. What is it?"
        
        response = workflow.process_user_input("")

        mock_persona.get_step_intro_message.assert_called_once_with(IDEATION_STEPS[0], workflow.scratchpad)
        assert response == "Let's define the problem you're solving. What is it?"
        assert mock_session_state.get(f"vp_intro_{IDEATION_STEPS[0]}") is True
        mock_update_scratchpad.assert_not_called() # No input, so no scratchpad update

    def test_ideation_process_input_and_suggest_next_step_decided_cue(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test processing user input in ideation with a 'decided' cue and suggesting the next step."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[1] # "ideation"
        workflow.current_ideation_step = IDEATION_STEPS[0] # "problem"
        
        user_input = "The problem is lack of affordable childcare."
        initial_scratchpad = workflow.scratchpad.copy()
        updated_scratchpad_after_input = initial_scratchpad.copy()
        updated_scratchpad_after_input[IDEATION_STEPS[0]] = user_input # "problem"
        mock_update_scratchpad.return_value = updated_scratchpad_after_input

        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.coach_on_decision.return_value = f"That's a clear problem: {user_input}. What's the target customer?"
        
        # Simulate session state for intro being handled
        mock_session_state[f"vp_intro_{IDEATION_STEPS[0]}"] = True

        response = workflow.process_user_input(user_input)

        mock_update_scratchpad.assert_called_once_with(user_input, initial_scratchpad)
        mock_persona.detect_user_cues.assert_called_once_with(user_input, IDEATION_STEPS[0])
        mock_persona.coach_on_decision.assert_called_once_with(
            IDEATION_STEPS[0], user_input, updated_scratchpad_after_input, "decided"
        )
        
        assert workflow.scratchpad == updated_scratchpad_after_input
        assert workflow.current_ideation_step == IDEATION_STEPS[1] # "target_customer"
        assert response == f"That's a clear problem: {user_input}. What's the target customer?"
        assert mock_session_state["scratchpad"] == updated_scratchpad_after_input
        assert mock_session_state.get("vp_ideation_started") is True

    def test_ideation_process_input_paraphrase_uncertain_cue(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test processing user input in ideation with an 'uncertain' cue, using paraphrase."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[1] # "ideation"
        workflow.current_ideation_step = IDEATION_STEPS[1] # "target_customer"
        
        # Simulate that "problem" was filled in a previous step directly in the workflow's scratchpad
        workflow.scratchpad[IDEATION_STEPS[0]] = "Lack of affordable childcare"

        user_input = "Maybe working parents?" # This input is for "target_customer"
        
        # This is the state of the scratchpad that update_scratchpad will be called with
        initial_scratchpad_as_called = workflow.scratchpad.copy()
        
        # This is what update_scratchpad is expected to return after processing the current input
        updated_scratchpad_after_input = initial_scratchpad_as_called.copy()
        updated_scratchpad_after_input[IDEATION_STEPS[1]] = user_input # "target_customer" is updated
        mock_update_scratchpad.return_value = updated_scratchpad_after_input

        mock_persona.detect_user_cues.return_value = "uncertain"
        mock_persona.paraphrase_user_input.return_value = "So you're thinking working parents, but maybe unsure? Let's explore that."
        
        mock_session_state[f"vp_intro_{IDEATION_STEPS[1]}"] = True

        response = workflow.process_user_input(user_input)

        mock_update_scratchpad.assert_called_once_with(user_input, initial_scratchpad_as_called)
        mock_persona.detect_user_cues.assert_called_once_with(user_input, IDEATION_STEPS[1])
        mock_persona.paraphrase_user_input.assert_called_once_with(
            user_input, "uncertain", IDEATION_STEPS[1], updated_scratchpad_after_input
        )
        
        assert workflow.scratchpad == updated_scratchpad_after_input
        assert workflow.current_ideation_step == IDEATION_STEPS[1] # Stays on current step
        # The mocked paraphrase_user_input does not end with '?', so reflection prompt is added.
        expected_response = "So you're thinking working parents, but maybe unsure? Let's explore that. What are your thoughts?"
        assert response == expected_response
        assert mock_session_state["scratchpad"] == updated_scratchpad_after_input

    def test_ideation_all_fields_filled_transition_to_recommendation(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transition from ideation to recommendation when all ideation fields are filled."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[1] # "ideation"
        # Let's assume current step is the last one, "use_case"
        workflow.current_ideation_step = IDEATION_STEPS[-1] # "use_case"

        user_input_for_last_step = "Parents use it to book last-minute care."
        
        # Pre-fill all other scratchpad fields
        filled_scratchpad = {}
        for i, step in enumerate(IDEATION_STEPS[:-1]):
            filled_scratchpad[step] = f"Content for {step}"
        
        # This is the scratchpad *before* the current input for "use_case"
        scratchpad_before_last_input = filled_scratchpad.copy()
        scratchpad_before_last_input[IDEATION_STEPS[-1]] = "" # "use_case" is empty
        scratchpad_before_last_input["research_requests"] = []
        workflow.scratchpad = scratchpad_before_last_input.copy() # Set workflow's scratchpad directly


        # This is the scratchpad *after* the current input for "use_case"
        fully_filled_scratchpad = filled_scratchpad.copy()
        fully_filled_scratchpad[IDEATION_STEPS[-1]] = user_input_for_last_step
        fully_filled_scratchpad["research_requests"] = []
        mock_update_scratchpad.return_value = fully_filled_scratchpad

        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.coach_on_decision.return_value = "That's a clear use case."
        mock_persona.offer_reflective_summary.return_value = "We've defined all parts of your value prop."
        mock_persona.communicate_next_step.return_value = "Now, let's move to recommendations."

        mock_session_state[f"vp_intro_{IDEATION_STEPS[-1]}"] = True

        response = workflow.process_user_input(user_input_for_last_step)

        mock_update_scratchpad.assert_called_once_with(user_input_for_last_step, scratchpad_before_last_input)
        mock_persona.detect_user_cues.assert_called_once_with(user_input_for_last_step, IDEATION_STEPS[-1])
        mock_persona.coach_on_decision.assert_called_once_with(
            IDEATION_STEPS[-1], user_input_for_last_step, fully_filled_scratchpad, "decided"
        )
        mock_persona.offer_reflective_summary.assert_called_once_with(fully_filled_scratchpad)
        mock_persona.communicate_next_step.assert_called_once_with(PHASES[1], PHASES[2], fully_filled_scratchpad)

        assert workflow.current_phase == PHASES[2] # "recommendation"
        assert workflow.current_ideation_step == "" # Cleared after ideation
        assert workflow.scratchpad == fully_filled_scratchpad
        
        expected_response = "We've defined all parts of your value prop. Now, let's move to recommendations. What are your thoughts?"
        assert response == expected_response
        assert mock_session_state["scratchpad"] == fully_filled_scratchpad

    def test_ideation_user_requests_specific_step_jump(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test that user input can jump to a specific ideation step."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[1] # "ideation"
        workflow.current_ideation_step = IDEATION_STEPS[0] # "problem"
        
        user_input = "Actually, I want to talk about the solution."
        
        initial_scratchpad = workflow.scratchpad.copy()
        updated_scratchpad_generic = initial_scratchpad.copy()
        updated_scratchpad_generic["general_notes"] = "User wants to discuss solution." # Example
        mock_update_scratchpad.return_value = updated_scratchpad_generic

        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.coach_on_decision.return_value = "Okay, you want to discuss the solution instead of the problem. Let's do that. What is your proposed solution?"

        mock_session_state[f"vp_intro_{IDEATION_STEPS[0]}"] = True # Intro for "problem" was handled

        response = workflow.process_user_input(user_input)
        
        assert workflow.current_ideation_step == IDEATION_STEPS[2] # "solution"

        mock_update_scratchpad.assert_called_once_with(user_input, initial_scratchpad)
        mock_persona.detect_user_cues.assert_called_once_with(user_input, IDEATION_STEPS[0])
        mock_persona.coach_on_decision.assert_called_once_with(
            IDEATION_STEPS[0], user_input, updated_scratchpad_generic, "decided"
        )
        
        assert response == "Okay, you want to discuss the solution instead of the problem. Let's do that. What is your proposed solution?"
        assert mock_session_state["scratchpad"] == updated_scratchpad_generic
        assert f"vp_intro_{IDEATION_STEPS[2]}" not in mock_session_state

    def test_recommendation_phase_initial_generation(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test the initial generation of recommendations when entering the phase."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        workflow.scratchpad["research_requests"] = [{"step": "problem", "details": "market size"}]
        
        mock_persona.offer_reflective_summary.return_value = "We've covered a lot in ideation."
        mock_persona.present_recommendations_and_ask_next.return_value = "Here are your recommendations. What next?"

        response = workflow.process_user_input("")

        mock_persona.offer_reflective_summary.assert_called_once_with(workflow.scratchpad)
        mock_persona.present_recommendations_and_ask_next.assert_called_once()
        args, kwargs = mock_persona.present_recommendations_and_ask_next.call_args
        assert isinstance(args[0], str)
        assert args[1] == workflow.scratchpad
        
        expected_response = "We've covered a lot in ideation. Now, let's look at some recommendations based on your value proposition. Here are your recommendations. What next?"
        assert response == expected_response
        assert mock_session_state.get("vp_recommendation_fully_generated_once") is True
        mock_update_scratchpad.assert_not_called()

    def test_recommendation_phase_user_wants_to_iterate(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transitioning to iteration phase from recommendation."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        mock_session_state["vp_recommendation_fully_generated_once"] = True
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        user_input = "I want to iterate on this."
        mock_persona.detect_user_cues.return_value = "open"
        mock_persona.communicate_next_step.return_value = "Okay, let's go to the iteration phase."
        mock_persona.get_reflection_prompt.return_value = "How would you like to start iterating?"

        response = workflow.process_user_input(user_input)

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[2])
        mock_persona.communicate_next_step.assert_called_once_with(PHASES[2], PHASES[3], workflow.scratchpad)
        
        assert workflow.current_phase == PHASES[3] # "iteration"
        expected_response = "Okay, let's go to the iteration phase. How would you like to start iterating?"
        assert response == expected_response
        mock_update_scratchpad.assert_not_called()

    def test_recommendation_phase_user_wants_summary(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transitioning to summary phase from recommendation."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        mock_session_state["vp_recommendation_fully_generated_once"] = True
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        user_input = "Looks good, let's get the summary."
        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.communicate_next_step.return_value = "Great! Moving to the summary."
        
        with patch.object(workflow, 'generate_summary', return_value="This is the final summary.") as mock_generate_summary:
            response = workflow.process_user_input(user_input)
            mock_generate_summary.assert_called_once()

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[2])
        mock_persona.communicate_next_step.assert_called_once_with(PHASES[2], PHASES[4], workflow.scratchpad)
        
        assert workflow.current_phase == PHASES[4] # "summary"
        assert workflow.completed is True
        expected_response = "Great! Moving to the summary. This is the final summary."
        assert response == expected_response
        mock_update_scratchpad.assert_not_called()

    def test_recommendation_phase_no_input_after_generation(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test response when no input is given after recommendations were already generated."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        mock_session_state["vp_recommendation_fully_generated_once"] = True
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        mock_persona.prompt_after_recommendations.return_value = "Recommendations shown. What next: iterate or summary?"
        
        response = workflow.process_user_input("")

        mock_persona.prompt_after_recommendations.assert_called_once_with(workflow.scratchpad)
        expected_response = "Recommendations shown. What next: iterate or summary?"
        assert response == expected_response
        mock_update_scratchpad.assert_not_called()

    def test_recommendation_phase_other_input_paraphrased(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test paraphrasing other user input in recommendation phase."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        mock_session_state["vp_recommendation_fully_generated_once"] = True
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        user_input = "These recommendations are interesting."
        mock_persona.detect_user_cues.return_value = "neutral"
        mock_persona.paraphrase_user_input.return_value = "You find the recommendations interesting. What would you like to do?"
        
        response = workflow.process_user_input(user_input)

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[2])
        mock_persona.paraphrase_user_input.assert_called_once_with(
            user_input, "neutral", PHASES[2], workflow.scratchpad
        )
        expected_response = "You find the recommendations interesting. What would you like to do?"
        assert response == expected_response
        mock_update_scratchpad.assert_not_called()

    def test_iteration_phase_initial_intro(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test the introductory message for the iteration phase."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        
        mock_persona.introduce_iteration_phase.return_value = "We're in iteration. Revise, re-run, or summarize?"
        
        response = workflow.process_user_input("")

        mock_persona.introduce_iteration_phase.assert_called_once_with(workflow.scratchpad)
        expected_response = "We're in iteration. Revise, re-run, or summarize?"
        assert response == expected_response
        mock_update_scratchpad.assert_not_called()

    def test_iteration_phase_revise_specific_step(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transitioning back to a specific ideation step for revision."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        
        step_to_revise = IDEATION_STEPS[1] # "target_customer"
        user_input = f"I want to revise {step_to_revise.replace('_', ' ')}."
        
        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.communicate_next_step.return_value = f"Okay, let's revise {step_to_revise}."
        mock_persona.get_reflection_prompt.return_value = "What are your new thoughts?"

        # Set vp_intro for the step to be revised, to check it gets popped
        mock_session_state[f"vp_intro_{step_to_revise}"] = True
        response = workflow.process_user_input(user_input)

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.communicate_next_step.assert_called_once_with(
            PHASES[3], PHASES[1], workflow.scratchpad, specific_step=step_to_revise
        )
        
        assert workflow.current_phase == PHASES[1] # "ideation"
        assert workflow.current_ideation_step == step_to_revise
        expected_response = f"Okay, let's revise {step_to_revise}. What are your new thoughts?"
        assert response == expected_response
        assert f"vp_intro_{step_to_revise}" not in mock_session_state # Check it was popped
        mock_update_scratchpad.assert_not_called()

    def test_iteration_phase_revise_unspecified_step_prompt(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test prompting for which step to revise if not specified."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        
        user_input = "I want to revise something."
        mock_persona.detect_user_cues.return_value = "open"
        mock_persona.ask_which_part_to_revise.return_value = "Sure, which part to revise (e.g., problem, solution)?"

        response = workflow.process_user_input(user_input)
        
        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.ask_which_part_to_revise.assert_called_once_with(workflow.scratchpad)
        assert response == "Sure, which part to revise (e.g., problem, solution)?"
        assert workflow.current_phase == PHASES[3] # Stays in iteration
        mock_update_scratchpad.assert_not_called()

    def test_iteration_phase_rerun_recommendations(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transitioning back to recommendation phase to re-run."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        
        user_input = "Let's re-run the recommendations."
        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.communicate_next_step.return_value = "Okay, re-running recommendations."
        mock_persona.get_reflection_prompt.return_value = "Let's see the new recommendations."

        mock_session_state["vp_recommendation_fully_generated_once"] = True # Was true
        response = workflow.process_user_input(user_input)

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.communicate_next_step.assert_called_once_with(
            PHASES[3], PHASES[2], workflow.scratchpad
        )
        
        assert workflow.current_phase == PHASES[2] # "recommendation"
        assert mock_session_state.get("vp_recommendation_fully_generated_once") is False # Reset for re-generation
        expected_response = "Okay, re-running recommendations. Let's see the new recommendations."
        assert response == expected_response
        mock_update_scratchpad.assert_not_called()

    def test_iteration_phase_proceed_to_summary(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transitioning to summary phase from iteration."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        user_input = "I'm done, let's summarize."
        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.communicate_next_step.return_value = "Alright, moving to summary."
        
        with patch.object(workflow, 'generate_summary', return_value="This is the final summary from iteration.") as mock_generate_summary:
            response = workflow.process_user_input(user_input)
            mock_generate_summary.assert_called_once()

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.communicate_next_step.assert_called_once_with(
            PHASES[3], PHASES[4], workflow.scratchpad
        )
        
        assert workflow.current_phase == PHASES[4] # "summary"
        assert workflow.completed is True
        expected_response = "Alright, moving to summary. This is the final summary from iteration."
        assert response == expected_response
        mock_update_scratchpad.assert_not_called()

    def test_iteration_phase_other_input_updates_scratchpad(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test that other input in iteration updates scratchpad and gets persona feedback."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        initial_scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        workflow.scratchpad = initial_scratchpad.copy()

        user_input = "I have some new thoughts on the main benefit."
        updated_scratchpad_from_input = initial_scratchpad.copy()
        updated_scratchpad_from_input["main_benefit"] = "New thoughts on main benefit"
        updated_scratchpad_from_input["general_iteration_notes"] = user_input # Example of general update
        mock_update_scratchpad.return_value = updated_scratchpad_from_input
        
        mock_persona.detect_user_cues.return_value = "open"
        mock_persona.paraphrase_user_input.return_value = "You have new thoughts on the main benefit."
        mock_persona.ask_iteration_next_action.return_value = "What next in iteration?"

        response = workflow.process_user_input(user_input)

        mock_update_scratchpad.assert_called_once_with(user_input, initial_scratchpad)
        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.paraphrase_user_input.assert_called_once_with(
            user_input, "open", PHASES[3], updated_scratchpad_from_input
        )
        mock_persona.ask_iteration_next_action.assert_called_once_with(updated_scratchpad_from_input)
        
        assert workflow.scratchpad == updated_scratchpad_from_input
        assert workflow.current_phase == PHASES[3] # Stays in iteration
        expected_response = "You have new thoughts on the main benefit. What next in iteration?"
        assert response == expected_response
        assert mock_session_state["scratchpad"] == updated_scratchpad_from_input

    def test_summary_phase_initial_generation(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test initial summary generation upon entering the summary phase."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[4] # "summary"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        
        with patch.object(workflow, 'generate_summary', return_value="This is your final summary.") as mock_generate_summary:
            response = workflow.process_user_input("")
            mock_generate_summary.assert_called_once()

        assert response == "This is your final summary."
        assert workflow.completed is True
        assert mock_session_state.get("vp_summary_generated_once") is True
        mock_update_scratchpad.assert_not_called()

    def test_summary_phase_user_requests_summary_again(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test user explicitly requesting summary again after it's generated."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[4] # "summary"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        mock_session_state["vp_summary_generated_once"] = True
        
        generated_summary_text = "This is your final summary, requested again."
        with patch.object(workflow, 'generate_summary', return_value=generated_summary_text) as mock_generate_summary:
            mock_session_state["vp_summary_generated_once"] = True # Ensure it's set within this context too
            response = workflow.process_user_input("Can I see the summary again?")
            mock_generate_summary.assert_called_once()

        assert response == generated_summary_text
        assert workflow.completed is True
        mock_update_scratchpad.assert_not_called()

    def test_summary_phase_no_input_after_generation_presents_existing(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test presenting existing summary if no specific input after generation."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[4] # "summary"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        mock_session_state["vp_summary_generated_once"] = True
        
        existing_summary_text = "This is the previously generated summary."
        with patch.object(workflow, 'generate_summary', return_value=existing_summary_text) as mock_generate_summary:
            mock_persona.present_existing_summary.return_value = f"Here is the summary again: {existing_summary_text}"
            mock_session_state["vp_summary_generated_once"] = True # Ensure it's set
            response = workflow.process_user_input("")

            mock_generate_summary.assert_called_once()
            mock_persona.present_existing_summary.assert_called_once_with(existing_summary_text, workflow.scratchpad)

        assert response == f"Here is the summary again: {existing_summary_text}"
        assert workflow.completed is True
        mock_update_scratchpad.assert_not_called()

    def test_phase_transition_validation_non_sequential_fail(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test that a non-sequential phase transition (not allowed) raises ValueError."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[0] # "intake"
        with pytest.raises(ValueError) as excinfo:
            workflow._transition_phase(PHASES[2])
        assert "Invalid phase transition" in str(excinfo.value)

    def test_phase_transition_validation_iteration_cycle_allowed(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test that cycling between iteration and recommendation is allowed."""
        workflow, mock_persona, mock_session_state = workflow_components
        # Iteration to Recommendation
        workflow.current_phase = PHASES[3] # "iteration"
        try:
            workflow._transition_phase(PHASES[2]) # "recommendation"
        except ValueError:
            pytest.fail("Transition from iteration to recommendation should be allowed.")
        assert workflow.current_phase == PHASES[2]

        # Recommendation to Iteration
        workflow.current_phase = PHASES[2] # "recommendation"
        try:
            workflow._transition_phase(PHASES[3]) # "iteration"
        except ValueError:
            pytest.fail("Transition from recommendation to iteration should be allowed.")
        assert workflow.current_phase == PHASES[3]

    def test_is_complete_method(self, mock_st_write, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test the is_complete method."""
        workflow, mock_persona, mock_session_state = workflow_components
        assert not workflow.is_complete()

        workflow.current_phase = PHASES[4] # "summary"
        with patch.object(workflow, 'scratchpad_is_filled_for_summary', return_value=True):
            assert workflow.is_complete()

        workflow.completed = True
        assert workflow.is_complete()