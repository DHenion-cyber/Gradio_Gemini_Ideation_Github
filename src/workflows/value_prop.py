"""
Defines the ValuePropWorkflow class, which manages the value proposition development process.
"""
import streamlit as st
# Persona will be passed in, no direct import needed here unless for type hinting
# from src.personas.coach import CoachPersona

class ValuePropWorkflow:
    def __init__(self, persona_instance, context=None):
        self.context = context or {}
        self.persona = persona_instance # Use the passed persona instance
        self.current_step = "problem"  # Initial step
        self.scratchpad = {
            "problem": "",
            "target_customer": "", # Changed from target_user
            "solution": "",
            "main_benefit": "", # Changed back to main_benefit
            "differentiator": "",
            "use_case": "", # Will store natural language description of use case(s)
            "research_requests": [] # List of strings or dicts
        }
        self.completed = False
        # self.intake_complete = False  # Flag for the initial intake message # Removed as per request

    def suggest_next_step(self, user_input=None):
        """
        Suggest the next most relevant step based on current scratchpad content and user intent.
        Allow user to revisit or expand previous steps if desired.
        """
        steps = ["problem", "target_customer", "solution", "main_benefit", "differentiator", "use_case"]
        # If the user input clearly refers to a previous or later step, honor that
        # (you can use simple keyword matching or a more advanced intent detector)
        if user_input:
            for step in steps:
                if step in user_input.lower(): # Simple keyword matching
                    self.current_step = step
                    return step
        # Otherwise, suggest the next incomplete step, but do not force it
        for step in steps:
            if not self.scratchpad.get(step):
                self.current_step = step
                return step
        # If all steps have content, remain flexible and ask what the user wants to focus on next
        self.current_step = "review"
        return "review"

    def process_user_input(self, user_input: str, search_results: list = None): # Added search_results
        user_input_stripped = user_input.strip()
        core_response = ""
        preliminary_message = "" # Will hold at most one preliminary message

        # 1. Handle intake-to-ideation transition message (once at the beginning)
        if self.current_step == "problem" and not st.session_state.get("vp_intake_complete", False):
            preliminary_message = self.persona.get_intake_to_ideation_transition_message() # Use self.persona
            st.session_state["vp_intake_complete"] = True

        # 2. Handle dedicated step introductions (if no intake message was just set)
        if not preliminary_message:
            step_intro = self.persona.get_step_intro_message(self.current_step, self.scratchpad) # Use self.persona
            if step_intro:
                preliminary_message = step_intro
                if not user_input_stripped: # If intro is shown and no user input, intro is the full response
                    return preliminary_message + self.persona.get_reflection_prompt() # Use self.persona

        # If there's a preliminary message and no user input, that message is the response.
        if preliminary_message and not user_input_stripped:
            return preliminary_message + self.persona.get_reflection_prompt() # Use self.persona

        # 3. Handle empty user input if not an intro-only response and current step needs input
        if not user_input_stripped:
            # Check if the current step is genuinely awaiting input
            if not self.scratchpad.get(self.current_step) and \
               (self.current_step != "problem" or st.session_state.get("vp_intake_complete", False)):
                core_response = self.persona.get_prompt_for_empty_input(self.current_step) # Use self.persona
            # else: user_input_stripped is empty, but no specific prompt needed.
            # core_response remains empty. preliminary_message (if any) will be shown if it exists.
        else: # user_input_stripped is NOT empty
            # 4. General stance handling and coaching
            # Pass search_results to persona methods if they can use it
            stance = self.persona.detect_user_stance(user_input_stripped, self.current_step) # Use self.persona
            effective_stance = stance # Stance used for coaching, may be overridden

            # Store user input based on stance and step
            # This logic remains in the workflow as it's about state management
            if stance == "decided":
                self.scratchpad[self.current_step] = user_input_stripped
            # Special handling for differentiator and use_case to capture input even if stance isn't "decided"
            # when the step is being introduced and user provides relevant input.
            elif self.current_step == "differentiator" and \
                 self.scratchpad.get("main_benefit") and \
                 user_input_stripped and \
                 not self.scratchpad.get("differentiator"):
                self.scratchpad["differentiator"] = user_input_stripped
                effective_stance = "decided" # Treat as decided for coaching this specific input
            elif self.current_step == "use_case" and \
                 self.scratchpad.get("differentiator") and \
                 user_input_stripped and \
                 not self.scratchpad.get("use_case"):
                self.scratchpad["use_case"] = user_input_stripped
                effective_stance = "decided" # Treat as decided for coaching this specific input

            # Call persona methods for dialog generation
            if effective_stance == "decided":
                core_response = self.persona.coach_on_decision( # Use self.persona
                    self.current_step, user_input_stripped, self.scratchpad, effective_stance, search_results=search_results
                )
            else: # uncertain, open, interest, neutral
                core_response = self.persona.paraphrase_user_input( # Use self.persona
                    user_input_stripped, stance, self.current_step, self.scratchpad, search_results=search_results
                )

        # Construct final response
        final_response_parts = []
        if preliminary_message:
            final_response_parts.append(preliminary_message)
        
        if core_response:
            final_response_parts.append(core_response.strip())
        
        final_response_str = " ".join(final_response_parts).strip()

        # Add reflection prompt if there's any content to reflect on
        if final_response_str:
            return final_response_str + self.persona.get_reflection_prompt() # Use self.persona
        return "" # Should ideally not happen if logic is correct

    def add_research_request(self, step: str, details: str = ""):
        self.scratchpad["research_requests"].append({"step": step, "details": details})

    def generate_summary(self):
        # Delegates summary generation entirely to the persona.
        return self.persona.generate_value_prop_summary(self.scratchpad) # Use self.persona

    def is_complete(self):
        return self.completed

    def get_step(self):
        return self.current_step
