import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase # For type hinting

class MainBenefitPhase(PhaseEngineBase):
    phase_name = "main_benefit"

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str = "value_prop"):
        super().__init__(coach_persona, workflow_name)

    # The handle_response logic is now primarily in PhaseEngineBase.

    def store_input_to_scratchpad(self, user_input: str):
        """Stores the validated user input (main_benefit) to the session scratchpad."""
        self.debug_log(step="store_input_to_scratchpad_main_benefit", user_input_len=len(user_input))
        st.session_state.scratchpad[self.phase_name] = user_input.strip()

    def get_next_phase_after_completion(self) -> str | None:
        """Determines the next phase name after successful completion of the main_benefit phase."""
        self.debug_log(step="get_next_phase_after_completion_main_benefit")
        self.mark_complete()
        return "differentiator"

    def get_next_phase_after_skip(self) -> str | None:
        """Determines the next phase name after skipping the main_benefit phase."""
        self.debug_log(step="get_next_phase_after_skip_main_benefit")
        return "differentiator"