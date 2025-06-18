import streamlit as st
from src.core.phase_engine_base import PhaseEngineBase
from src.core.coach_persona_base import CoachPersonaBase
from src.analytics import log_event

class IntakePhase(PhaseEngineBase):
    phase_name = "intake"

    def __init__(self, coach_persona: CoachPersonaBase, workflow_name: str):
        super().__init__(coach_persona, workflow_name)
        self.questions = [
            {
                "key": "vp_background",
                "header": "Professional Background",
                "question": "What is your professional background or area of training?",
                "placeholder": "e.g., Hospital admin, MD/PhD, software engineer"
            },
            {
                "key": "vp_interests",
                "header": "Interests / Experiences",
                "question": "Do you have any particular interests or past experiences that motivate you to think about healthcare innovation?",
                "placeholder": "e.g., Interested in AI, equity, or care navigation"
            },
            {
                "key": "vp_problem_motivation",
                "header": "Problem Motivation",
                "question": "Are there specific problems or inefficiencies in healthcare that you feel strongly about addressing? (Optional)",
                "placeholder": "Optional — anything you’re passionate about fixing?"
            },
            {
                "key": "vp_anything_else",
                "header": "Anything Else?",
                "question": "Is there anything else you want to me to know or consider before we start brainstorming?",
                "placeholder": "Constraints, goals, or side-notes you want me to consider?"
            }
        ]
        # current_question_index is loaded from session_state in __init__ and enter
        if "intake_question_index" not in st.session_state:
            st.session_state.intake_question_index = 0
        self.current_question_index = st.session_state.intake_question_index

        if "scratchpad" not in st.session_state:
            st.session_state["scratchpad"] = {}

    def enter(self) -> str:
        # super().enter() is called by the workflow manager before this method if it's a new phase.
        # If we are re-entering the same phase (e.g. for the next question), super().enter() might not be called by manager.
        # However, PhaseEngineBase.enter() resets _is_complete, which is desired for each sub-question.
        # For safety and clarity, we call it here to ensure phase_enter event and _is_complete reset.
        super().enter()
        
        self.current_question_index = st.session_state.get("intake_question_index", 0)
        
        if self.current_question_index < len(self.questions):
            question_data = self.questions[self.current_question_index]
            st.session_state["current_phase_header"] = question_data["header"]
            st.session_state["current_phase_placeholder"] = question_data["placeholder"]
            log_event("intake_question_presented", phase_name=self.phase_name, workflow_name=self.workflow_name, question_key=question_data["key"], question_idx=self.current_question_index)
            self.debug_log(step="present_question", question_key=question_data["key"], index=self.current_question_index)
            return question_data["question"]
        else:
            # This state implies all questions have been answered or skipped.
            # The phase should have transitioned via get_next_phase_after_completion/skip.
            # If enter() is called when all questions are done, it's likely a redundant call or a state error.
            self.debug_log(step="enter_called_after_all_questions_done", index=self.current_question_index)
            # Mark complete here to be safe, though it should have been done by the base class
            # when the last valid input was processed.
            if not self._is_complete : # Check if base class already marked it.
                 self.mark_complete() # This marks the *entire phase* as complete.
            return self.coach_persona.get_completion_message(phase_name=self.phase_name, details="All intake questions have been addressed.")

    def store_input_to_scratchpad(self, user_input: str):
        """Stores the user's response for the current intake question."""
        if self.current_question_index < len(self.questions):
            current_question_data = self.questions[self.current_question_index]
            key_to_store = current_question_data["key"]
            st.session_state["scratchpad"][key_to_store] = user_input
            log_event("intake_answer_stored", phase_name=self.phase_name, workflow_name=self.workflow_name, question_key=key_to_store, answer_length=len(user_input), question_idx=self.current_question_index)
            self.debug_log(step="store_to_scratchpad", key=key_to_store, input_length=len(user_input))
        else:
            self.debug_log(step="store_input_to_scratchpad_error", error="current_question_index out of bounds", index=self.current_question_index)
            # This case should ideally not be reached if logic is correct.

    def _get_next_phase_logic(self, action_type: str) -> str | None:
        """Common logic for advancing after completion or skip."""
        self.debug_log(step=f"_get_next_phase_logic_start_for_{action_type}", old_idx=self.current_question_index)
        
        # The current question (at self.current_question_index) has just been processed (answered/skipped).
        # Now we advance the index for the *next* interaction.
        self.current_question_index += 1
        st.session_state.intake_question_index = self.current_question_index
        self.debug_log(step=f"advanced_question_index_for_{action_type}", new_idx=self.current_question_index)

        if self.current_question_index < len(self.questions):
            # More questions remain in the intake phase. Stay in the current phase.
            # The PhaseEngineBase.handle_response will see a None next_phase,
            # and the subsequent call to enter() will present the new current_question_index.
            # The _is_complete flag (for the sub-question) would have been set by PhaseEngineBase.
            # It will be reset by super().enter() when the next question is presented.
            return None
        else:
            # All intake questions are done. Transition to the next main phase.
            log_event("intake_all_questions_complete", phase_name=self.phase_name, workflow_name=self.workflow_name)
            self.debug_log(step="all_intake_questions_processed_transition")
            
            # Clean up session state specific to intake flow
            st.session_state.intake_question_index = 0 # Reset for potential future runs
            if "current_phase_header" in st.session_state:
                del st.session_state["current_phase_header"]
            if "current_phase_placeholder" in st.session_state:
                del st.session_state["current_phase_placeholder"]
            
            # All intake questions are done. Mark the entire IntakePhase as complete.
            self.mark_complete()
            self.debug_log(step="intake_phase_fully_completed_and_marked")
            return "problem"

    def get_next_phase_after_completion(self) -> str | None:
        """Determines the next step after a single intake question is completed."""
        return self._get_next_phase_logic("completion")

    def get_next_phase_after_skip(self) -> str | None:
        """Determines the next step after a single intake question is skipped."""
        return self._get_next_phase_logic("skip")