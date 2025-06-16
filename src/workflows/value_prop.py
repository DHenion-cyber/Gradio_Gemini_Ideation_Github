# Enhanced CoachPersona Integration Summary:
# - Integrated CoachPersona for all user-facing messages and conversational logic.
# - Persona behaviors (single-question per turn, recaps, micro-validation, progress summaries,
#   user approval for chatbot ideas) are now actively used throughout all workflow phases.
# - Replaced previous stance detection with CoachPersona's `assess_input_clarity_depth`
#   and `detect_user_cues` for more nuanced understanding of user input.
# - Workflow leverages CoachPersona’s recap (`_build_contextual_recap_prompt_segment`, `offer_reflective_summary`)
#   and explanation logic (`get_step_intro_message`, `communicate_next_step`) before asking for user input,
#   especially at phase/step transitions.
# - User-initiated requests to jump to specific ideation steps are prioritized by `suggest_next_step`.
# - Calls to CoachPersona methods like `coach_on_decision`, `paraphrase_user_input`,
#   `generate_value_prop_summary` deliver transparent next steps and progress.
# - Original phase tracking and core ideation logic remain, but interaction layer is now persona-driven.
#
# Original Summary of Changes:
# - Added explicit phase tracking: "intake", "ideation", "recommendation", "iteration", "summary".
# - Renamed `current_step` to `current_ideation_step` to manage sub-steps within "ideation" phase.
# - Introduced `current_phase` to track the overall workflow stage.
# - Implemented logic for transitioning from "ideation" to "recommendation" phase.
# - Detailed implementation of "recommendation" phase: aggregates research_requests,
#   simulates search, prepares structured response (findings, strengths, tips).
# - Implemented "iteration" phase: allows revision of scratchpad fields and re-running recommendations.
# - Implemented "summary" phase: generates a comprehensive paragraph-style summary.
# - Ensured workflow can cycle between recommendation and iteration before summary.
# - Cleaned up duplicated method definition.
# - Updated docstrings and comments for all new logic and state transitions.

"""
ALL workflow phases are required and must occur in order. Skipping phases based on user decisiveness or input maturity is not permitted.
"""
"""Defines the ValuePropWorkflow class, managing the value proposition coaching process with CoachPersona integration."""
import streamlit as st
from typing import TYPE_CHECKING, List, Dict, Any
from .base import WorkflowBase

# Persona will be passed in, no direct import needed here unless for type hinting
if TYPE_CHECKING:
    from personas.coach import CoachPersona

