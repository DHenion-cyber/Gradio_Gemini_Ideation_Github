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
                "placeholder": "E.g., Software Engineer, Nurse, Researcher, MBA Student"
            },
            {
                "key": "vp_interests",
                "header": "Interests / Experiences",
                "question": "Do you have any particular interests or past experiences that motivate you to think about healthcare innovation?",
                "placeholder": "E.g., Personal health journey, family experience, volunteer work"
            },
            {
                "key": "vp_problem_motivation",
                "header": "Problem Motivation",
                "question": "Are there specific problems or inefficiencies in healthcare that you feel strongly about addressing? (Optional)",
                "placeholder": "E.g., Long wait times, data silos, access to care (leave blank if none)"
            },
            {
                "key": "vp_anything_else",
                "header": "Anything Else?",
                "question": "Is there anything else you want to me to know or consider before we start brainstorming?",
                "placeholder": "E.g., I’d like a small community-benefit startup that’s self-sustaining and needs <10 hrs/month from me."
            }
        ]
        self.current_question_index = 0
        if "intake_question_index" not in st.session_state:
            st.session_state.intake_question_index = 0
        self.current_question_index = st.session_state.intake_question_index

        if "scratchpad" not in st.session_state:
            st.session_state["scratchpad"] = {}

    def enter(self) -> str:
        super().enter() # Calls debug_log and log_event for phase_enter
        self.current_question_index = st.session_state.get("intake_question_index", 0)
        if self.current_question_index < len(self.questions):
            question_data = self.questions[self.current_question_index]
            # These will be used by Streamlit UI to render header and placeholder
            st.session_state["current_phase_header"] = question_data["header"]
            st.session_state["current_phase_placeholder"] = question_data["placeholder"]
            log_event("intake_question_presented", phase_name=self.phase_name, workflow_name=self.workflow_name, question_key=question_data["key"])
            return question_data["question"]
        else:
            # This should ideally not be reached if phase transitions correctly
            self.mark_complete()
            return "We've completed the intake. Let's move on."

    def handle_response(self, user_input: str) -> dict:
        self.debug_log(step="handle_response_start", user_input=user_input, current_question_index=self.current_question_index)

        # Store the answer
        current_question_data = self.questions[self.current_question_index]
        st.session_state["scratchpad"][current_question_data["key"]] = user_input
        log_event("intake_answer_received", phase_name=self.phase_name, workflow_name=self.workflow_name, question_key=current_question_data["key"], answer_length=len(user_input))

        # Move to the next question or complete the phase
        self.current_question_index += 1
        st.session_state.intake_question_index = self.current_question_index

        if self.current_question_index < len(self.questions):
            next_question_data = self.questions[self.current_question_index]
            st.session_state["current_phase_header"] = next_question_data["header"]
            st.session_state["current_phase_placeholder"] = next_question_data["placeholder"]
            log_event("intake_question_presented", phase_name=self.phase_name, workflow_name=self.workflow_name, question_key=next_question_data["key"])
            self.debug_log(step="next_question", next_question_key=next_question_data["key"])
            # Acknowledge and ask next question
            ack_message = self.coach_persona.acknowledge_user_input(user_input, current_question_data.get("header"))
            return {"next_phase": None, "reply": f"{ack_message} {next_question_data['question']}"}
        else:
            self.mark_complete()
            st.session_state.intake_question_index = 0 # Reset for potential future runs
            # Clear header/placeholder for next phase
            if "current_phase_header" in st.session_state:
                del st.session_state["current_phase_header"]
            if "current_phase_placeholder" in st.session_state:
                del st.session_state["current_phase_placeholder"]
            log_event("intake_complete", phase_name=self.phase_name, workflow_name=self.workflow_name)
            self.debug_log(step="intake_complete_transitioning_to_problem")
            ack_message = self.coach_persona.acknowledge_user_input(user_input, current_question_data.get("header"))
            return {"next_phase": "problem", "reply": f"{ack_message} Thanks for sharing that. Now, let's move on to the 'Problem' phase."}

    def get_current_question_display_info(self) -> dict:
        """Provides current question's header and placeholder for the UI."""
        if not self.complete and self.current_question_index < len(self.questions):
            q_data = self.questions[self.current_question_index]
            return {"header": q_data["header"], "placeholder": q_data["placeholder"]}
        return {"header": None, "placeholder": None}