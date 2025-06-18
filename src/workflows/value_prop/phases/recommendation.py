import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase # For type hinting
from src.workflows.value_prop.persona import ValuePropCoachPersona # Specific persona for its methods

class RecommendationPhase(PhaseEngineBase):
    phase_name = "recommendation"

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str = "value_prop"):
        super().__init__(coach_persona, workflow_name)
        # Ensure coach_persona is an instance of ValuePropCoachPersona for specific methods
        if not isinstance(self.coach_persona, ValuePropCoachPersona):
            # This is a fallback or error, ideally the correct persona is injected.
            # For now, we'll assume it is, or methods might fail.
            self.debug_log(step="__init__", warning="Coach persona might not be ValuePropCoachPersona, specific methods may fail.")


    def enter(self) -> str:
        """
        Generates and presents recommendations.
        Overrides base enter to include recommendation generation.
        """
        self.debug_log(step="enter_phase")
        super().enter() # Calls base enter for logging etc. but we'll override the return message.

        if isinstance(self.coach_persona, ValuePropCoachPersona):
            recs_text = self.coach_persona.generate_value_prop_recommendations(st.session_state.scratchpad)
            st.session_state.scratchpad["cached_recommendations"] = recs_text
        else:
            # Fallback if persona is not the expected type
            recs_text = "Could not generate specific recommendations at this time. Generic advice: review your inputs thoroughly."
            st.session_state.scratchpad["cached_recommendations"] = recs_text
            self.debug_log(step="enter_phase_fallback_recs", persona_type=type(self.coach_persona).__name__)

        intro_message = self.coach_persona.get_step_intro_message(phase_name=self.phase_name)
        # The intro message from persona might be generic like "Here are recommendations..."
        # We append the actual recommendations.
        return f"{intro_message}\n\n{recs_text}\n\nWhat would you like to do next? (Type 'iterate' to refine, or 'summary' to wrap up.)"


    # The handle_response logic is now primarily in PhaseEngineBase.

    def store_input_to_scratchpad(self, user_input: str):
        """
        This phase primarily processes commands ('iterate', 'summary') rather than storing free text.
        The user's choice is acted upon by get_next_phase_after_completion.
        """
        self.debug_log(step="store_input_to_scratchpad_recommendation", user_input=user_input, info="Input is command-like, not stored in scratchpad field.")
        # No direct storage into a specific scratchpad field for this phase's input.
        # The input (e.g. "iterate", "summary") drives the next phase decision.
        # We can store the last command if needed for analytics or complex logic.
        st.session_state.scratchpad["last_recommendation_command"] = user_input.strip().lower()


    def get_next_phase_after_completion(self) -> str | None:
        """
        Determines the next phase based on the user's command after seeing recommendations.
        The base class's handle_response would have validated the input.
        """
        # The user_input that led to completion is implicitly "iterate" or "summary"
        # (or something the persona validated as such).
        # We can retrieve the last input if necessary, or rely on intent.
        last_command = st.session_state.scratchpad.get("last_recommendation_command", "")
        
        # A more robust way might be to check an intent set by the base class's micro_validate
        # if we had specific intents for "chose_iterate" vs "chose_summary".
        # For now, simple string check on the stored command.

        if "iterate" in last_command:
            self.debug_log(step="get_next_phase_recommendation_to_iteration")
            self.mark_complete() # User chose to iterate, this phase's interaction is done.
            return "iteration"
        elif "summary" in last_command:
            self.debug_log(step="get_next_phase_recommendation_to_summary")
            self.mark_complete() # User chose summary, this phase's interaction is done.
            return "summary"
        
        # Fallback if the command wasn't clear, though micro_validate should prevent this.
        # If micro_validate allowed an ambiguous input (e.g. "ok") that wasn't "iterate" or "summary"
        # the phase should not complete and should re-prompt.
        # Returning None here means "stay in phase", and since self.mark_complete() wasn't called,
        # the workflow manager won't auto-advance. The persona's clarification prompt will be shown.
        self.debug_log(step="get_next_phase_recommendation_unclear_command_stay", command=last_command)
        return None # Stay in phase to re-prompt if command was not iterate/summary but passed micro_validate.

    def get_next_phase_after_skip(self) -> str | None:
        """
        Determines the next phase if the user skips recommendations.
        Typically, this might lead to summary or allow re-evaluation.
        """
        self.debug_log(step="get_next_phase_after_skip_recommendation")
        # If recommendations are skipped, perhaps proceed to summary.
        return "summary"