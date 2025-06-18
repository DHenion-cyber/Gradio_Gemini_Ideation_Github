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
        super().enter()
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

        if story_found:
            prompt = f"{recap_message}Would you like to use that story as a concrete use-case example, share a different one, or have me draft one from published data?"
        else:
            prompt = "Let's define a concrete use-case example. Would you like to share one, or have me draft one from published data?"
        
        log_event("use_case_prompted", phase_name=self.phase_name, workflow_name=self.workflow_name, story_found=story_found)
        return prompt

    def handle_response(self, user_input: str) -> dict:
        self.debug_log(step="handle_response_start", user_input=user_input, waiting_for_selection=st.session_state.use_case_waiting_for_suggestion_selection)
        
        # If waiting for selection from suggestions
        if st.session_state.get("use_case_waiting_for_suggestion_selection", False):
            try:
                selection_index = int(user_input.strip()) - 1
                if 0 <= selection_index < len(st.session_state.use_case_suggestions):
                    selected_use_case = st.session_state.use_case_suggestions[selection_index]
                    st.session_state["scratchpad"]["vp_use_case"] = selected_use_case
                    ack = self.coach_persona.micro_validate(selected_use_case, phase_name=self.phase_name)
                    self.mark_complete()
                    log_event("use_case_suggestion_selected", phase_name=self.phase_name, workflow_name=self.workflow_name, selection=selected_use_case)
                    st.session_state.use_case_waiting_for_suggestion_selection = False
                    st.session_state.use_case_suggestions = []
                    return {"next_phase": "recommendation", "reply": f"{ack} Great choice. We'll use that as your use case."}
                else:
                    log_event("use_case_invalid_suggestion_selection", phase_name=self.phase_name, workflow_name=self.workflow_name, user_input=user_input)
                    return {"next_phase": None, "reply": "That doesn't seem like a valid selection. Please choose a number from the list."}
            except ValueError:
                log_event("use_case_invalid_suggestion_format", phase_name=self.phase_name, workflow_name=self.workflow_name, user_input=user_input)
                # Treat as unclear if not a number when expecting one
                reply = self.coach_persona.get_clarification_prompt(user_input, phase_name=self.phase_name)
                return {"next_phase": None, "reply": f"{reply} Please select a number from the suggestions, or tell me if you'd like to provide your own."}


        # Standard intent classification (will be enhanced later per Task E)
        # For now, simple keyword checking for "help", "draft", "different", "my own"
        # This is a temporary basic intent classification
        input_lower = user_input.lower()

        if "help" in input_lower or "draft" in input_lower or "published data" in input_lower: # Ask for help / suggestion
            log_event("use_case_ask_help", phase_name=self.phase_name, workflow_name=self.workflow_name)
            # Call persona.create_suggested_use_case() - to be implemented in Task C
            # For now, placeholder behavior until persona method is ready
            suggested_scenarios_str = self.coach_persona.create_suggested_use_case(st.session_state["scratchpad"])
            
            # Assuming create_suggested_use_case returns a string with scenarios, possibly numbered
            # Or a list of strings. Let's assume it returns a string that we parse or display.
            # For now, let's simulate it returns a list of strings.
            # This part will be refined once create_suggested_use_case is implemented.
            
            # Temporary simulation of suggestions
            # In reality, this comes from self.coach_persona.create_suggested_use_case
            suggestions = getattr(self.coach_persona, 'create_suggested_use_case', lambda x: ["Example use case 1: A busy professional uses a meal planning app to save time.", "Example use case 2: A student uses an AI tutor to prepare for exams."])(st.session_state["scratchpad"])

            if isinstance(suggestions, str): # If it returns a single string with newlines
                st.session_state.use_case_suggestions = [s.strip() for s in suggestions.split('\n') if s.strip()]
            elif isinstance(suggestions, list):
                 st.session_state.use_case_suggestions = suggestions
            else: # Fallback
                st.session_state.use_case_suggestions = ["Could not generate suggestions at this time."]

            if st.session_state.use_case_suggestions:
                response_text = "Okay, here are a couple of evidence-backed scenarios based on what you've shared:\n"
                for i, scenario in enumerate(st.session_state.use_case_suggestions):
                    response_text += f"{i+1}. {scenario}\n"
                response_text += "\nPlease type the number of the scenario you'd like to select, or describe your own."
                st.session_state.use_case_waiting_for_suggestion_selection = True
                log_event("use_case_suggestions_provided", phase_name=self.phase_name, workflow_name=self.workflow_name, count=len(st.session_state.use_case_suggestions))
                return {"next_phase": None, "reply": response_text}
            else:
                log_event("use_case_no_suggestions_generated", phase_name=self.phase_name, workflow_name=self.workflow_name)
                return {"next_phase": None, "reply": "I tried to draft some scenarios, but couldn't come up with any right now. Could you please share your own use case?"}

        elif len(user_input) > 10: # Arbitrary length to assume it's a user-provided story
            # Provide story
            st.session_state["scratchpad"]["vp_use_case"] = user_input
            ack = self.coach_persona.micro_validate(user_input, phase_name=self.phase_name)
            self.mark_complete()
            log_event("use_case_provided_by_user", phase_name=self.phase_name, workflow_name=self.workflow_name, length=len(user_input))
            return {"next_phase": "recommendation", "reply": f"{ack} That's a clear use case. We'll proceed with that."}
        
        else: # Unclear
            log_event("use_case_unclear_input", phase_name=self.phase_name, workflow_name=self.workflow_name, user_input=user_input)
            reply = self.coach_persona.get_clarification_prompt(user_input, phase_name=self.phase_name)
            return {"next_phase": None, "reply": reply}