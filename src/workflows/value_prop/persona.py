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


    GENERIC_RESPONSES = [
        "ok", "okay", "sure", "yes", "yeah", "yep", "got it", "idk", "i don't know", "maybe",
        "alright", "fine", "sounds good", "correct", "mmhmm", "uh huh", "k"
    ]

    def micro_validate(self, user_input: str, phase_name: str = "", **kwargs) -> bool:
        """
        Validates if the user input is specific enough and not too short or generic.
        Returns True if valid, False otherwise.
        """
        input_clean = user_input.strip().lower()

        if not input_clean:
            return False  # Empty input is not valid content

        # Check for length (Task C: <= 5 characters is too short)
        if len(input_clean) <= 5:
            # Allow short specific inputs if not generic (e.g. "AI" for interests if phase allows)
            # However, the rule is generic: <=5 is too short.
            # We need to be careful if a phase *expects* very short input.
            # For now, apply the rule generally.
            if input_clean not in self.GENERIC_RESPONSES: # e.g. "AI" is short but not generic
                 # If a phase specifically allows very short, non-generic answers, this might need adjustment
                 # For now, sticking to the rule: <=5 is generally too short for meaningful phase input.
                 # Let's consider if the phase is 'intake' for vp_problem_motivation (optional)
                 if phase_name == "vp_problem_motivation" and not input_clean: # Empty is fine for optional
                     return True # Explicitly allowing empty for this optional field if it reaches here (though empty check above handles it)
                 # If it's short AND generic, it's definitely false. If short but not generic, it's borderline.
                 # Task C: "If input is too short or generic (≤ 5 characters or in generic-list)"
                 # This implies length alone can be a reason.
                 return False


        # Check against generic responses list (Task C)
        if input_clean in self.GENERIC_RESPONSES:
            return False

        # Add any phase-specific validation if needed
        # if phase_name == "some_specific_phase":
        #     if not self._is_valid_for_some_specific_phase(input_clean):
        #         return False

        return True # Input is considered specific enough

    def get_acknowledgement_message(self, phase_name: str, user_input: str, **kwargs) -> str:
        """
        Provides an acknowledgement message for valid user input.
        """
        # PhaseEngineBase calls this when micro_validate is True.
        phase_display = phase_name.replace('_', ' ')
        user_input_length = len(kwargs.get("user_input", "").split()) # Get word count

        if phase_name.startswith("vp_"): # For intake sub-questions
            header = kwargs.get("header", phase_display)
            if user_input_length <= 3: # Arbitrary short length
                return "Got it, thanks."
            return f"Thanks for sharing your thoughts on '{header}'. I've noted that."
        
        # For other phases
        if user_input_length <= 3: # Arbitrary short length
            return f"Okay, noted for {phase_display}."
        return f"Thanks for detailing the {phase_display}. I've noted that."

    def suggest_examples(self, phase_name: str, user_input: str = "", **kwargs) -> str:
        """
        Suggests examples or provides hints if the user is stuck or input is unclear.
        For 'use_case', it generates numbered suggestions and sets state for selection.
        """
        if phase_name == "problem":
            return "For example, a problem could be 'university students struggle to find affordable off-campus housing' or 'small businesses find it hard to manage online reviews'."
        elif phase_name == "use_case":
            # Generate suggestions using the dedicated method
            suggestions = self.create_suggested_use_case(st.session_state.get("scratchpad", {}))
            
            if suggestions:
                st.session_state.use_case_suggestions = suggestions
                st.session_state.use_case_waiting_for_suggestion_selection = True
                
                response_text = "Okay, here are a couple of evidence-backed scenarios based on what you've shared:\n"
                for i, scenario in enumerate(suggestions):
                    response_text += f"{i+1}. {scenario}\n"
                response_text += "\nPlease type the number of the scenario you'd like to select, or describe your own."
                return response_text
            else:
                st.session_state.use_case_suggestions = []
                st.session_state.use_case_waiting_for_suggestion_selection = False
                return "I tried to draft some scenarios, but couldn't come up with any right now. Could you please share your own use case example?"
        # Add more phase-specific examples
        return f"I'm not sure what to suggest for {phase_name.replace('_',' ')} right now. Could you try rephrasing or being more specific about what you need help with?"

    def summarise_intake(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        """
        Summarises the user's input in a structured way, often to confirm understanding.
        """
        # This would typically be used after collecting a piece of information.
        # Example: "So, to confirm, the {phase_name.replace('_', ' ')} you've described is: '{user_input}'. Is that correct?"
        # For now, a simpler confirmation.
        return f"So, for {phase_name.replace('_', ' ')}, you're thinking: '{user_input[:100]}...'. Does that sound right?"

    def get_clarification_prompt(self, user_input: str, phase_name: str = "", reason: str = None, **kwargs) -> str:
        phase_display = phase_name.replace('_', ' ')
        if reason == "validation_failed":
            # Check if it's an intake question that's optional
            if phase_name == "vp_problem_motivation" and not user_input.strip():
                 # This case should ideally be handled by "skip" intent or specific logic in IntakePhase for optional.
                 # If micro_validate failed for an empty optional field, it means the flow needs adjustment.
                 # For now, assume micro_validate=False means we need more.
                 return f"For {phase_display}, if you have something specific, please share. Otherwise, you can say 'skip'. Could you provide more details or rephrase?"
            return f"That seems a bit too brief or generic for {phase_display}. Could you please provide more specific details or a more complete thought?"
        elif reason == "unclear_input":
            return f"I'm not quite sure how to interpret '{user_input[:30]}...' for {phase_display}. Could you try rephrasing or adding more context?"
        elif reason == "awaiting_suggestion_selection": # Specific to use_case
             # Suggestions should be in st.session_state.use_case_suggestions
            suggestions_list = st.session_state.get("use_case_suggestions", [])
            if suggestions_list:
                prompt = "Here are the suggestions again:\n"
                for i, scenario in enumerate(suggestions_list):
                    prompt += f"{i+1}. {scenario}\n"
                prompt += "\nPlease type the number of the scenario you'd like to select, or describe your own."
                return prompt
            else: # Should not happen if waiting_for_suggestion_selection is true
                return f"I expected to have suggestions for you for {phase_display}, but I can't find them. Could you describe your own use case, or ask me to draft new ideas?"

        # Default clarification
        return f"I'm not quite sure I understand that for {phase_display}. Could you please elaborate or rephrase?"

    def get_positive_affirmation_response(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        return "Great! Let's proceed."

    def get_negative_affirmation_response(self, user_input: str, phase_name: str = "", **kwargs) -> str:
        return f"Okay, let's reconsider the {phase_name.replace('_', ' ')} then. What are your thoughts now?"

    def get_skip_confirmation_message(self, phase_name: str, **kwargs) -> str:
        """
        Returns a confirmation message when a user skips a phase/question.
        """
        phase_display = phase_name.replace('_', ' ')
        if phase_name.startswith("vp_"): # For intake sub-questions
             header = kwargs.get("header", phase_display) # IntakePhase might pass header
             return f"Okay, we'll skip the question about '{header}' for now."
        return f"Understood. We'll skip the {phase_display} phase for now and move on."

    def acknowledge_user_input(self, user_input: str, context_description: str = None) -> str:
        """
        Provides a simple acknowledgment of the user's input.
        """
        if context_description:
            return f"Thanks for sharing your thoughts on {context_description}."
        if len(user_input) > 50:
            return f"Thanks for providing that detail: '{user_input[:50]}...'."
        elif user_input:
            return f"Okay, I've noted: '{user_input}'."
        return "Got it."

    # --- Value-Prop Specific Persona Methods (examples, can be expanded) ---

    def create_suggested_use_case(self, scratchpad: dict) -> list[str]:
        """Return 1–2 short evidence-based scenarios using available intake info."""
        suggestions = []
        background = scratchpad.get("vp_background", "")
        interests = scratchpad.get("vp_interests", "")
        problem_motivation = scratchpad.get("vp_problem_motivation", "")

        if background:
            suggestions.append(f"Leveraging your background in {background}, consider a use case where a professional like you addresses [a specific challenge related to your background].")
        if interests:
            suggestions.append(f"Inspired by your interest in {interests}, a potential use case could be developing a tool for individuals passionate about [a related aspect of your interest].")
        if problem_motivation:
            suggestions.append(f"Focusing on your motivation to solve {problem_motivation}, one use case might be a system that directly tackles [a component of that problem].")

        if not suggestions:
            suggestions.append("A general use case: A healthcare provider uses a new tool to improve patient communication.")
            suggestions.append("Another general use case: A patient uses an app to manage their chronic condition more effectively.")
        
        # Return 1 or 2 suggestions
        if len(suggestions) > 2:
            import random
            return random.sample(suggestions, 2)
        elif suggestions:
            return suggestions
        else: # Should not happen with fallbacks
            return ["Could not generate a specific suggestion at this time. Please describe a use case you have in mind."]


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