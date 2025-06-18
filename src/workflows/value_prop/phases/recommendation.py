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


    def handle_response(self, user_input: str) -> dict:
        """
        Processes user's response after showing recommendations.
        User can choose to iterate or go to summary.
        """
        self.debug_log(step="handle_response_start", user_input=user_input)
        intent = self.classify_intent(user_input) # Basic intent
        txt_lower = user_input.lower().strip()
        reply_text = ""
        next_phase_name = None

        if "iterate" in txt_lower or intent == "ask_suggestion": # Treat "help" or "suggestion" as wanting to iterate for now
            self.mark_complete() # This phase is complete, moving to iteration
            next_phase_name = "iteration"
            reply_text = self.coach_persona.get_positive_affirmation_response(user_input, phase_name=self.phase_name) + \
                         " Moving to the iteration phase."
            self.debug_log(step="handle_response_iterate", next_phase_suggestion=next_phase_name)
        elif "summary" in txt_lower:
            self.mark_complete() # This phase is complete, moving to summary
            next_phase_name = "summary"
            reply_text = self.coach_persona.get_positive_affirmation_response(user_input, phase_name=self.phase_name) + \
                         " Proceeding to summary."
            self.debug_log(step="handle_response_summary", next_phase_suggestion=next_phase_name)
        else:
            # If input is unclear, re-iterate options.
            cached_recs = st.session_state.scratchpad.get("cached_recommendations", "Recommendations were shown.")
            reply_text = self.coach_persona.get_clarification_prompt(user_input, phase_name=self.phase_name) + \
                         f"\n\n{cached_recs}\n\nPlease type 'iterate' to refine your inputs, or 'summary' to proceed to the final summary."
            self.debug_log(step="handle_response_unclear")

        return {"next_phase": next_phase_name, "reply": reply_text}