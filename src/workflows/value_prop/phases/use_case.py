import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.workflows.value_prop.persona import ValuePropCoachPersona # Corrected import
from src.analytics import log_event

class UseCasePhase(PhaseEngineBase):
    phase_name = "use_case"

    def __init__(self, coach_persona: ValuePropCoachPersona, workflow_name: str):
        super().__init__(coach_persona, workflow_name)
        # Ensure coach_persona is an instance of ValuePropCoachPersona for type hinting
        self.coach_persona: ValuePropCoachPersona = coach_persona
        if "scratchpad" not in st.session_state:
            st.session_state["scratchpad"] = {}
        # State to manage if we are waiting for user to select a suggested use case
        if "use_case_waiting_for_suggestion_selection" not in st.session_state:
            st.session_state.use_case_waiting_for_suggestion_selection = False
        if "use_case_suggestions" not in st.session_state:
            st.session_state.use_case_suggestions = []


    def enter(self) -> str:
        super().enter() # Resets _is_complete for this interaction attempt
        
        # If we are waiting for a selection, the prompt should reflect that.
        # The actual suggestions would have been given in the previous turn's reply.
        if st.session_state.get("use_case_waiting_for_suggestion_selection", False):
            # The persona's suggest_examples (called by base class) should have provided the numbered list.
            # The prompt here is just a reminder if needed, or can be part of the persona's reply.
            # For now, assume the persona's reply from the "ask_suggestion" intent handled the prompt.
            # This enter() call is more about setting up for the *next* input.
            # If the suggestions were just presented, the user is about to type a number.
            # The base class's `handle_response` will get that number.
            # `store_input_to_scratchpad` and `get_next_phase_after_completion` will process it.
            # So, the prompt from `enter()` when waiting for selection might be minimal or just re-iterate.
            # Let's rely on the persona's reply from the previous turn to have the main prompt.
            # This `enter` can provide a generic "Please make your selection." if needed,
            # but usually the last bot message already asked for the number.
            # For simplicity, if waiting for selection, the main prompt is already active.
            # We just ensure the state is correctly set.
            self.debug_log(step="enter_use_case_waiting_for_selection")
            # The actual list of suggestions should be in the last bot message.
            # The persona's `suggest_examples` method (called by base `handle_response`) is responsible for formatting that.
            return self.coach_persona.get_clarification_prompt(user_input="", phase_name=self.phase_name, reason="awaiting_suggestion_selection")

        # Standard entry: not waiting for a selection from a list.
        st.session_state.use_case_waiting_for_suggestion_selection = False
        st.session_state.use_case_suggestions = []

        interests = st.session_state.get("scratchpad", {}).get("vp_interests", "")
        problem_motivation = st.session_state.get("scratchpad", {}).get("vp_problem_motivation", "")
        
        recap_message = ""
        story_found = False
        if interests:
            recap_message += f"Based on your interests, you mentioned: \"{interests}\". "
            story_found = True
        if problem_motivation:
            recap_message += f"Regarding problem motivation, you noted: \"{problem_motivation}\". "
            story_found = True

        base_prompt = self.coach_persona.get_step_intro_message(phase_name=self.phase_name) # "Let's define a concrete use-case..."
        
        full_prompt = base_prompt
        if story_found:
            full_prompt = f"{recap_message}\n{base_prompt} Would you like to use aspects of that story, share a different one, or have me draft some ideas based on published data?"
        else:
            full_prompt = f"{base_prompt} Would you like to share one, or have me draft some ideas based on published data?"
        
        log_event("use_case_prompted", phase_name=self.phase_name, workflow_name=self.workflow_name, story_found=story_found)
        return full_prompt

    def store_input_to_scratchpad(self, user_input: str):
        intent = st.session_state.get("last_intent_classified", self.classify_intent(user_input))
        
        if st.session_state.get("use_case_waiting_for_suggestion_selection", False):
            # User input is expected to be a number (index for suggestion)
            # The actual storage of the selected use case text happens in get_next_phase_after_completion
            # after the index is validated.
            self.debug_log(step="store_input_use_case_selection_pending", raw_selection_input=user_input)
            # We could store the raw number input here if needed for analytics.
            st.session_state.scratchpad["temp_use_case_selection_input"] = user_input
        elif intent == "provide_detail": # User provided their own use case text
            st.session_state["scratchpad"]["vp_use_case"] = user_input.strip()
            self.debug_log(step="store_input_use_case_direct", input_len=len(user_input))
        else:
            # For "ask_suggestion", "skip", "unclear", etc., no direct text is stored as "vp_use_case" here.
            self.debug_log(step="store_input_use_case_noop_for_intent", intent=intent)

    def get_next_phase_after_completion(self) -> str | None:
        # This method is called by PhaseEngineBase *after* input has been deemed valid
        # (non-empty, passed micro_validate if it was "provide_detail" or "affirm").
        # The intent is available from the base class's processing.
        user_input = st.session_state.get("last_user_input", "") # Assuming WorkflowManager or Base stores this
        intent = st.session_state.get("last_intent_classified", self.classify_intent(user_input))

        self.debug_log(step="get_next_phase_use_case_start", intent=intent, waiting_selection=st.session_state.get("use_case_waiting_for_suggestion_selection"))

        if st.session_state.get("use_case_waiting_for_suggestion_selection", False):
            try:
                # User input here is the *validated* selection number (or text that micro_validate passed)
                # The actual selection text needs to be retrieved from use_case_suggestions
                raw_selection_input = st.session_state.scratchpad.get("temp_use_case_selection_input", user_input)
                selection_index = int(raw_selection_input.strip()) - 1
                
                if 0 <= selection_index < len(st.session_state.use_case_suggestions):
                    selected_use_case = st.session_state.use_case_suggestions[selection_index]
                    st.session_state["scratchpad"]["vp_use_case"] = selected_use_case # Actual storage
                    log_event("use_case_suggestion_selected", phase_name=self.phase_name, selection=selected_use_case, index=selection_index)
                    st.session_state.use_case_waiting_for_suggestion_selection = False
                    st.session_state.use_case_suggestions = []
                    if "temp_use_case_selection_input" in st.session_state.scratchpad:
                        del st.session_state.scratchpad["temp_use_case_selection_input"]
                    self.mark_complete() # Use case selected, phase is done
                    return "recommendation"
                else:
                    log_event("use_case_invalid_selection_index_in_get_next", index_input=raw_selection_input)
                    # This case implies micro_validate passed something that wasn't a valid number in range.
                    # Persona should clarify. Stay in phase.
                    st.session_state.use_case_waiting_for_suggestion_selection = True # Remain waiting
                    return None
            except ValueError:
                log_event("use_case_selection_not_int_in_get_next", input_val=user_input)
                # micro_validate should have caught this if it wasn't "ok" etc.
                st.session_state.use_case_waiting_for_suggestion_selection = True # Remain waiting
                return None

        # Not waiting for selection, standard intents:
        if intent == "provide_detail": # User provided their own use case
            # Already stored by store_input_to_scratchpad
            log_event("use_case_provided_by_user_confirmed", phase_name=self.phase_name, length=len(user_input))
            self.mark_complete() # User provided use case, phase is done
            return "recommendation"
        
        if intent == "ask_suggestion":
            # Persona's suggest_examples (called by base) should have generated the reply with suggestions.
            # Here, we set the state to expect a selection.
            # The suggestions themselves are assumed to be in the persona's reply.
            # We need to capture them if the persona doesn't directly put them in session_state.
            # Let's assume ValuePropCoachPersona.suggest_examples for use_case stores them.
            # If not, this needs adjustment. For now, assume persona handles putting suggestions in its reply.
            
            # Simulate suggestions being available from persona (e.g. persona.last_suggestions)
            # This is a bit of a workaround because the base class's suggest_examples doesn't return the suggestions directly to here.
            # A better way: persona.suggest_examples stores suggestions in st.session_state.use_case_suggestions
            # Let's modify ValuePropCoachPersona.suggest_examples for 'use_case' to do this.
            # For now, we'll fetch them if the persona put them there.
            
            # This logic is now primarily handled by the persona's suggest_examples method.
            # That method should set use_case_waiting_for_suggestion_selection = True
            # and populate st.session_state.use_case_suggestions.
            # The reply from the persona will contain the numbered list.
            # So, if intent was ask_suggestion, we just stay in the phase.
            self.debug_log(step="get_next_phase_use_case_ask_suggestion_received")
            # Ensure the state is set if persona's suggest_examples did it
            if not st.session_state.get("use_case_waiting_for_suggestion_selection", False):
                 # This is a fallback if persona didn't set it, should be reviewed.
                 self.debug_log(warning="use_case_waiting_for_suggestion_selection not set by persona's suggest_examples")
                 # Attempt to generate suggestions here if not already done by persona.
                 # This duplicates logic that should be in the persona.
                 # For now, assume persona handles it.
            return None # Stay in phase, next `enter` will re-evaluate.

        # If "affirm" (e.g. "yes" to "use that story?"), and story was found.
        if intent == "affirm":
            interests = st.session_state.get("scratchpad", {}).get("vp_interests", "")
            problem_motivation = st.session_state.get("scratchpad", {}).get("vp_problem_motivation", "")
            if interests or problem_motivation: # If there was something to affirm
                affirmed_story = []
                if interests: affirmed_story.append(f"Interest: {interests}")
                if problem_motivation: affirmed_story.append(f"Motivation: {problem_motivation}")
                st.session_state.scratchpad["vp_use_case"] = "; ".join(affirmed_story)
                log_event("use_case_affirmed_from_prior_input", phase_name=self.phase_name)
                self.mark_complete() # User affirmed existing story, phase is done
                return "recommendation"

        # Default: if micro_validate passed but no specific path, stay and let persona clarify.
        self.debug_log(step="get_next_phase_use_case_fallthrough", intent=intent)
        return None

    def get_next_phase_after_skip(self) -> str | None:
        self.debug_log(step="get_next_phase_after_skip_use_case")
        st.session_state["scratchpad"]["vp_use_case"] = "User skipped providing a use case." # Store placeholder
        st.session_state.use_case_waiting_for_suggestion_selection = False
        st.session_state.use_case_suggestions = []
        # Do not mark complete if skipped, but allow progression.
        return "recommendation" # Proceed even if skipped