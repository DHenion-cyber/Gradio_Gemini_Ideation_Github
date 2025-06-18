import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase # For type hinting

class ProblemPhase(PhaseEngineBase):
    phase_name = "problem"

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str = "value_prop"):
        super().__init__(coach_persona, workflow_name)

    def handle_response(self, user_input: str) -> dict:
        """
        Processes the user's response for the problem phase.
        """
        self.debug_log(step="handle_response_start", user_input=user_input)
        intent = self.classify_intent(user_input)
        reply_text = ""
        next_phase_name = None

        current_scratchpad_value = st.session_state.scratchpad.get(self.phase_name, "")

        if intent == "negative" and current_scratchpad_value:
            reply_text = self.coach_persona.get_negative_affirmation_response(user_input, phase_name=self.phase_name) + \
                         " Please tell me about the problem you are addressing."
            self.debug_log(step="handle_response_negative_intent_with_existing_value")
        elif user_input.strip() and user_input.lower() != "no":
            st.session_state.scratchpad[self.phase_name] = user_input.strip()
            self.mark_complete()
            reply_text = self.coach_persona.micro_validate(user_input, phase_name=self.phase_name) + \
                         " Problem statement updated."
            # next_phase_name = "target_customer" # To be handled by workflow runner
            self.debug_log(step="handle_response_input_provided_and_complete", next_phase_suggestion=next_phase_name)
        else:
            reply_text = self.coach_persona.get_clarification_prompt(user_input, phase_name=self.phase_name) + \
                         " Please describe the problem your idea solves."
            self.debug_log(step="handle_response_unclear_or_no_new_input")

        return {"next_phase": next_phase_name, "reply": reply_text}