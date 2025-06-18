import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase # For type hinting
from src.workflows.value_prop.persona import ValuePropCoachPersona # Specific persona

class SummaryPhase(PhaseEngineBase):
    phase_name = "summary"

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str = "value_prop"):
        super().__init__(coach_persona, workflow_name)
        if not isinstance(self.coach_persona, ValuePropCoachPersona):
            self.debug_log(step="__init__", warning="Coach persona might not be ValuePropCoachPersona for summary generation.")

    def enter(self) -> str:
        """
        Generates and presents the final summary.
        Overrides base enter to include summary generation.
        """
        self.debug_log(step="enter_phase")
        super().enter() # Base class enter for logging etc.

        summary_text = ""
        if isinstance(self.coach_persona, ValuePropCoachPersona):
            summary_text = self.coach_persona.generate_value_prop_summary(st.session_state.scratchpad)
        else:
            summary_text = "Could not generate a detailed summary at this time. Please review your scratchpad."
            self.debug_log(step="enter_phase_fallback_summary", persona_type=type(self.coach_persona).__name__)

        st.session_state.scratchpad["final_summary"] = summary_text
        
        # The persona's get_step_intro_message for "summary" might be a generic intro.
        # We append the actual summary.
        intro_message = self.coach_persona.get_step_intro_message(phase_name=self.phase_name)
        
        # Mark workflow as complete when entering summary phase
        # This might be better handled by the workflow manager after this phase completes.
        # For now, let's assume entering summary means the main data collection is done.
        # self.mark_complete() # This phase completes upon user saying "done" or similar.

        return f"{intro_message}\n\nHere is your final summary:\n{summary_text}\n\nLet me know if you'd like it repeated, or type 'done' to finish."

    # The handle_response logic is now primarily in PhaseEngineBase.

    def store_input_to_scratchpad(self, user_input: str):
        """
        This phase primarily processes commands ('repeat', 'done').
        The user's choice is acted upon by get_next_phase_after_completion.
        """
        self.debug_log(step="store_input_to_scratchpad_summary", user_input=user_input, info="Input is command-like.")
        st.session_state.scratchpad["last_summary_command"] = user_input.strip().lower()

    def get_next_phase_after_completion(self) -> str | None:
        """
        Determines the next step after user responds to the summary.
        'done' completes the workflow (returns None). 'repeat' stays in summary.
        """
        last_command = st.session_state.scratchpad.get("last_summary_command", "")

        if "done" in last_command: # This also covers "affirm" if persona maps it to "done" effectively
            self.debug_log(step="get_next_phase_summary_to_end_workflow")
            self.mark_complete() # User is done, mark phase (and workflow) as complete.
            return None # Signals end of workflow
        elif "repeat" in last_command:
            self.debug_log(step="get_next_phase_summary_repeat")
            # To repeat, we stay in the current phase. The enter() method will be called again.
            # The _is_complete flag for this interaction was set by base.handle_response.
            # The next call to super().enter() will reset it for the "repeated" interaction.
            return self.phase_name # Explicitly stay in 'summary' phase. Or return None if manager handles re-entry.
                                   # Returning self.phase_name is clearer for explicit re-entry.
                                   # However, base class handle_response returns None for next_phase if it's not changing.
                                   # Let's align with that: if we want to stay, next_phase_decision is None.
                                   # The persona's reply should be the repeated summary.
                                   # This logic is tricky: base class sets self.complete=True.
                                   # If we return None, workflow manager might think phase is done and try to move.
                                   # For "repeat", we need to ensure the phase is NOT considered fully complete.
                                   # The base class's mark_complete() was called.
                                   # This needs careful handling in the persona's micro_validate or ack message for "repeat".
                                   # For now, assume "repeat" means the persona handles re-displaying.
                                   # The base class will call mark_complete(). If we return None, it means "stay and re-prompt".
                                   # The enter() method will be called again.
            return None # Stay in summary, enter() will re-display.
        
        # Fallback if command was unclear but somehow validated
        self.debug_log(step="get_next_phase_summary_unclear_command_fallback", command=last_command)
        return None # Stay in summary and re-prompt via enter()

    def get_next_phase_after_skip(self) -> str | None:
        """
        If the user skips the summary phase (e.g., types 'skip' when presented with summary).
        This usually implies they are done with the workflow.
        """
        self.debug_log(step="get_next_phase_after_skip_summary")
        self.mark_complete() # Skipping summary also means workflow is done.
        return None # Signals end of workflow