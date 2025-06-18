import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase
from src.workflows.value_prop import ITERATION_SUB_PHASES, SCRATCHPAD_KEYS

class IterationPhase(PhaseEngineBase):
    phase_name = "iteration"

    # Internal states for the iteration phase
    ITERATION_STATE_CHOOSE_REVISION = "choose_revision"
    ITERATION_STATE_GET_REVISION_DETAIL = "get_revision_detail"
    ITERATION_STATE_AWAIT_COMMAND = "await_command_after_revision" # After detail is provided

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str = "value_prop"):
        super().__init__(coach_persona, workflow_name)
        # Initialize internal state for iteration
        if "iteration_internal_state" not in st.session_state:
            st.session_state.iteration_internal_state = self.ITERATION_STATE_CHOOSE_REVISION
        if "iteration_target_field" not in st.session_state:
            st.session_state.iteration_target_field = None

    def enter(self) -> str:
        """
        Enter the iteration phase. The message depends on the internal state.
        """
        self.debug_log(step="enter_phase", internal_state=st.session_state.iteration_internal_state)
        super().enter() # Base class enter for logging

        st.session_state.iteration_internal_state = self.ITERATION_STATE_CHOOSE_REVISION
        st.session_state.iteration_target_field = None
        return self.coach_persona.get_step_intro_message(phase_name="revise") # "revise" is the initial sub-step

    def handle_response(self, user_input: str) -> dict:
        self.debug_log(step="handle_response_start", user_input=user_input, internal_state=st.session_state.iteration_internal_state)
        reply_text = ""
        next_phase_name = None # Stays in 'iteration' phase unless explicitly changed

        current_internal_state = st.session_state.iteration_internal_state

        if current_internal_state == self.ITERATION_STATE_CHOOSE_REVISION:
            # User is specifying which field to revise
            target_field_input = user_input.strip().lower().replace(" ", "_")
            valid_fields_to_revise = [key for key in SCRATCHPAD_KEYS if key not in ["research_requests", "cached_recommendations", "final_summary"]]

            if target_field_input in valid_fields_to_revise:
                st.session_state.iteration_target_field = target_field_input
                st.session_state.iteration_internal_state = self.ITERATION_STATE_GET_REVISION_DETAIL
                reply_text = self.coach_persona.get_step_intro_message(phase_name="revise_detail", target_to_revise=target_field_input)
                self.debug_log(step="choose_revision_success", target=target_field_input)
            else:
                fields_str = ", ".join([f.replace('_', ' ') for f in valid_fields_to_revise])
                reply_text = self.coach_persona.get_clarification_prompt(user_input, phase_name="revise") + \
                             f" Please choose a valid item to revise from: {fields_str}."
                self.debug_log(step="choose_revision_invalid_field", provided=target_field_input)

        elif current_internal_state == self.ITERATION_STATE_GET_REVISION_DETAIL:
            # User is providing the new text for the chosen field
            target_field = st.session_state.iteration_target_field
            if target_field:
                st.session_state.scratchpad[target_field] = user_input.strip()
                st.session_state.iteration_internal_state = self.ITERATION_STATE_AWAIT_COMMAND
                reply_text = self.coach_persona.micro_validate(user_input, phase_name="revise_detail") + \
                             f" {target_field.replace('_', ' ').capitalize()} updated. " + \
                             "Type 're-run' to regenerate recommendations with this change, or 'summary' to finish."
                self.debug_log(step="get_revision_detail_success", field=target_field, new_value=user_input)
            else: # Should not happen if logic is correct
                reply_text = "An error occurred. Please try choosing an item to revise again."
                st.session_state.iteration_internal_state = self.ITERATION_STATE_CHOOSE_REVISION
                self.debug_log(step="get_revision_detail_error_no_target")


        elif current_internal_state == self.ITERATION_STATE_AWAIT_COMMAND:
            # User has revised a field and is now deciding to re-run or go to summary
            txt_lower = user_input.lower().strip()
            if "summary" in txt_lower:
                self.mark_complete() # Iteration phase is complete
                next_phase_name = "summary"
                reply_text = self.coach_persona.get_positive_affirmation_response(user_input) + " Proceeding to summary."
                self._reset_internal_iteration_state()
                self.debug_log(step="await_command_summary", next_phase=next_phase_name)
            elif "re-run" in txt_lower or "rerun" in txt_lower:
                # Mark complete for this iteration cycle, but the overall "iteration" phase might continue
                # The transition to "recommendation" will be handled by the workflow runner
                self.mark_complete() # Iteration phase itself is considered 'done' for this cycle, leading to re-recommend or summary
                next_phase_name = "recommendation" # Signal to go back to recommendation
                reply_text = self.coach_persona.get_step_intro_message(phase_name="rerun")
                self._reset_internal_iteration_state()
                self.debug_log(step="await_command_rerun", next_phase=next_phase_name)
            else:
                reply_text = self.coach_persona.get_clarification_prompt(user_input) + \
                             "Please type 're-run' to see updated recommendations, or 'summary' to finish."
                self.debug_log(step="await_command_unclear")
        else:
            # Should not happen
            reply_text = "An unexpected error occurred in the iteration phase. Resetting."
            self._reset_internal_iteration_state()
            st.session_state.iteration_internal_state = self.ITERATION_STATE_CHOOSE_REVISION
            self.debug_log(step="unknown_internal_state", state=current_internal_state)


        return {"next_phase": next_phase_name, "reply": reply_text}

    def _reset_internal_iteration_state(self):
        st.session_state.iteration_internal_state = self.ITERATION_STATE_CHOOSE_REVISION
        st.session_state.iteration_target_field = None
        self.debug_log(step="_reset_internal_iteration_state")