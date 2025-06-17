import pytest
from unittest.mock import MagicMock, patch

from src.personas.coach import CoachPersona
from src.workflows.value_prop import ValuePropWorkflow, IdeationState # Corrected import

SKIP_REASON = "obsolete after state-machine refactor"
SKIP_PHASE_REASON = "obsolete after state-machine; will be rewritten"
SKIP_REFRACTOR_REASON = (
    "Obsolete after state-machine refactor; will be rewritten once "
    "Recommendation/Iteration/Summary phases match new architecture."
)

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
class TestValuePropositionWorkflow:

    def test_recommendation_flow(self, mock_update_scratchpad, workflow_components): # Added mock_update_scratchpad
        """
        Tests the recommendation flow:
        - Pre-fills scratchpad so ideation is done.
        - Forces workflow.state = workflow.states["recommendation"].
        - Calls workflow.state.enter(workflow) and asserts "top recommendations".
        - Calls workflow.state.handle("iterate", workflow) and asserts
          workflow.state.name == "revise".
        """
        workflow, mock_persona, mock_session_state = workflow_components

        # Pre-fill scratchpad so ideation is considered done
        for step in workflow.IDEATION_STEPS:
            workflow.scratchpad[step] = f"Content for {step}"
            workflow.states[step].completed = True # Mark individual ideation states as completed

        # Force workflow to recommendation state
        assert "recommendation" in workflow.states, "RecommendationState not found in workflow states"
        workflow.state = workflow.states["recommendation"]
        workflow.current_phase = "recommendation" # Also set the phase

        # Call workflow.state.enter(workflow) and assert "top recommendations"
        enter_messages = workflow.state.enter(workflow)
        assert isinstance(enter_messages, list)
        assert len(enter_messages) > 0
        assert "top recommendations" in enter_messages[0].lower()
        assert workflow.cached_recommendations is not None # Check that recommendations were cached

        # Call workflow.state.handle("iterate", workflow)
        handle_messages = workflow.state.handle("iterate", workflow)
        assert isinstance(handle_messages, list)
        assert "moving to the iteration phase" in handle_messages[0].lower()
        
        # Assert workflow.state.name == "revise" (since workflow.states["iteration"] is ReviseState)
        assert workflow.state is not None, "Workflow state became None after handle"
        assert workflow.state.name == "revise", \
            f"Workflow state name is {workflow.state.name}, expected 'revise'"


    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_initialization(self, workflow_components):
        """Test that the workflow initializes correctly."""
        workflow, mock_persona, mock_session_state = workflow_components
        assert workflow is not None
        assert workflow.persona == mock_persona
        assert workflow.current_phase == PHASES[0]  # "intake"
        expected_first = "use_case"
        assert workflow.state.name == expected_first
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

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_initial_greeting_in_intake_phase(self, workflow_components): # Corrected mock name
        """Test the initial greeting when no user input is provided in the intake phase."""
        workflow, mock_persona, mock_session_state = workflow_components
        msgs = workflow.process_user_input("")
        
        mock_persona.greet_and_explain_value_prop_process.assert_called_once()
        expected_response = "Hello! Let's start with your value proposition. What problem are you solving?"
        assert msgs == [expected_response]
        assert workflow.current_phase == PHASES[0] # Still "intake"

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_intake_to_ideation_transition_on_first_input(self, workflow_components): # Corrected mock name
        """Test transition from intake to ideation upon receiving the first user input."""
        workflow, mock_persona, mock_session_state = workflow_components
        
        # Mock update_scratchpad to return an updated scratchpad
        initial_scratchpad = workflow.scratchpad.copy() # Use workflow.scratchpad
        updated_scratchpad_after_input = initial_scratchpad.copy()
        updated_scratchpad_after_input["problem"] = "Initial user idea" # Simulate scratchpad update
        # mock_update_scratchpad.return_value = updated_scratchpad_after_input # This line would need mock_update_scratchpad if test was active

        user_input = "I have an idea for a new app."

        msgs = workflow.process_user_input(user_input)

        # mock_update_scratchpad.assert_called_once_with(user_input, initial_scratchpad) # This line would need mock_update_scratchpad if test was active
        mock_persona.active_listening.assert_called_once_with(user_input)
        mock_persona.get_intake_to_ideation_transition_message.assert_called_once()
        
        # After transition, current_phase is "ideation", current_ideation_step is "problem"
        mock_persona.get_step_intro_message.assert_called_once_with(IDEATION_STEPS[0], updated_scratchpad_after_input)

        assert workflow.current_phase == PHASES[1]  # "ideation"
        assert workflow.scratchpad == updated_scratchpad_after_input # workflow.scratchpad is updated
        
        # preliminary_message = "Okay, I understand. Great start! Now let's move to ideation."
        # core_response = "Let's talk about the problem."
        # combined = "Okay, I understand. Great start! Now let's move to ideation. Let's talk about the problem."
        # Since this doesn't end with "?", reflection prompt " What are your thoughts?" is added by the final block in process_user_input.
        expected_response = "Okay, I understand. Great start! Now let's move to ideation. Let's talk about the problem. What are your thoughts?"
        assert msgs == [expected_response]
        assert mock_session_state["scratchpad"] == updated_scratchpad_after_input
        assert mock_session_state.get(f"vp_intro_{IDEATION_STEPS[0]}") is True

    @pytest.mark.parametrize(
        "intro_message, expected_response_text",
        [
            ("Let's define the problem. What is it?", "Let's define the problem. What is it?"), # Ends with ?
            ("Let's define the problem. It is important.", "Let's define the problem. It is important."), # Ends with .
            ("Let's define the problem. This is key!", "Let's define the problem. This is key!"), # Ends with !
            ("Let's define the problem, it is complex,", "Let's define the problem, it is complex,"), # Ends with ,
            ("Let's define the problem for our app", "Let's define the problem for our app What are your thoughts?") # No specific end punctuation
        ]
    )
    @pytest.mark.skip(reason=SKIP_REASON)
    def test_ideation_step_intro_if_no_input_punctuation_handling(
        self, workflow_components, intro_message, expected_response_text
    ):
        """Test intro for ideation step with various ending punctuations for the intro message."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[1]  # "ideation"
        workflow.current_ideation_step = IDEATION_STEPS[0]  # "problem"
        
        # Ensure get_reflection_prompt is consistently mocked for the last case
        mock_persona.get_reflection_prompt.return_value = "What are your thoughts?"
        mock_persona.get_step_intro_message.return_value = intro_message
        
        msgs = workflow.process_user_input("")

        mock_persona.get_step_intro_message.assert_called_once_with(IDEATION_STEPS[0], workflow.scratchpad)
        assert msgs == [expected_response_text]
        assert mock_session_state.get(f"vp_intro_{IDEATION_STEPS[0]}") is True
        # mock_update_scratchpad.assert_not_called()  # This line would need mock_update_scratchpad if test was active

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_ideation_process_input_and_suggest_next_step_decided_cue(self, workflow_components): # Corrected mock name
        """Test processing user input in ideation with a 'decided' cue and suggesting the next step."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[1] # "ideation"
        workflow.current_ideation_step = IDEATION_STEPS[0] # "problem"
        
        user_input = "The problem is lack of affordable childcare."
        initial_scratchpad = workflow.scratchpad.copy()
        updated_scratchpad_after_input = initial_scratchpad.copy()
        updated_scratchpad_after_input[IDEATION_STEPS[0]] = user_input # "problem"
        # mock_update_scratchpad.return_value removed

        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.coach_on_decision.return_value = f"That's a clear problem: {user_input}. What's the target customer?"
        
        # Simulate session state for intro being handled
        mock_session_state[f"vp_intro_{IDEATION_STEPS[0]}"] = True

        msgs = workflow.process_user_input(user_input)
        assert "problem" in workflow.scratchpad and workflow.scratchpad["problem"]

        # mock_update_scratchpad.assert_called_once_with removed
        mock_persona.detect_user_cues.assert_called_once_with(user_input, IDEATION_STEPS[0])
        mock_persona.coach_on_decision.assert_called_once_with(
            IDEATION_STEPS[0], user_input, updated_scratchpad_after_input, "decided"
        )
        
        assert workflow.scratchpad == updated_scratchpad_after_input
        assert workflow.state.name == IDEATION_STEPS[1] # "target_customer"
        assert msgs == [f"That's a clear problem: {user_input}. What's the target customer?"]
        assert mock_session_state["scratchpad"] == updated_scratchpad_after_input
        assert mock_session_state.get("vp_ideation_started") is True

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_ideation_process_input_paraphrase_uncertain_cue(self, workflow_components): # Corrected mock name
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
        # mock_update_scratchpad.return_value removed

        mock_persona.detect_user_cues.return_value = "uncertain"
        mock_persona.paraphrase_user_input.return_value = "So you're thinking working parents, but maybe unsure? Let's explore that."
        
        mock_session_state[f"vp_intro_{IDEATION_STEPS[1]}"] = True

        msgs = workflow.process_user_input(user_input)
        assert "target_customer" in workflow.scratchpad and workflow.scratchpad["target_customer"]

        # mock_update_scratchpad.assert_called_once_with removed
        mock_persona.detect_user_cues.assert_called_once_with(user_input, IDEATION_STEPS[1])
        mock_persona.paraphrase_user_input.assert_called_once_with(
            user_input, "uncertain", IDEATION_STEPS[1], updated_scratchpad_after_input
        )
        
        assert workflow.scratchpad == updated_scratchpad_after_input
        assert workflow.state.name == IDEATION_STEPS[1] # Stays on current step
        # The mocked paraphrase_user_input does not end with '?', so reflection prompt is added.
        expected_response = "So you're thinking working parents, but maybe unsure? Let's explore that. What are your thoughts?"
        assert msgs == [expected_response]
        assert mock_session_state["scratchpad"] == updated_scratchpad_after_input

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_ideation_all_fields_filled_transition_to_recommendation(self, workflow_components): # Corrected mock name
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
        # mock_update_scratchpad.return_value removed

        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.coach_on_decision.return_value = "That's a clear use case."
        mock_persona.offer_reflective_summary.return_value = "We've defined all parts of your value prop."
        mock_persona.communicate_next_step.return_value = "Now, let's move to recommendations."

        mock_session_state[f"vp_intro_{IDEATION_STEPS[-1]}"] = True

        msgs = workflow.process_user_input(user_input_for_last_step)
        assert "use_case" in workflow.scratchpad and workflow.scratchpad["use_case"]

        # mock_update_scratchpad.assert_called_once_with removed
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
        assert msgs == [expected_response]
        assert mock_session_state["scratchpad"] == fully_filled_scratchpad

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_ideation_user_requests_specific_step_jump(self, workflow_components): # Corrected mock name
        """Test that user input can jump to a specific ideation step."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[1] # "ideation"
        workflow.current_ideation_step = IDEATION_STEPS[0] # "problem"
        
        user_input = "Actually, I want to talk about the solution."
        
        initial_scratchpad = workflow.scratchpad.copy()
        updated_scratchpad_generic = initial_scratchpad.copy()
        updated_scratchpad_generic["general_notes"] = "User wants to discuss solution." # Example
        # mock_update_scratchpad.return_value = updated_scratchpad_generic # This line would need mock_update_scratchpad if test was active

        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.coach_on_decision.return_value = "Okay, you want to discuss the solution instead of the problem. Let's do that. What is your proposed solution?"

        mock_session_state[f"vp_intro_{IDEATION_STEPS[0]}"] = True # Intro for "problem" was handled

        msgs = workflow.process_user_input(user_input)
        
        assert workflow.state.name == IDEATION_STEPS[2] # "solution"

        # mock_update_scratchpad.assert_called_once_with(user_input, initial_scratchpad) # This line would need mock_update_scratchpad if test was active
        mock_persona.detect_user_cues.assert_called_once_with(user_input, IDEATION_STEPS[0])
        mock_persona.coach_on_decision.assert_called_once_with(
            IDEATION_STEPS[0], user_input, updated_scratchpad_generic, "decided"
        )
        
        assert msgs == ["Okay, you want to discuss the solution instead of the problem. Let's do that. What is your proposed solution?"]
        assert mock_session_state["scratchpad"] == updated_scratchpad_generic
        assert f"vp_intro_{IDEATION_STEPS[2]}" not in mock_session_state

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_recommendation_phase_initial_generation(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test the initial generation of recommendations when entering the phase."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        workflow.scratchpad["research_requests"] = [{"step": "problem", "details": "market size"}]
        
        mock_persona.offer_reflective_summary.return_value = "We've covered a lot in ideation."
        mock_persona.present_recommendations_and_ask_next.return_value = "Here are your recommendations. What next?"

        msgs = workflow.process_user_input("")

        mock_persona.offer_reflective_summary.assert_called_once_with(workflow.scratchpad)
        mock_persona.present_recommendations_and_ask_next.assert_called_once()
        args, kwargs = mock_persona.present_recommendations_and_ask_next.call_args
        assert isinstance(args[0], str)
        assert args[1] == workflow.scratchpad
        
        expected_response = "We've covered a lot in ideation. Now, let's look at some recommendations based on your value proposition. Here are your recommendations. What next?"
        assert msgs == [expected_response]
        assert mock_session_state.get("vp_recommendation_fully_generated_once") is True
        mock_update_scratchpad.assert_not_called()

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_recommendation_phase_user_wants_to_iterate(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transitioning to iteration phase from recommendation."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        mock_session_state["vp_recommendation_fully_generated_once"] = True
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        user_input = "I want to iterate on this."
        mock_persona.detect_user_cues.return_value = "open"
        mock_persona.communicate_next_step.return_value = "Okay, let's go to the iteration phase."
        mock_persona.get_reflection_prompt.return_value = "How would you like to start iterating?"

        msgs = workflow.process_user_input(user_input)

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[2])
        mock_persona.communicate_next_step.assert_called_once_with(PHASES[2], PHASES[3], workflow.scratchpad)
        
        assert workflow.current_phase == PHASES[3] # "iteration"
        # expected_response = "Okay, let's go to the iteration phase. How would you like to start iterating?"
        assert any("iteration phase" in m for m in msgs)
        mock_update_scratchpad.assert_not_called()

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_recommendation_phase_user_wants_summary(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transitioning to summary phase from recommendation."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        mock_session_state["vp_recommendation_fully_generated_once"] = True
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        user_input = "Looks good, let's get the summary."
        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.communicate_next_step.return_value = "Great! Moving to the summary."
        
        with patch.object(workflow, 'generate_summary', return_value="This is the final summary.") as mock_generate_summary:
            msgs = workflow.process_user_input(user_input)
            mock_generate_summary.assert_called_once()

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[2])
        mock_persona.communicate_next_step.assert_called_once_with(PHASES[2], PHASES[4], workflow.scratchpad)
        
        assert workflow.current_phase == PHASES[4] # "summary"
        assert workflow.completed is True
        expected_response = "Great! Moving to the summary. This is the final summary."
        assert msgs == [expected_response]
        mock_update_scratchpad.assert_not_called()

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_recommendation_phase_no_input_after_generation(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test response when no input is given after recommendations were already generated."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        mock_session_state["vp_recommendation_fully_generated_once"] = True
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        mock_persona.prompt_after_recommendations.return_value = "Recommendations shown. What next: iterate or summary?"
        
        msgs = workflow.process_user_input("")

        mock_persona.prompt_after_recommendations.assert_called_once_with(workflow.scratchpad)
        expected_response = "Recommendations shown. What next: iterate or summary?"
        assert msgs == [expected_response]
        mock_update_scratchpad.assert_not_called()

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_recommendation_phase_other_input_paraphrased(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test paraphrasing other user input in recommendation phase."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[2] # "recommendation"
        mock_session_state["vp_recommendation_fully_generated_once"] = True
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        user_input = "These recommendations are interesting."
        mock_persona.detect_user_cues.return_value = "neutral"
        mock_persona.paraphrase_user_input.return_value = "You find the recommendations interesting. What would you like to do?"
        
        msgs = workflow.process_user_input(user_input)

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[2])
        mock_persona.paraphrase_user_input.assert_called_once_with(
            user_input, "neutral", PHASES[2], workflow.scratchpad
        )
        expected_response = "You find the recommendations interesting. What would you like to do?"
        assert msgs == [expected_response]
        mock_update_scratchpad.assert_not_called()

    # @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON) # Un-skipping
    def test_iteration_initial_intro(self, mock_update_scratchpad, workflow_components):
        """Test the introductory message for the iteration phase (ReviseState)."""
        workflow, mock_persona, mock_session_state = workflow_components

        # Simulate transition to iteration phase, which should set state to ReviseState
        workflow.current_phase = "recommendation" # Start from recommendation
        for step in workflow.IDEATION_STEPS: # Ensure ideation is complete
            workflow.scratchpad[step] = f"Content for {step}"
            workflow.states[step].completed = True
        
        workflow.state = workflow.states["recommendation"] # Set current state to recommendation
        
        # User input "iterate" from recommendation state should transition to iteration (ReviseState)
        # The RecommendationState.handle method sets workflow.state = workflow.states["iteration"]
        # which is an instance of ReviseState.
        # Then, process_user_input for the new phase/state should call its enter() method.
        
        # To directly test ReviseState.enter(), we can set the state and call enter.
        # However, the prompt implies testing the flow.
        # Let's simulate the transition from RecommendationState.handle("iterate", workflow)
        
        # Manually set to recommendation state first
        recommendation_state = workflow.states["recommendation"]
        recommendation_state.handle("iterate", workflow) # This should change workflow.state to ReviseState

        assert workflow.state.name == "revise", f"Expected state 'revise', got '{workflow.state.name}'"
        
        # Now, the ReviseState's enter method should be called by the workflow logic
        # if we were to call process_user_input with an empty string in this new state.
        # For a direct test of the enter message:
        enter_messages = workflow.state.enter(workflow)
        
        assert isinstance(enter_messages, list)
        assert len(enter_messages) == 1
        expected_message_part = "Which part to revise"
        assert expected_message_part.lower() in enter_messages[0].lower()
        assert enter_messages[0].endswith("(e.g. problem, solution, differentiator)?")
        mock_update_scratchpad.assert_not_called()

    # @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON) # Un-skipping
    def test_iteration_revise_flow(self, mock_update_scratchpad, workflow_components):
        """Test the revise flow: update a field and assert scratchpad updated."""
        workflow, mock_persona, mock_session_state = workflow_components

        # Setup: Ensure scratchpad has some initial content and workflow is in ReviseState
        field_to_revise = "problem"
        original_content = "Original problem statement."
        new_content = "Revised problem statement."
        workflow.scratchpad[field_to_revise] = original_content
        for step in workflow.IDEATION_STEPS: # Fill other fields for completeness
            if step != field_to_revise:
                workflow.scratchpad[step] = f"Content for {step}"
        
        # Manually set state to ReviseState (which is workflow.states["iteration"])
        workflow.state = workflow.states["iteration"] # This is ReviseState
        assert workflow.state.name == "revise"

        # 1. User specifies the field to revise
        revise_state = workflow.state
        handle_messages_1 = revise_state.handle(field_to_revise, workflow)
        
        assert isinstance(handle_messages_1, list)
        assert f"let's revise {field_to_revise}" in handle_messages_1[0].lower()
        assert workflow.state.name == "revise_detail", "State should transition to ReviseDetailState"
        assert workflow.state.target == field_to_revise, "Target not set in ReviseDetailState"

        # 2. User provides the new text for the field
        revise_detail_state = workflow.state
        handle_messages_2 = revise_detail_state.handle(new_content, workflow)

        assert isinstance(handle_messages_2, list)
        assert f"{field_to_revise} updated" in handle_messages_2[0].lower()
        assert "'re-run' to regenerate" in handle_messages_2[1].lower()
        
        # Assert scratchpad is updated
        assert workflow.scratchpad[field_to_revise] == new_content
        assert revise_detail_state.completed is True, "ReviseDetailState should be marked as completed"
        
        mock_update_scratchpad.assert_not_called() # update_scratchpad is not used by these states

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_iteration_phase_revise_specific_step(self, mock_update_scratchpad, workflow_components): # Corrected mock name
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
        msgs = workflow.process_user_input(user_input)

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.communicate_next_step.assert_called_once_with(
            PHASES[3], PHASES[1], workflow.scratchpad, specific_step=step_to_revise
        )
        
        assert workflow.current_phase == PHASES[1] # "ideation"
        assert workflow.state.name == step_to_revise
        # expected_response = f"Okay, let's revise {step_to_revise}. What are your new thoughts?"
        assert any("revise" in m and "target_customer" in m for m in msgs)
        assert f"vp_intro_{step_to_revise}" not in mock_session_state # Check it was popped
        mock_update_scratchpad.assert_not_called()

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_iteration_phase_revise_unspecified_step_prompt(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test prompting for which step to revise if not specified."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        
        user_input = "I want to revise something."
        mock_persona.detect_user_cues.return_value = "open"
        mock_persona.ask_which_part_to_revise.return_value = "Sure, which part to revise (e.g., problem, solution)?"

        msgs = workflow.process_user_input(user_input)
        
        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.ask_which_part_to_revise.assert_called_once_with(workflow.scratchpad)
        assert msgs == ["Sure, which part to revise (e.g., problem, solution)?"]
        assert workflow.current_phase == PHASES[3] # Stays in iteration
        mock_update_scratchpad.assert_not_called()

    # @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON) # Un-skipping
    def test_iteration_rerun_flow(self, mock_update_scratchpad, workflow_components):
        """Test sending 're-run' and assert state becomes 'recommendation'."""
        workflow, mock_persona, mock_session_state = workflow_components

        # Setup: Start in ReviseDetailState (simulating after a revision)
        # or any state from which 're-run' is a valid next logical step.
        # For simplicity, let's assume we are in ReviseDetailState and it has just completed.
        field_revised = "problem"
        workflow.scratchpad[field_revised] = "Revised problem statement."
        
        # Manually set state to ReviseDetailState and mark as completed
        # This state doesn't have an explicit 're-run' handling,
        # The user types 're-run' which is then processed by the main workflow loop.
        # The RerunState is entered if the user input is 're-run' *after* a ReviseDetailState.
        # For this test, we'll directly set the state to RerunState and call its enter method.

        # To test the RerunState directly:
        rerun_state = workflow.states["rerun"]
        assert rerun_state.name == "rerun"
        
        # Call enter on RerunState
        enter_messages = rerun_state.enter(workflow)
        
        assert isinstance(enter_messages, list)
        assert "re-running recommendations" in enter_messages[0].lower()
        
        # Assert workflow state transitions to recommendation
        assert workflow.state is not None, "Workflow state became None after RerunState.enter"
        assert workflow.state.name == "recommendation", \
            f"Workflow state name is {workflow.state.name}, expected 'recommendation'"
        
        mock_update_scratchpad.assert_not_called()

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_iteration_phase_proceed_to_summary(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test transitioning to summary phase from iteration."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}

        user_input = "I'm done, let's summarize."
        mock_persona.detect_user_cues.return_value = "decided"
        mock_persona.communicate_next_step.return_value = "Alright, moving to summary."
        
        with patch.object(workflow, 'generate_summary', return_value="This is the final summary.") as mock_generate_summary:
            msgs = workflow.process_user_input(user_input)
            mock_generate_summary.assert_called_once()

        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.communicate_next_step.assert_called_once_with(PHASES[3], PHASES[4], workflow.scratchpad)
        
        assert workflow.current_phase == PHASES[4] # "summary"
        assert workflow.completed is True
        expected_response = "Alright, moving to summary. This is the final summary."
        assert msgs == [expected_response]
        mock_update_scratchpad.assert_not_called()

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_iteration_phase_other_input_updates_scratchpad(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """
        Test that other, non-keyword input during iteration phase still results in
        the scratchpad being updated (e.g., with general notes or if the input
        was relevant to the current implicit context of iteration).
        """
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[3] # "iteration"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        
        user_input = "I'm thinking about the colors for the logo."
        
        # This is the scratchpad that update_scratchpad will be called with
        initial_scratchpad_as_called = workflow.scratchpad.copy()
        
        # This is what update_scratchpad is expected to return
        updated_scratchpad_after_input = initial_scratchpad_as_called.copy()
        # Simulate that update_scratchpad adds a general note or similar
        updated_scratchpad_after_input["general_notes"] = "User is thinking about logo colors."
        mock_update_scratchpad.return_value = updated_scratchpad_after_input

        mock_persona.detect_user_cues.return_value = "neutral" # Or any cue that doesn't lead to immediate phase change
        mock_persona.ask_iteration_next_action.return_value = "Okay, noted. What would you like to do next: revise, re-run recommendations, or summarize?"
        
        msgs = workflow.process_user_input(user_input)

        mock_update_scratchpad.assert_called_once_with(user_input, initial_scratchpad_as_called)
        mock_persona.detect_user_cues.assert_called_once_with(user_input, PHASES[3])
        mock_persona.ask_iteration_next_action.assert_called_once_with(updated_scratchpad_after_input)
        
        assert workflow.scratchpad == updated_scratchpad_after_input
        assert any("or summarize?" in m for m in msgs)
        assert workflow.current_phase == PHASES[3] # Stays in iteration

    # @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON) # Un-skipping and renaming
    def test_summary_initial(self, mock_update_scratchpad, workflow_components):
        """Test the initial generation of summary when entering SummaryState."""
        workflow, mock_persona, mock_session_state = workflow_components

        key_problem_text = "Unique problem XYZ for testing summary"
        workflow.scratchpad["problem"] = key_problem_text
        workflow.scratchpad["solution"] = "A brilliant solution for XYZ"
        # Fill other essential fields for a more complete summary
        for step in workflow.IDEATION_STEPS:
            if not workflow.scratchpad.get(step): # Ensure all ideation steps have some content
                workflow.scratchpad[step] = f"Details for {step}"
        
        # Configure persona's summary generation to include key text
        # The SummaryState.enter() calls workflow.generate_summary() which uses the persona.
        expected_summary_fragment = f"summary about the {key_problem_text}"
        mock_persona.generate_value_prop_summary.return_value = f"This is a detailed {expected_summary_fragment} and other vital information."

        # Manually set workflow to SummaryState
        workflow.current_phase = "summary" # Set phase
        summary_state = workflow.states.get("summary")
        assert summary_state is not None, "SummaryState not found in workflow states"
        workflow.state = summary_state # Set state object
        
        # Call SummaryState.enter()
        enter_messages = workflow.state.enter(workflow)

        # Assertions
        # SummaryState.enter calls workflow.generate_summary(), which should use the persona's method
        mock_persona.generate_value_prop_summary.assert_called_once_with(workflow.scratchpad, workflow.cached_recommendations)
        
        assert workflow.final_summary is not None
        assert key_problem_text in workflow.final_summary, "Key scratchpad text not in final_summary"
        assert expected_summary_fragment.lower() in workflow.final_summary.lower()

        assert isinstance(enter_messages, list)
        assert len(enter_messages) == 2
        assert f"Here is your final summary:\n{workflow.final_summary}" == enter_messages[0]
        assert "Let me know if you'd like it repeated." == enter_messages[1]
        
        assert not summary_state.completed, "SummaryState should not be completed just by entering"
        assert not workflow.completed, "Workflow should not be completed just by entering SummaryState"

    # @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON) # Un-skipping and renaming
    def test_summary_repeat(self, mock_update_scratchpad, workflow_components):
        """Test repeating the summary in SummaryState."""
        workflow, mock_persona, mock_session_state = workflow_components

        initial_summary_text = "This is the initial summary for repeating."
        workflow.scratchpad["problem"] = "Repeatable problem"
        mock_persona.generate_value_prop_summary.return_value = initial_summary_text

        # Manually set workflow to SummaryState and call enter to set final_summary
        workflow.current_phase = "summary"
        summary_state = workflow.states.get("summary")
        assert summary_state is not None, "SummaryState not found"
        workflow.state = summary_state
        
        # Call enter to populate workflow.final_summary
        workflow.state.enter(workflow)
        mock_persona.generate_value_prop_summary.assert_called_once() # Called during enter
        assert workflow.final_summary == initial_summary_text

        # Call handle with "repeat"
        handle_messages = workflow.state.handle("repeat please", workflow)

        # Assertions
        assert isinstance(handle_messages, list)
        assert len(handle_messages) == 1
        assert handle_messages[0] == initial_summary_text, "Repeated summary does not match initial summary"
        
        # Ensure generate_summary was not called again during handle("repeat")
        mock_persona.generate_value_prop_summary.assert_called_once()
        
        assert not summary_state.completed, "SummaryState should not be completed after 'repeat'"
        assert not workflow.completed, "Workflow should not be completed after 'repeat' in SummaryState"

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_summary_phase_no_input_after_generation_presents_existing(self, mock_update_scratchpad, workflow_components): # Corrected mock name
        """Test presenting existing summary if no specific input after generation."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[4] # "summary"
        workflow.scratchpad = {step: f"Content for {step}" for step in IDEATION_STEPS}
        mock_session_state["vp_summary_generated_once"] = True
        
        existing_summary_text = "This is the previously generated summary."
        with patch.object(workflow, 'generate_summary', return_value=existing_summary_text) as mock_generate_summary:
            mock_persona.present_existing_summary.return_value = f"Here is the summary again: {existing_summary_text}"
            mock_session_state["vp_summary_generated_once"] = True # Ensure it's set
            msgs = workflow.process_user_input("")

            mock_generate_summary.assert_called_once() # Should still call generate_summary to get the "existing" one
            mock_persona.present_existing_summary.assert_called_once_with(existing_summary_text, workflow.scratchpad)

        assert msgs == [f"Here is the summary again: {existing_summary_text}"]
        assert workflow.completed is True
        mock_update_scratchpad.assert_not_called()

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_phase_transition_validation_non_sequential_fail(self, workflow_components): # Corrected mock name
        """Test that a non-sequential phase transition (not allowed) raises ValueError."""
        workflow, mock_persona, mock_session_state = workflow_components
        workflow.current_phase = PHASES[0] # "intake"
        with pytest.raises(ValueError) as excinfo:
            workflow._transition_phase(PHASES[2])
        assert "Invalid phase transition" in str(excinfo.value)

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_phase_transition_validation_iteration_cycle_allowed(self, workflow_components): # Corrected mock name
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

    @pytest.mark.skip(reason=SKIP_REFRACTOR_REASON)
    def test_is_complete_method(self, workflow_components): # Corrected mock name
        """Test the is_complete method."""
        workflow, mock_persona, mock_session_state = workflow_components
        
        for st in workflow.states.values():
            st.completed = True
        
        assert workflow.is_complete()