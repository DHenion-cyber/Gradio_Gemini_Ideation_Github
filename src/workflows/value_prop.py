"""Defines the ValuePropWorkflow class, managing the value proposition coaching process."""
import streamlit as st
from typing import TYPE_CHECKING
from .base import WorkflowBase # Added import

# Persona will be passed in, no direct import needed here unless for type hinting
if TYPE_CHECKING:
    from personas.coach import CoachPersona

class ValuePropWorkflow(WorkflowBase): # Inherit from WorkflowBase
    def __init__(self, context=None):
        """
        Initializes the ValuePropWorkflow.
        The 'persona_instance' (CoachPersona) must be provided within the 'context' dictionary.
        """
        self.context = context or {}
        self.persona = self.context.get('persona_instance') # Get persona from context
        if self.persona is None:
            raise ValueError("A 'persona_instance' of CoachPersona must be provided in the context for ValuePropWorkflow.")
        
        self.current_step = "problem"  # Initial step
        self.scratchpad = {
            "problem": "",
            "target_customer": "",
            "solution": "",
            "main_benefit": "",
            "differentiator": "",
            "use_case": "",
            "research_requests": []
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

    def process_user_input(self, user_input: str): # search_results parameter removed to match WorkflowBase
        """
        Processes the user's input for the value proposition workflow,
        updates the scratchpad, and determines the next interaction.
        Conforms to WorkflowBase.process_user_input.
        """
        # This import is needed here if not already at module level and if update_scratchpad is a global util
        from utils.scratchpad_extractor import update_scratchpad # Ensure this path is correct
        from llm_utils import query_openai, build_conversation_messages # For direct LLM call if needed

        user_input_stripped = user_input.strip()
        core_response = ""
        preliminary_message = ""

        # Update internal scratchpad - ValuePropWorkflow manages its own scratchpad
        # The generic update_scratchpad might be too broad if ValuePropWorkflow has specific logic.
        # For now, let's assume ValuePropWorkflow updates its self.scratchpad directly or via a dedicated method.
        # If user_input_stripped is relevant to the current_step, it will be stored later.
        # The generic update_scratchpad from conversation_phases might try to update all fields.
        # Let's defer scratchpad update until stance is known or specific logic applies.

        # Determine if we are in the initial "exploration" phase for the value proposition
        # This could be when 'problem' is the current step and it's empty,
        # or a more explicit state if ValuePropWorkflow had an 'is_exploring' flag.
        is_initial_exploration = (self.current_step == "problem" and not self.scratchpad.get("problem"))

        if is_initial_exploration and user_input_stripped: # And user has provided some input for exploration
            # This section mirrors the core of the old `handle_exploration`
            # The scratchpad update here should be specific to exploration if needed,
            # or rely on the general update_scratchpad if that's appropriate.
            # For now, let's assume update_scratchpad is a general utility.
            self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy()) # Update own scratchpad
            st.session_state["scratchpad"] = self.scratchpad # Also update global for other modules if necessary

            try:
                messages_for_llm = build_conversation_messages(
                    scratchpad=self.scratchpad,
                    latest_user_input=user_input_stripped,
                    current_phase="exploration" # Explicitly set phase for LLM
                )
                core_response = query_openai(messages=messages_for_llm)
                if not core_response or not core_response.strip():
                    core_response = "I'm processing that. Could you tell me a bit more, or perhaps we can explore another angle?"
                    # Consider logging this via self.persona or a direct log call
            except Exception as e:
                # st.error(f"Error querying LLM in exploration: {e}") # UI call, persona should handle
                core_response = f"I encountered an issue during exploration: {e}. Could you please try rephrasing?"
            # After this exploration call, the LLM (guided by VALUE_PROP_EXPLORATION_SYSTEM_PROMPT)
            # might have filled some scratchpad items or asked a question.
            # The next call to process_user_input will then proceed to step-specific logic.
            # The reflection prompt will be added at the end.

        else: # Not initial exploration, or no user input for exploration -> proceed with step-specific logic
            # 1. Handle intake-to-ideation transition message (once at the beginning)
            if self.current_step == "problem" and not st.session_state.get("vp_intake_complete", False):
                preliminary_message = self.persona.get_intake_to_ideation_transition_message()
                st.session_state["vp_intake_complete"] = True

            # 2. Handle dedicated step introductions
            if not preliminary_message:
                step_intro = self.persona.get_step_intro_message(self.current_step, self.scratchpad)
                if step_intro:
                    preliminary_message = step_intro
                    if not user_input_stripped:
                        return preliminary_message + self.persona.get_reflection_prompt()

            if preliminary_message and not user_input_stripped:
                return preliminary_message + self.persona.get_reflection_prompt()

            # 3. Handle empty user input for current step
            if not user_input_stripped:
                if not self.scratchpad.get(self.current_step) and \
                   (self.current_step != "problem" or st.session_state.get("vp_intake_complete", False)):
                    core_response = self.persona.get_prompt_for_empty_input(self.current_step)
            else: # user_input_stripped is NOT empty
                # Generic scratchpad update based on user input.
                # This might be too aggressive. Consider updating only self.current_step or based on LLM extraction.
                # For now, let's keep it simple: update the current step if stance is decided.
                # The update_scratchpad utility from scratchpad_extractor.py is more sophisticated.
                # Let's use that for a general update first.
                # self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                # st.session_state["scratchpad"] = self.scratchpad # Keep global session state sync

                stance = self.persona.detect_user_stance(user_input_stripped, self.current_step)
                effective_stance = stance

                # Store user input into the specific current_step if decided
                if stance == "decided":
                    self.scratchpad[self.current_step] = user_input_stripped
                elif self.current_step == "differentiator" and self.scratchpad.get("main_benefit") and not self.scratchpad.get("differentiator"):
                    self.scratchpad["differentiator"] = user_input_stripped
                    effective_stance = "decided"
                elif self.current_step == "use_case" and self.scratchpad.get("differentiator") and not self.scratchpad.get("use_case"):
                    self.scratchpad["use_case"] = user_input_stripped
                    effective_stance = "decided"
                
                # After potentially updating the current step, a more general update_scratchpad can refine other fields
                # This ensures the current step is prioritized by direct assignment if "decided".
                self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                st.session_state["scratchpad"] = self.scratchpad


                if effective_stance == "decided":
                    core_response = self.persona.coach_on_decision(
                        self.current_step, user_input_stripped, self.scratchpad, effective_stance # search_results removed
                    )
                else: # uncertain, open, interest, neutral
                    core_response = self.persona.paraphrase_user_input(
                        user_input_stripped, stance, self.current_step, self.scratchpad # search_results removed
                    )

        final_response_parts = []
        if preliminary_message:
            final_response_parts.append(preliminary_message)
        
        if core_response:
            final_response_parts.append(core_response.strip())
        
        final_response_str = " ".join(final_response_parts).strip()

        if final_response_str:
            return final_response_str + self.persona.get_reflection_prompt()
        # If by some chance final_response_str is empty (e.g. empty preliminary and core_response)
        # return a generic prompt or handle appropriately.
        # For now, this case should be rare.
        return self.persona.get_prompt_for_empty_input(self.current_step) + self.persona.get_reflection_prompt() if not final_response_str else final_response_str

    def add_research_request(self, step: str, details: str = ""):
        self.scratchpad["research_requests"].append({"step": step, "details": details})

    def generate_summary(self):
        """
        Generates a summary of the current state of the value proposition workflow.
        Delegates the actual summary content generation to the persona.
        Conforms to WorkflowBase.generate_summary.
        """
        # Delegates summary generation entirely to the persona.
        return self.persona.generate_value_prop_summary(self.scratchpad) # Use self.persona

    def is_complete(self):
        """
        Checks if the value proposition workflow has reached its completion state.
        Conforms to WorkflowBase.is_complete.
        """
        return self.completed

    def get_step(self):
        """
        Returns the current step or phase of the value proposition workflow.
        Conforms to WorkflowBase.get_step.
        """
        return self.current_step
