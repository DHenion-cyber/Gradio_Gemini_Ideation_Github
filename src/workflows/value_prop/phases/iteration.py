import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase
from src.workflows.value_prop import ITERATION_SUB_PHASES, SCRATCHPAD_KEYS, PHASE_ORDER

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
        self.debug_log(step="enter_phase_iteration", internal_state=st.session_state.get("iteration_internal_state"))
        super().enter() # Resets _is_complete for the current sub-step interaction

        current_internal_state = st.session_state.get("iteration_internal_state", self.ITERATION_STATE_CHOOSE_REVISION)

        if current_internal_state == self.ITERATION_STATE_CHOOSE_REVISION:
            st.session_state.iteration_target_field = None # Ensure target field is reset
            return self.coach_persona.get_step_intro_message(phase_name="revise_choose_field")
        elif current_internal_state == self.ITERATION_STATE_GET_REVISION_DETAIL:
            target_field = st.session_state.get("iteration_target_field")
            if target_field:
                return self.coach_persona.get_step_intro_message(phase_name="revise_provide_detail", target_to_revise=target_field)
            else: # Fallback if target_field was somehow lost
                st.session_state.iteration_internal_state = self.ITERATION_STATE_CHOOSE_REVISION
                return self.coach_persona.get_clarification_prompt(user_input="", phase_name="revise_choose_field", reason="internal_error_no_target")
        elif current_internal_state == self.ITERATION_STATE_AWAIT_COMMAND:
            return self.coach_persona.get_step_intro_message(phase_name="revise_await_command")
        
        # Default fallback, should ideally not be reached
        st.session_state.iteration_internal_state = self.ITERATION_STATE_CHOOSE_REVISION
        return self.coach_persona.get_step_intro_message(phase_name="revise_choose_field")

    def store_input_to_scratchpad(self, user_input: str):
        current_internal_state = st.session_state.get("iteration_internal_state")
        if current_internal_state == self.ITERATION_STATE_GET_REVISION_DETAIL:
            target_field = st.session_state.get("iteration_target_field")
            if target_field:
                st.session_state.scratchpad[target_field] = user_input.strip()
                self.debug_log(step="store_input_revision_detail", field=target_field, input_len=len(user_input))
            else:
                self.debug_log(step="store_input_revision_detail_error", error="No target_field in session")
        # For CHOOSE_REVISION and AWAIT_COMMAND, the input is not directly stored in scratchpad this way.
        # CHOOSE_REVISION stores to iteration_target_field (handled in get_next_phase)
        # AWAIT_COMMAND leads to phase transition.
        else:
            self.debug_log(step="store_input_iteration_noop", internal_state=current_internal_state)


    def get_next_phase_after_completion(self) -> str | None:
        current_internal_state = st.session_state.get("iteration_internal_state")
        # user_input is implicitly the one that passed micro_validate from PhaseEngineBase
        # and is available in st.session_state.last_user_input
        user_input = st.session_state.get("last_user_input", "")
        intent = st.session_state.get("last_intent_classified", "")

        self.debug_log(step="iteration_get_next_phase", current_state=current_internal_state, user_input=user_input, intent=intent)

        if current_internal_state == self.ITERATION_STATE_CHOOSE_REVISION:
            # Input should be the field name to revise.
            # micro_validate in persona should ensure it's not a generic "ok" for this state.
            # For now, assume user_input is the field name.
            target_field_input = user_input.strip().lower().replace(" ", "_")
            # Use SCRATCHPAD_KEYS from value_prop/__init__.py, excluding non-user-editable ones
            valid_fields_to_revise = [
                key for key in SCRATCHPAD_KEYS
                if key not in ["research_requests", "cached_recommendations", "final_summary",
                               "vp_background", "vp_interests", "vp_problem_motivation", "vp_anything_else"] # Intake keys are not revised here
            ]
            # Also allow revising the main value prop phases directly by their phase_name
            valid_fields_to_revise.extend([p for p in PHASE_ORDER if p not in ["intake", "recommendation", "iteration", "summary"] and p not in valid_fields_to_revise])


            if target_field_input in valid_fields_to_revise:
                st.session_state.iteration_target_field = target_field_input
                st.session_state.iteration_internal_state = self.ITERATION_STATE_GET_REVISION_DETAIL
                self.debug_log(step="iteration_state_transition_to_get_detail", target=target_field_input)
                return None # Stay in iteration phase, next enter() will give new prompt
            else:
                # Input was not a valid field. Base class handle_response would have called micro_validate.
                # If micro_validate passed (e.g. "ok"), but it's not a field, it's an issue.
                # The persona's get_clarification_prompt (called by base if micro_validate fails) should handle this.
                # We don't transition state here.
                self.debug_log(step="iteration_choose_field_invalid", provided=target_field_input, valid_options=valid_fields_to_revise)
                return None # Stay, let persona clarify

        elif current_internal_state == self.ITERATION_STATE_GET_REVISION_DETAIL:
            # Input (the revised text) has been validated by persona & stored by store_input_to_scratchpad.
            st.session_state.iteration_internal_state = self.ITERATION_STATE_AWAIT_COMMAND
            self.debug_log(step="iteration_state_transition_to_await_command")
            return None # Stay in iteration phase

        elif current_internal_state == self.ITERATION_STATE_AWAIT_COMMAND:
            # Input should be "summary" or "re-run"
            # micro_validate should have confirmed this if intent was "provide_detail"
            # or intent classification caught it.
            txt_lower = user_input.lower().strip()
            if "summary" in txt_lower: # This could also be intent == "go_to_summary" if we had such an intent
                self._reset_internal_iteration_state()
                self.mark_complete() # Iteration phase is fully complete
                self.debug_log(step="iteration_complete_transition_to_summary")
                return "summary"
            elif "re-run" in txt_lower or "rerun" in txt_lower: # Intent == "request_rerun"
                self._reset_internal_iteration_state()
                self.mark_complete() # Iteration phase is complete for this cycle, will re-enter recommendation
                self.debug_log(step="iteration_complete_transition_to_recommendation_for_rerun")
                return "recommendation"
            else:
                # Invalid command, persona clarification should handle.
                # PhaseEngineBase would have called get_clarification_prompt.
                self.debug_log(step="iteration_await_command_invalid_stay", command=txt_lower)
                return None # Stay, let persona clarify
        
        self.debug_log(step="get_next_phase_iteration_fallthrough", state=current_internal_state)
        return None # Default to staying in iteration phase if logic is unclear

    def get_next_phase_after_skip(self) -> str | None:
        # Skipping within iteration sub-states doesn't make much sense.
        # Treat skip as needing clarification for the current sub-state.
        self.debug_log(step="get_next_phase_after_skip_iteration", internal_state=st.session_state.get("iteration_internal_state"))
        # The base class will call coach_persona.get_clarification_prompt or suggest_examples.
        # We don't change internal state or phase here.
        return None

    def _reset_internal_iteration_state(self):
        st.session_state.iteration_internal_state = self.ITERATION_STATE_CHOOSE_REVISION
        st.session_state.iteration_target_field = None
        # self._is_complete = False # Reset completion for the overall iteration phase if re-entering
        self.debug_log(step="_reset_internal_iteration_state_called")