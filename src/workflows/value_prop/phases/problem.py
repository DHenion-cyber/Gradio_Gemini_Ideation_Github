import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase # For type hinting

class ProblemPhase(PhaseEngineBase):
    phase_name = "problem"

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str = "value_prop"):
        super().__init__(coach_persona, workflow_name)

    # The handle_response logic is now primarily in PhaseEngineBase.
    # Subclasses like this one mainly need to implement the storage and transition logic.

    def store_input_to_scratchpad(self, user_input: str):
        """Stores the validated user input (problem description) to the session scratchpad."""
        self.debug_log(step="store_input_to_scratchpad_problem", user_input_len=len(user_input))
        st.session_state.scratchpad[self.phase_name] = user_input.strip()
        # Potentially log an event here if more detailed tracking per phase is needed beyond base class

    def get_next_phase_after_completion(self) -> str | None:
        """Determines the next phase name after successful completion of the problem phase."""
        self.debug_log(step="get_next_phase_after_completion_problem")
        self.mark_complete() # Mark this single-step phase as complete
        return "target_customer" # Or dynamically determine based on workflow logic if needed

    def get_next_phase_after_skip(self) -> str | None:
        """Determines the next phase name after skipping the problem phase."""
        self.debug_log(step="get_next_phase_after_skip_problem")
        # Skipping problem might still lead to target customer, or a different path.
        # For now, assume linear progression.
        return "target_customer"