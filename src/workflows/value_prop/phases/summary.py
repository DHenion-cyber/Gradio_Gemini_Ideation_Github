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

    def handle_response(self, user_input: str) -> dict:
        """
        Processes user's response after showing the summary.
        User can ask to repeat or finish.
        """
        self.debug_log(step="handle_response_start", user_input=user_input)
        txt_lower = user_input.lower().strip()
        reply_text = ""
        next_phase_name = None # Stays in summary unless "done"

        if "repeat" in txt_lower:
            summary_text = st.session_state.scratchpad.get("final_summary", "No summary available to repeat.")
            reply_text = f"Certainly, here is the summary again:\n{summary_text}\n\nType 'done' if you are finished."
            self.debug_log(step="handle_response_repeat_summary")
        elif "done" in txt_lower or self.classify_intent(user_input) == "affirm":
            self.mark_complete() # Mark this phase (and implicitly workflow) as complete
            reply_text = self.coach_persona.get_positive_affirmation_response(user_input, phase_name=self.phase_name) + \
                         " All done with the Value Proposition workflow! Good luck."
            # No next_phase means workflow ends. This will be handled by the main app loop.
            self.debug_log(step="handle_response_done")
        else:
            summary_text = st.session_state.scratchpad.get("final_summary", "")
            reply_text = self.coach_persona.get_clarification_prompt(user_input, phase_name=self.phase_name) + \
                         f"\n\nSummary was:\n{summary_text}\n\nPlease type 'repeat' or 'done'."
            self.debug_log(step="handle_response_unclear")

        return {"next_phase": next_phase_name, "reply": reply_text}