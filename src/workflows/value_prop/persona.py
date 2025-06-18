from src.core.coach_persona_base import CoachPersonaBase
import streamlit as st # For accessing scratchpad if needed by persona logic

# A more sophisticated persona would likely use an LLM or more complex logic.
# For now, these are placeholders or simple pass-throughs.

class ValuePropCoachPersona(CoachPersonaBase):
    """
    Coach persona specific to the Value Proposition workflow.
    """
    def __init__(self, workflow_name: str = "value_prop"):
        self.workflow_name = workflow_name
        # Potentially load workflow-specific prompts or configurations here

    def _get_scratchpad_value(self, key: str, default: str = "") -> str:
        """Helper to get a value from the workflow-specific scratchpad."""
        # Assuming scratchpad keys are stored unprefixed in st.session_state.scratchpad
        # and PhaseEngineBase/WorkflowManager handles prefixing if necessary for storage.
        # For direct access here, we assume keys are as defined for the workflow.
        return st.session_state.get("scratchpad", {}).get(key, default)

    def get_step_intro_message(self, phase_name: str, **kwargs) -> str:
        """
        Returns the introductory message or question for the current phase/step.
        """
        # These messages are adapted from the original ValuePropWorkflow state classes
        # In a real scenario, these might be dynamically generated or come from a config.
        # The phase_name here corresponds to the 'name' attribute of the old IdeationState classes.
        # e.g., "use_case", "problem", "target_customer", etc.

        current_value = self._get_scratchpad_value(phase_name)

        if phase_name == "use_case":
            if current_value:
                return f"We previously discussed the use case: {current_value}. Would you like to explore this now? (yes/no)"
            return "Let's start by defining the primary use case for your idea. What specific scenario or situation will your product/service address? Would you like to explore this now? (yes/no)"
        elif phase_name == "problem":
            if current_value:
                return f"We identified the problem as: {current_value}. Would you like to explore this now? (yes/no)"
            return "Next, let's clearly define the problem your idea solves. What specific pain point or unmet need are you addressing? Would you like to explore this now? (yes/no)"
        elif phase_name == "target_customer":
            if current_value:
                return f"Our target customer is: {current_value}. Would you like to explore this now? (yes/no)"
            return "Who is the target customer for this solution? Describe your ideal user or buyer. Would you like to explore this now? (yes/no)"
        elif phase_name == "solution":
            if current_value:
                return f"The proposed solution is: {current_value}. Would you like to explore this now? (yes/no)"
            return "What is your proposed solution to this problem for the target customer? Describe your product or service. Would you like to explore this now? (yes/no)"
        elif phase_name == "main_benefit":
            if current_value:
                return f"The main benefit is: {current_value}. Would you like to explore this now? (yes/no)"
            return "What is the single most important benefit your solution provides to the target customer? Would you like to explore this now? (yes/no)"
        elif phase_name == "differentiator":
            if current_value:
                return f"Our key differentiator is: {current_value}. Would you like to explore this now? (yes/no)"
            return "What makes your solution different from or better than existing alternatives? This is your key differentiator. Would you like to explore this now? (yes/no)"
        elif phase_name == "recommendation":
            # This phase is more complex in the original, involving cached_recommendations
            # For now, a simple intro. The PhaseEngine will handle the actual recommendation display.
            return "I've analyzed your inputs. Here are my top recommendations. Type 'iterate' to refine, or 'summary' to wrap up."
        elif phase_name == "revise": # For Iteration's ReviseState
            return "We're in iteration. Which part of your value proposition would you like to revise (e.g., problem, solution, target_customer)?"
        elif phase_name == "revise_detail": # For Iteration's ReviseDetailState
            target_to_revise = kwargs.get("target_to_revise", "the selected item")
            return f"Okay, let's revise {target_to_revise.replace('_', ' ')}. What's the new text?"
        elif phase_name == "rerun": # For Iteration's RerunState
            return "Re-running recommendations with your updated inputs..."
        elif phase_name == "summary":
            # The SummaryPhase will generate the actual summary. This is just an intro.
            return "Let's generate the final summary of your value proposition."
        else:
            return f"Welcome to the {phase_name.replace('_', ' ')} phase. What are your thoughts?"


    def micro_validate(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        """
        Provides a micro-validation or immediate feedback on the user's input.
        """
        # Example: if a user provides input for 'problem', this could be:
        # "Thanks for sharing the problem statement."
        # This can be made more intelligent.
        if user_input:
            return f"Got it. You mentioned: '{user_input[:50]}...'."
        return "Okay."

    def suggest_examples(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        """
        Suggests examples or provides hints if the user is stuck or input is unclear.
        """
        if phase_name == "problem":
            return "For example, a problem could be 'university students struggle to find affordable off-campus housing' or 'small businesses find it hard to manage online reviews'."
        elif phase_name == "use_case":
            return "A use case could be 'a student quickly finding relevant study materials for an exam' or 'a remote team collaborating effectively on a project document'."
        # Add more phase-specific examples
        return "I'm not sure what to suggest for this right now. Could you try rephrasing or being more specific?"

    def summarise_intake(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        """
        Summarises the user's input in a structured way, often to confirm understanding.
        """
        # This would typically be used after collecting a piece of information.
        # Example: "So, to confirm, the {phase_name.replace('_', ' ')} you've described is: '{user_input}'. Is that correct?"
        # For now, a simpler confirmation.
        return f"So, for {phase_name.replace('_', ' ')}, you're thinking: '{user_input[:100]}...'. Does that sound right?"

    def get_clarification_prompt(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        return f"I'm not quite sure I understand that in the context of {phase_name.replace('_', ' ')}. Could you please elaborate or rephrase?"

    def get_positive_affirmation_response(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        return "Great! Let's proceed."

    def get_negative_affirmation_response(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        return f"Okay, let's reconsider the {phase_name.replace('_', ' ')} then. What are your thoughts now?"

    # --- Value-Prop Specific Persona Methods (examples, can be expanded) ---

    def generate_value_prop_recommendations(self, scratchpad: dict) -> str:
        """
        Generates recommendations based on the filled scratchpad.
        This is a placeholder. A real implementation would use an LLM or rule-based system.
        """
        # Based on the original RecommendationState's dummy_recs
        problem = scratchpad.get("problem", "the defined problem")
        solution = scratchpad.get("solution", "your solution")
        target_customer = scratchpad.get("target_customer", "your target customer")

        recs = [
            f"1. Ensure your messaging for '{solution}' clearly addresses '{problem}' for '{target_customer}'.",
            f"2. Consider testing the appeal of your main benefit with a small segment of '{target_customer}'.",
            f"3. Double-check if your differentiator is truly unique compared to competitors targeting '{target_customer}'."
        ]
        return "\n".join(recs)

    def generate_value_prop_summary(self, scratchpad: dict) -> str:
        """
        Generates a final summary paragraph for the value proposition.
        Placeholder, similar to the original ValuePropWorkflow.generate_summary().
        """
        summary_parts = []
        if scratchpad.get("use_case"):
            summary_parts.append(f"The primary use case is '{scratchpad['use_case']}'.")
        if scratchpad.get("problem"):
            summary_parts.append(f"It addresses the problem of '{scratchpad['problem']}'")
        if scratchpad.get("target_customer"):
            summary_parts.append(f"for {scratchpad['target_customer']}.")
        if scratchpad.get("solution"):
            summary_parts.append(f"The proposed solution, '{scratchpad['solution']}',")
        if scratchpad.get("main_benefit"):
            summary_parts.append(f"offers the main benefit of '{scratchpad['main_benefit']}'.")
        if scratchpad.get("differentiator"):
            summary_parts.append(f"It stands out due to '{scratchpad['differentiator']}'.")

        if not summary_parts:
            return "No information was provided to generate a summary."
        
        full_summary = " ".join(summary_parts)
        # Simple grammar correction for flow
        full_summary = full_summary.replace(" .", ".").replace(" ,", ",")
        return full_summary.strip()