import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase # For type hinting

class UseCasePhase(PhaseEngineBase):
    phase_name = "use_case"

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str = "value_prop"):
        super().__init__(coach_persona, workflow_name)

    def handle_response(self, user_input: str) -> dict:
        """
        Processes the user's response for the use case phase.
        """
        self.debug_log(step="handle_response_start", user_input=user_input)
        # The original ValuePropWorkflow's UseCaseState asked "Would you like to explore this now? (yes/no)"
        # and only proceeded if not "no". This logic is now partly in the persona's get_step_intro_message.
        # The PhaseEngineBase's classify_intent can be used here.

        intent = self.classify_intent(user_input)
        reply_text = ""
        next_phase_name = None # Stays in this phase by default

        current_scratchpad_value = st.session_state.scratchpad.get(self.phase_name, "")

        if intent == "negative" and current_scratchpad_value:
            # User said "no" to exploring the existing use case.
            # We can ask them to provide a new one or confirm they want to skip (though PRD says no skipping).
            # For now, let's assume "no" means they don't want to change it if it exists, and we move on.
            # Or, if the question was "Would you like to explore this now?", "no" means skip this turn.
            # The original logic was: if user_input.lower() != "no": workflow.scratchpad[self.name] = user_input
            # This implies "no" was a way to *not* update.
            # Let's assume "no" to "explore this now?" means "I don't want to talk about this specific item right now".
            # This is tricky because the PRD says "ALL workflow phases are required".
            # For now, if they say "no" to the intro prompt, we'll ask them to provide input.
            reply_text = self.coach_persona.get_negative_affirmation_response(user_input, phase_name=self.phase_name) + \
                         " Please tell me about the primary use case."
            self.debug_log(step="handle_response_negative_intent_with_existing_value")

        elif user_input.strip() and user_input.lower() != "no": # User provided some input that isn't "no"
            st.session_state.scratchpad[self.phase_name] = user_input.strip()
            self.mark_complete() # Mark as complete as per original logic
            reply_text = self.coach_persona.micro_validate(user_input, phase_name=self.phase_name) + \
                         " Use case updated."
            # Determine next phase from PHASE_ORDER in __init__.py of the workflow
            # This logic will be centralized in the main workflow runner.
            # For now, this phase engine signals completion. The workflow manager/runner decides the next.
            # next_phase_name = "problem" # Hardcoding next for now, will be dynamic
            self.debug_log(step="handle_response_input_provided_and_complete", next_phase_suggestion=next_phase_name)
        else: # "no" to providing new input, or empty input
            # If they say "no" and there's no existing value, or input is empty.
            reply_text = self.coach_persona.get_clarification_prompt(user_input, phase_name=self.phase_name) + \
                         " Please describe the primary use case."
            self.debug_log(step="handle_response_unclear_or_no_new_input")


        return {"next_phase": next_phase_name, "reply": reply_text}