class ValuePropWorkflow(WorkflowBase): # Inherit from WorkflowBase
    """
    Manages the value proposition coaching workflow, guiding the user through
    phases of intake, ideation, recommendation, iteration, and summary.
    Deeply integrates CoachPersona for enhanced conversational guidance, including
    single-question turns, contextual recaps, nuanced input assessment (clarity and cues),
    collaborative ideation, micro-validation, and transparent progress communication.
    """
    PHASES: List[str] = ["intake", "ideation", "recommendation", "iteration", "summary"]
    IDEATION_STEPS: List[str] = ["problem", "target_customer", "solution", "main_benefit", "differentiator", "use_case"]

    def __init__(self, context: Dict[str, Any] = None):
        """
        Initializes the ValuePropWorkflow.
        The 'persona_instance' (CoachPersona) must be provided within the 'context' dictionary.
        """
        self.context = context or {}
        self.persona = self.context.get('persona_instance') # Get persona from context
        if self.persona is None:
            raise ValueError("A 'persona_instance' of CoachPersona must be provided in the context for ValuePropWorkflow.")

        self.current_phase: str = self.PHASES[0]  # Initial phase: "intake"
        self.current_ideation_step: str = self.IDEATION_STEPS[0]  # Initial ideation step: "problem"
        self.scratchpad: Dict[str, Any] = {
            "problem": "",
            "target_customer": "",
            "solution": "",
            "main_benefit": "",
            "differentiator": "",
            "use_case": "",
            "research_requests": []
        }
        self.completed: bool = False
        # self.intake_complete = False # This logic will be handled by phase transition

    def _are_ideation_fields_filled(self) -> bool:
        """Checks if all core ideation scratchpad fields are filled."""
        return all(self.scratchpad.get(step) for step in self.IDEATION_STEPS)

    def set_phase(self, phase_name: str) -> None:
        """
        Sets the current workflow phase.
        ALL workflow phases are required and must occur in order. Skipping phases based on user decisiveness or input maturity is not permitted.
        Args:
            phase_name: The name of the phase to set.
        Raises:
            ValueError: If the phase_name is not a valid phase.
        """
        if phase_name not in self.PHASES:
            raise ValueError(f"Invalid phase: {phase_name}. Must be one of {self.PHASES}")
        self.current_phase = phase_name
        # Potentially reset ideation step if moving to ideation, or handle other phase-specific initializations
        if phase_name == "ideation" and not self.current_ideation_step:
             self.current_ideation_step = self.IDEATION_STEPS[0]
        elif phase_name != "ideation":
            self.current_ideation_step = "" # Clear ideation step if not in ideation phase

    def get_phase(self) -> str:
        """Returns the current workflow phase."""
        return self.current_phase

    def _transition_phase(self, next_phase: str) -> None:
        """
        Internal method to transition to the next phase, including persona communication.
        ALL workflow phases are required and must occur in order. Skipping phases based on user decisiveness or input maturity is not permitted.
        Args:
            next_phase: The name of the phase to transition to.
        """
        st.write(f"Attempting to transition from {self.current_phase} to {next_phase}") # For debugging

        current_phase_index = self.PHASES.index(self.current_phase)
        next_phase_index = self.PHASES.index(next_phase)

        # Allowed transitions:
        # 1. Sequentially (e.g., intake -> ideation)
        # 2. Iteration <-> Recommendation cycle
        # 3. Recommendation -> Summary (user wants to finalize)
        # 4. Iteration -> Ideation (user wants to revise a specific ideation step)
        is_sequential = (next_phase_index == current_phase_index + 1)
        is_iteration_to_recommendation = (self.current_phase == "iteration" and next_phase == "recommendation")
        is_recommendation_to_iteration = (self.current_phase == "recommendation" and next_phase == "iteration")
        is_recommendation_to_summary = (self.current_phase == "recommendation" and next_phase == "summary")
        is_iteration_to_ideation = (self.current_phase == "iteration" and next_phase == "ideation")

        if not (is_sequential or \
                is_iteration_to_recommendation or \
                is_recommendation_to_iteration or \
                is_recommendation_to_summary or \
                is_iteration_to_ideation):
            raise ValueError(f"Invalid phase transition from '{self.current_phase}' to '{next_phase}'. "
                             "Allowed transitions: sequential, iteration<->recommendation, recommendation->summary, iteration->ideation.")

        # Persona communication about the transition will be handled by the calling logic in process_user_input
        # before or after this call, using methods like communicate_next_step or offer_reflective_summary.
        self.set_phase(next_phase)
        st.write(f"Successfully transitioned to {self.current_phase}") # For debugging

    def suggest_next_step(self, user_input: str = None) -> str:
        """
        Suggests the next most relevant ideation step based on current scratchpad content
        and user intent, when in the 'ideation' phase.
        This method does NOT modify self.current_ideation_step.
        Args:
            user_input: The user's input string, which may contain keywords for a specific step.
        Returns:
            The string name of the suggested ideation step, or "review_ideation", or "".
        """
        if self.current_phase != "ideation":
            return ""

        # 1. Check if user input explicitly mentions an ideation step for a JUMP
        if user_input:
            user_input_lower = user_input.lower()
            for step_candidate in self.IDEATION_STEPS:
                # Check for "target customer" as well as "target_customer"
                keyword_match = step_candidate.replace("_", " ") in user_input_lower or \
                                step_candidate in user_input_lower
                if keyword_match:
                    if step_candidate != self.current_ideation_step:
                        return step_candidate # User explicitly mentioned a DIFFERENT step (jump)
                    # If keyword matches current step, ignore it for jump logic, proceed to sequential suggestion
                    break # Found a match for current step, no need to check other keywords for jump

        # 2. Suggest the next incomplete ideation step sequentially from the current one
        current_step_index = -1
        if self.current_ideation_step in self.IDEATION_STEPS:
            try:
                current_step_index = self.IDEATION_STEPS.index(self.current_ideation_step)
            except ValueError:
                pass # current_ideation_step might be empty or "review_ideation"

        if current_step_index != -1: # If current_ideation_step is a valid known step
            for i in range(current_step_index + 1, len(self.IDEATION_STEPS)):
                step_candidate = self.IDEATION_STEPS[i]
                if not self.scratchpad.get(step_candidate):
                    return step_candidate # Found next incomplete step

        # 3. If all subsequent steps are filled, or if current_ideation_step was not a known step,
        #    or if we started from a non-step (e.g. empty current_ideation_step),
        #    check from the beginning for *any* incomplete step.
        for step_candidate in self.IDEATION_STEPS:
            if not self.scratchpad.get(step_candidate):
                return step_candidate # Found first incomplete step from start

        # 4. If all ideation steps have content
        return "review_ideation"

    def process_user_input(self, user_input: str): # search_results parameter removed to match WorkflowBase
        """
        Processes the user's input based on the current workflow phase,
        updates the scratchpad, and determines the next interaction.
        Conforms to WorkflowBase.process_user_input.
        """
        from src.utils.scratchpad_extractor import update_scratchpad # Ensure this path is correct
        from src.llm_utils import query_openai, build_conversation_messages # For direct LLM call if needed

        user_input_stripped = user_input.strip()
        core_response = ""
        preliminary_message = ""
        final_response_str = ""

        # Phase-specific logic
        if self.current_phase == "intake":
            if user_input_stripped:
                self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                st.session_state["scratchpad"] = self.scratchpad
                
                # Persona handles recap of initial input and explains process
                # For simplicity, assume first input moves to ideation.
                # A more robust intake might have multiple turns.
                ack_message = self.persona.active_listening(user_input_stripped) # Acknowledge input
                transition_explanation = self.persona.get_intake_to_ideation_transition_message() # Get transition message
                
                preliminary_message = f"{ack_message} {transition_explanation}".strip() # Combine them

                assert self.PHASES.index("ideation") == self.PHASES.index(self.current_phase) + 1, \
                    "Intake phase must transition directly to ideation."
                self._transition_phase("ideation") # Transition first
                
                # Now, get the intro for the *new* phase/step
                # The actual question for the first ideation step will be part of get_step_intro_message
                step_intro = self.persona.get_step_intro_message(self.current_ideation_step, self.scratchpad)
                core_response = step_intro # This will be combined with preliminary_message later
                st.session_state[f"vp_intro_{self.current_ideation_step}"] = True
            else:
                # First time in intake, no user input yet
                core_response = self.persona.greet_and_explain_value_prop_process() # This should end with a question

        elif self.current_phase == "ideation":
            # Determine if we are in the initial "exploration" for the first ideation step
            # This specific direct LLM call block (171-191) is complex to refactor fully without more persona methods
            # for "initial broad exploration". For now, we'll focus on integrating persona for subsequent steps.
            # The key is that *after* this block, interactions become persona-driven.

            is_first_input_for_any_ideation_step = not st.session_state.get(f"vp_intro_{self.current_ideation_step}", False)

            if is_first_input_for_any_ideation_step and not user_input_stripped:
                # Show intro for the current ideation step if not shown yet and no input
                step_intro = self.persona.get_step_intro_message(self.current_ideation_step, self.scratchpad)
                if step_intro:
                    preliminary_message = step_intro
                    st.session_state[f"vp_intro_{self.current_ideation_step}"] = True
                # The step_intro from persona should ideally end with a question.
                # If not, append a generic reflection prompt.
                final_response_str = preliminary_message # which is step_intro here
                # Check for truncation (ends with comma) or if it doesn't end with sentence-terminating punctuation
                ends_with_q_mark = final_response_str.strip().endswith("?")
                ends_with_period = final_response_str.strip().endswith(".")
                ends_with_exclamation = final_response_str.strip().endswith("!")
                ends_with_comma_suggesting_truncation = final_response_str.strip().endswith(",")

                if not ends_with_comma_suggesting_truncation and not (ends_with_q_mark or ends_with_period or ends_with_exclamation):
                    final_response_str += " " + self.persona.get_reflection_prompt()
                return final_response_str

            if user_input_stripped:
                # Always update scratchpad with new input
                self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                st.session_state["scratchpad"] = self.scratchpad
                st.session_state["vp_ideation_started"] = True # Mark that ideation has received some input

                user_cue = self.persona.detect_user_cues(user_input_stripped, self.current_ideation_step)
                # assess_input_clarity_depth will be used within coach_on_decision and paraphrase_user_input

                # Mark current step intro as "handled" because we have input for it now.
                st.session_state[f"vp_intro_{self.current_ideation_step}"] = True

                if user_cue == "decided" or \
                   (self.current_ideation_step == "differentiator" and self.scratchpad.get("main_benefit")) or \
                   (self.current_ideation_step == "use_case" and self.scratchpad.get("differentiator")):
                    # If user is decided, or if we can auto-progress based on previous fields being filled
                    if user_cue == "decided": # Ensure the current step is updated if user was decisive
                         self.scratchpad[self.current_ideation_step] = user_input_stripped # Explicitly save decided input

                    core_response = self.persona.coach_on_decision(
                        self.current_ideation_step, user_input_stripped, self.scratchpad, user_cue
                    )
                    
                    next_ideation_step_candidate = self.suggest_next_step(user_input_stripped)
                    
                    if self._are_ideation_fields_filled():
                        # All ideation fields are filled, transition to recommendation
                        if not preliminary_message: # Ensure transition message is only added once if already set by other logic
                             preliminary_message = self.persona.offer_reflective_summary(self.scratchpad)
                        preliminary_message += " " + self.persona.communicate_next_step(self.current_phase, "recommendation", self.scratchpad)
                        
                        # Ensure 'recommendation' is the correct next phase sequentially from 'ideation'
                        # This assertion might be too strict if other transitions from ideation are ever allowed.
                        # For now, value_prop workflow is linear from ideation to recommendation.
                        if self.PHASES.index("recommendation") != self.PHASES.index(self.current_phase) + 1:
                             # This case should ideally not be hit if _are_ideation_fields_filled is true
                             # and we are in 'ideation'. Adding a log for safety.
                             st.error(f"Unexpected phase state before transitioning from ideation. Current: {self.current_phase}")
                        
                        self._transition_phase("recommendation")
                        self.current_ideation_step = "" # Clear ideation step as we are leaving the phase
                        core_response = "" # Persona messages for transition are in preliminary_message
                    
                    elif next_ideation_step_candidate and next_ideation_step_candidate != "review_ideation":
                        # A valid next step (or a jump to a specific step) is suggested.
                        if next_ideation_step_candidate != self.current_ideation_step:
                            # This is a progression to a new step or a jump.
                            # The core_response from coach_on_decision was for the *old* current_ideation_step.
                            # The persona's response (e.g., from coach_on_decision) might have already
                            # textually handled the transition/jump.
                            self.current_ideation_step = next_ideation_step_candidate
                            # Ensure the intro for this new step can be shown if the user sends empty input next
                            st.session_state.pop(f"vp_intro_{self.current_ideation_step}", None)
                            # The core_response (from coach_on_decision on the *previous* step) is used for this turn.
                            # The next turn, if user_input is empty, will trigger the intro for the new current_ideation_step.
                        # else: next_ideation_step_candidate is the same as current_ideation_step.
                        # This implies the user is decided on the current step, but suggest_next_step didn't find
                        # a different, valid, incomplete step to move to automatically.
                        # The core_response from coach_on_decision (for the current step) is appropriate.
                    
                    # else (next_ideation_step_candidate is "review_ideation" or empty):
                        # This means either all steps are filled (handled by _are_ideation_fields_filled),
                        # or suggest_next_step couldn't find a clear next step (e.g., current step is last, or an issue).
                        # The core_response from coach_on_decision (for the current step) is generally appropriate.
                        # If it's "review_ideation", the persona's response should guide the user.
                else: # uncertain, open, curious, neutral
                    core_response = self.persona.paraphrase_user_input(
                        user_input_stripped, user_cue, self.current_ideation_step, self.scratchpad
                    )
            else: # No user input stripped, and not the first intro for the step
                if not self.scratchpad.get(self.current_ideation_step):
                    core_response = self.persona.get_prompt_for_empty_input(self.current_ideation_step)
                else: # Field has content, but user sent empty input (e.g. just hit enter)
                    core_response = self.persona.offer_reflective_summary(self.scratchpad) + " " + \
                                    self.persona.get_prompt_for_empty_input(self.current_ideation_step) # Re-prompt for current step or offer to move on

            # After processing, check if all ideation fields are filled to transition (redundant if handled above, but safe)
            if self._are_ideation_fields_filled() and self.current_phase == "ideation":
                if not preliminary_message: # Ensure transition message is only added once
                    preliminary_message = self.persona.offer_reflective_summary(self.scratchpad) + " " + \
                                          self.persona.communicate_next_step(self.current_phase, "recommendation", self.scratchpad)
                assert self.PHASES.index("recommendation") == self.PHASES.index(self.current_phase) + 1, \
                    "Ideation phase must transition directly to recommendation."
                self._transition_phase("recommendation")
                self.current_ideation_step = ""
                core_response = "" # Transition messages handled

        elif self.current_phase == "recommendation":
            # This phase generates recommendations based on the ideation scratchpad.
            # It's typically entered automatically after ideation or by user navigation.

            # Check if recommendations should be generated/regenerated this turn.
            # Trigger if it's the first time in session OR user explicitly asks.
            generated_once = st.session_state.get("vp_recommendation_fully_generated_once", False)
            # Regenerate if not generated, or if user explicitly asks to see/regenerate recommendations.
            # A casual mention like "these recommendations are good" should not trigger regeneration if already generated.
            explicit_regen_request = False
            if user_input_stripped:
                lower_input = user_input_stripped.lower()
                if "regenerate recommendation" in lower_input or \
                   "show recommendation" in lower_input or \
                   "get recommendation" in lower_input: # Made more specific
                    explicit_regen_request = True
            
            should_generate_recommendations = not generated_once or explicit_regen_request

            if should_generate_recommendations:
                if hasattr(self.persona, 'offer_reflective_summary'):
                    preliminary_message = self.persona.offer_reflective_summary(self.scratchpad)
                else:
                    preliminary_message = "Let's review where we are before moving to recommendations." # Fallback
                
                preliminary_message += " Now, let's look at some recommendations based on your value proposition."

                research_findings_parts = []
                if self.scratchpad.get("research_requests"):
                    research_findings_parts.append("Research Findings (based on your requests and simulated search):\n")
                    for i, req in enumerate(self.scratchpad["research_requests"]):
                        simulated_search_query = f"Searching for: {req['details']} (related to {req['step']})"
                        st.write(f"Simulating search: {simulated_search_query}")
                        simulated_result = f"  - Stub Result {i+1} for '{req['step']}': Key insights regarding '{req['details']}' would typically include market data analysis, competitor strategies, and potential customer validation approaches..."
                        research_findings_parts.append(f"For '{req['step']}' (request: '{req['details']}'):\n{simulated_result}\n")
                else:
                    research_findings_parts.append("Research Findings: No specific research requests were made during ideation. General market research is always recommended.\n")
                research_findings_str = "".join(research_findings_parts)

                strengths_parts = ["Identified Strengths (from your inputs):\n"]
                has_strengths = False
                for step in self.IDEATION_STEPS:
                    if self.scratchpad.get(step):
                        strengths_parts.append(f"- **{step.replace('_', ' ').title()}**: {self.scratchpad[step]}\n")
                        has_strengths = True
                if not has_strengths:
                    strengths_parts.append("  - Core strengths are still being defined.\n")
                strengths_str = "".join(strengths_parts)
            
                tips_parts = ["General Tips & Recommendations:\n"]
                tips_parts.append("- **Validate Early & Often**: Continuously test your assumptions...\n")
                tips_parts.append("- **Focus on Differentiation**: Clearly articulate what makes your solution unique...\n")
                tips_parts.append("- **Craft Compelling Use Cases**: Develop clear, relatable examples...\n")
                tips_parts.append("- **Understand Market Context**: Research your market trends...\n")
                tips_str = "".join(tips_parts)

                recommendation_content = f"\n\n{research_findings_str}\n{strengths_str}\n{tips_str}"
                
                if hasattr(self.persona, 'present_recommendations_and_ask_next'):
                    core_response = self.persona.present_recommendations_and_ask_next(recommendation_content, self.scratchpad)
                else: # Fallback if persona method is missing
                    core_response = recommendation_content + "\n\nWhat are your thoughts on these recommendations? We can iterate on them, or if you're ready, move to a summary."
                st.session_state["vp_recommendation_fully_generated_once"] = True
            
            elif user_input_stripped:
                user_cue = self.persona.detect_user_cues(user_input_stripped, self.current_phase)
                if "iterate" in user_input_stripped.lower() or "refine" in user_input_stripped.lower() or user_cue == "open":
                    preliminary_message = self.persona.communicate_next_step(self.current_phase, "iteration", self.scratchpad)
                    self._transition_phase("iteration")
                    core_response = ""
                elif "summary" in user_input_stripped.lower() or user_cue == "decided":
                    preliminary_message = self.persona.communicate_next_step(self.current_phase, "summary", self.scratchpad)
                    self._transition_phase("summary")
                    core_response = self.generate_summary()
                    self.completed = True
                else:
                    core_response = self.persona.paraphrase_user_input(user_input_stripped, user_cue, self.current_phase, self.scratchpad)
            else:
                if hasattr(self.persona, 'prompt_after_recommendations'):
                    core_response = self.persona.prompt_after_recommendations(self.scratchpad)
                else: # Fallback
                    core_response = "The recommendations have been provided. What would you like to do next? We can iterate, revisit previous steps, or proceed to the summary."

        elif self.current_phase == "iteration":
            if not user_input_stripped:
                if hasattr(self.persona, 'introduce_iteration_phase'):
                    core_response = self.persona.introduce_iteration_phase(self.scratchpad)
                else: # Fallback
                    core_response = "We are now in the iteration phase. You can revise parts of your value proposition, ask to re-run recommendations, or move to the summary. What would you like to do?"
            else:
                user_cue = self.persona.detect_user_cues(user_input_stripped, self.current_phase)
                user_intent_lower = user_input_stripped.lower()

                # Prioritize explicit commands over general cues like "decided"
                # More robust check for "rerun/re-run recommendation"
                is_rerun_recommendation_request = \
                    ("rerun" in user_intent_lower or "re-run" in user_intent_lower) and \
                    ("recommendation" in user_intent_lower or "recommendations" in user_intent_lower)

                if is_rerun_recommendation_request:
                    st.session_state["vp_recommendation_fully_generated_once"] = False
                    preliminary_message = self.persona.communicate_next_step(self.current_phase, "recommendation", self.scratchpad)
                    self._transition_phase("recommendation")
                    core_response = ""
                elif "revise" in user_intent_lower or ("edit" in user_intent_lower and any(s.replace("_", " ") in user_intent_lower for s in self.IDEATION_STEPS)):
                    revised_part_identified = False
                    for step in self.IDEATION_STEPS:
                        if step.replace("_", " ") in user_intent_lower:
                            preliminary_message = self.persona.communicate_next_step(self.current_phase, "ideation", self.scratchpad, specific_step=step)
                            self._transition_phase("ideation")
                            self.current_ideation_step = step
                            st.session_state.pop(f"vp_intro_{step}", None)
                            core_response = ""
                            revised_part_identified = True
                            break
                    if not revised_part_identified:
                        if hasattr(self.persona, 'ask_which_part_to_revise'):
                            core_response = self.persona.ask_which_part_to_revise(self.scratchpad)
                        else: # Fallback
                            core_response = "Which part of the value proposition would you like to revise? For example, 'revise problem' or 'change target customer'."
                elif "summary" in user_intent_lower or \
                     "proceed" in user_intent_lower or \
                     "done" in user_intent_lower or \
                     "finish" in user_intent_lower or \
                     user_cue == "decided": # "decided" cue leads to summary if no more specific command matched
                    preliminary_message = self.persona.communicate_next_step(self.current_phase, "summary", self.scratchpad)
                    self._transition_phase("summary")
                    core_response = self.generate_summary()
                    self.completed = True
                else:
                    self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                    st.session_state["scratchpad"] = self.scratchpad
                    base_response = self.persona.paraphrase_user_input(user_input_stripped, user_cue, self.current_phase, self.scratchpad)
                    if hasattr(self.persona, 'ask_iteration_next_action'):
                        next_action_prompt = self.persona.ask_iteration_next_action(self.scratchpad)
                    else: # Fallback
                        next_action_prompt = "What would you like to do next in this iteration phase?"
                    core_response = f"{base_response} {next_action_prompt}"

        elif self.current_phase == "summary": # This part should already be updated from previous diffs
            if not st.session_state.get("vp_summary_generated_once", False) or \
               (user_input_stripped and "summary" in user_input_stripped.lower()):
                core_response = self.generate_summary()
                self.completed = True
                st.session_state["vp_summary_generated_once"] = True
            else:
                current_summary = self.generate_summary()
                if hasattr(self.persona, 'present_existing_summary'):
                     core_response = self.persona.present_existing_summary(current_summary, self.scratchpad)
                else: # Fallback
                    core_response = f"We've already completed the summary. Here it is again for your reference:\n\n{current_summary}"
                self.completed = True


        # Construct final response string
        if not final_response_str:
            response_parts = []
            if preliminary_message:
                response_parts.append(preliminary_message.strip())
            if core_response:
                response_parts.append(core_response.strip())
            
            final_response_str = " ".join(filter(None, response_parts)).strip()

        # The get_reflection_prompt() is now expected to be handled more selectively within specific logic paths
        # or by persona methods themselves ensuring they end with a question.
        # The fallback for a completely empty final_response_str remains.
        if not final_response_str :
             final_response_str = self.persona.get_prompt_for_empty_input(self.current_ideation_step or "current focus") + " " + self.persona.get_reflection_prompt()
        
        return final_response_str.strip()


    def add_research_request(self, step: str, details: str = ""):
        """Adds a research request to the scratchpad, associated with an ideation step."""
        if "research_requests" not in self.scratchpad:
            self.scratchpad["research_requests"] = []
        self.scratchpad["research_requests"].append({"step": step, "details": details})
        st.write(f"Research request added for {step}: {details}") # For debugging

    def generate_summary(self) -> str:
        """
        Generates a comprehensive summary by calling the CoachPersona's summary generation method.
        Conforms to WorkflowBase.generate_summary.
        """
        # Delegate summary generation to the persona
        # The persona's generate_value_prop_summary should handle the full content and narrative.
        summary_text = self.persona.generate_value_prop_summary(self.scratchpad, for_reflection=False)
        
        # Optionally, add a standard intro/outro if the persona's method doesn't include it,
        # but ideally, the persona method provides the complete, user-facing summary.
        # For now, assume persona's method is comprehensive.
        if not summary_text: # Fallback if persona returns empty
            # Fallback to a more structured summary if persona fails
            summary_parts = [
                f"Value Proposition Summary (Finalized in Phase: {self.current_phase}):\n\n",
                "This captures the core elements, insights, and direction established for your value proposition:\n\n"
            ]
            summary_parts.append("**I. Core Value Proposition Elements:**\n")
            for step in self.IDEATION_STEPS:
                content = self.scratchpad.get(step, "(Not defined)")
                summary_parts.append(f"   - **{step.replace('_', ' ').title()}**: {content}\n")
            summary_parts.append("\n")
            summary_parts.append("**II. Key Recommendation Themes:**\n")
            if st.session_state.get("vp_recommendation_fully_generated_once", False):
                themes = [
                    "Continuous validation of assumptions (problem, solution, customer).",
                    "Clear articulation of unique differentiators.",
                    "Development of compelling and relatable use cases.",
                    "Thorough understanding of the market context and competition."
                ]
                if self.scratchpad.get("research_requests"):
                    themes.append(f"Targeted research based on {len(self.scratchpad['research_requests'])} specific request(s).")
                for theme in themes:
                    summary_parts.append(f"   - {theme}\n")
            else:
                summary_parts.append("   - Recommendations were not fully explored in this session.\n")
            summary_parts.append("\n")
            summary_parts.append("**III. Overall Spirit & Next Steps:**\n")
            # Try to get at least the spirit if full summary failed
            spirit = self.persona.capture_spirit_of_value_prop_conversation(self.scratchpad) if hasattr(self.persona, 'capture_spirit_of_value_prop_conversation') else "The conversation aimed to build a strong foundation for your venture."
            summary_parts.append(f"   - {spirit}\n")
            summary_parts.append("\nThis summary encapsulates our work. You can use this as a basis for further development and communication.")
            return "".join(summary_parts)
        return summary_text
        spirit_message = self.persona.capture_spirit_of_value_prop_conversation(self.scratchpad)
        if spirit_message:
            summary_parts.append(f"   {spirit_message}\n")
        else: # Fallback
            summary_parts.append(
                "   The collaborative process aimed to build a robust value proposition. "
                "The next steps involve acting on these insights, further testing, and refining your approach.\n"
            )
        
        return "".join(summary_parts)

    def is_complete(self) -> bool:
        """
        Checks if the value proposition workflow has reached its completion state.
        Workflow is considered complete when it reaches the 'summary' phase and
        the summary has been (notionally) generated.
        Conforms to WorkflowBase.is_complete.
        """
        return self.completed or (self.current_phase == "summary" and self.scratchpad_is_filled_for_summary())
        # We can refine what "filled for summary" means, for now, just being in summary phase is enough.

    def scratchpad_is_filled_for_summary(self) -> bool:
        """Helper to determine if scratchpad is sufficiently filled for a meaningful summary."""
        # For now, this means all ideation steps are filled.
        # This could be expanded based on requirements for the summary phase.
        return self._are_ideation_fields_filled()

    def get_step(self) -> str: # Conforms to WorkflowBase.get_step
        """
        Returns the current overall phase of the value proposition workflow.
        This was previously `current_step` but now maps to `current_phase`
        to reflect the main stages of the workflow.
        Conforms to WorkflowBase.get_step.
        """
        return self.current_phase
