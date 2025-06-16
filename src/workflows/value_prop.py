# Summary of Changes:
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
"""Defines the ValuePropWorkflow class, managing the value proposition coaching process."""
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
        Internal method to transition to the next phase.
        ALL workflow phases are required and must occur in order. Skipping phases based on user decisiveness or input maturity is not permitted.
        Args:
            next_phase: The name of the phase to transition to.
        """
        # Add any logic needed before transitioning (e.g., logging, validation)
        st.write(f"Transitioning from {self.current_phase} to {next_phase}") # For debugging

        # ALL workflow phases are required and must occur in order.
        # Skipping phases based on user decisiveness or input maturity is not permitted.
        current_phase_index = self.PHASES.index(self.current_phase)
        next_phase_index = self.PHASES.index(next_phase)

        if next_phase_index != current_phase_index + 1 and \
           not (self.current_phase == "iteration" and next_phase == "recommendation") and \
           not (self.current_phase == "recommendation" and next_phase == "iteration"):
            raise ValueError(f"Invalid phase transition from '{self.current_phase}' to '{next_phase}'. "
                             "Phases must proceed sequentially, or cycle between recommendation/iteration.")

        self.set_phase(next_phase)
        # Add any logic needed after transitioning (e.g., sending a message to the user)

    def suggest_next_step(self, user_input: str = None) -> str:
        """
        Suggests the next most relevant ideation step based on current scratchpad content
        and user intent, when in the 'ideation' phase.
        Allow user to revisit or expand previous steps if desired.
        """
        if self.current_phase != "ideation":
            return "" # Only suggest ideation steps during ideation phase

        # If the user input clearly refers to a previous or later ideation step, honor that
        if user_input:
            for step in self.IDEATION_STEPS:
                if step in user_input.lower(): # Simple keyword matching
                    self.current_ideation_step = step
                    return step
        # Otherwise, suggest the next incomplete ideation step
        for step in self.IDEATION_STEPS:
            if not self.scratchpad.get(step):
                self.current_ideation_step = step
                return step
        # If all ideation steps have content, ideation might be complete or user can review
        self.current_ideation_step = "review_ideation" # A special step to indicate review within ideation
        return "review_ideation"

    def process_user_input(self, user_input: str): # search_results parameter removed to match WorkflowBase
        """
        Processes the user's input based on the current workflow phase,
        updates the scratchpad, and determines the next interaction.
        Conforms to WorkflowBase.process_user_input.
        """
        from utils.scratchpad_extractor import update_scratchpad # Ensure this path is correct
        from llm_utils import query_openai, build_conversation_messages # For direct LLM call if needed

        user_input_stripped = user_input.strip()
        core_response = ""
        preliminary_message = ""
        final_response_str = ""

        # Phase-specific logic
        if self.current_phase == "intake":
            # Initial interaction, gather basic idea.
            # For now, assume persona handles the initial greeting and prompt.
            # If user provides input, update scratchpad (e.g., problem or general idea)
            if user_input_stripped:
                self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                st.session_state["scratchpad"] = self.scratchpad
                # Persona might ask clarifying questions or confirm understanding.
                # For simplicity, we'll transition after first input.
                core_response = self.persona.greet_and_explain_value_prop_process() # Assuming persona has such a method
                # Enforce: intake MUST transition to ideation.
                assert self.PHASES.index("ideation") == self.PHASES.index(self.current_phase) + 1, \
                    "Intake phase must transition directly to ideation."
                self._transition_phase("ideation")
                preliminary_message = self.persona.get_intake_to_ideation_transition_message()
            else:
                # First time in intake, no user input yet
                core_response = self.persona.greet_and_explain_value_prop_process() # Or a specific intake prompt

        elif self.current_phase == "ideation":
            # Logic for guiding through IDEATION_STEPS
            # This section adapts the original process_user_input logic for the ideation phase.

            # Determine if we are in the initial "exploration" for the first ideation step
            is_initial_ideation_exploration = (self.current_ideation_step == self.IDEATION_STEPS[0] and \
                                               not self.scratchpad.get(self.IDEATION_STEPS[0]) and \
                                               not st.session_state.get("vp_ideation_started", False))

            if is_initial_ideation_exploration and user_input_stripped:
                self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                st.session_state["scratchpad"] = self.scratchpad
                st.session_state["vp_ideation_started"] = True # Mark that ideation has received first input

                try:
                    # Using "exploration" for LLM context as it's the start of filling fields
                    messages_for_llm = build_conversation_messages(
                        scratchpad=self.scratchpad,
                        latest_user_input=user_input_stripped,
                        current_phase="exploration" # This was the original phase name for this LLM call
                    )
                    core_response = query_openai(messages=messages_for_llm)
                    if not core_response or not core_response.strip():
                        core_response = "I'm processing that. Could you tell me a bit more, or perhaps we can explore another angle?"
                except Exception as e:
                    core_response = f"I encountered an issue during exploration: {e}. Could you please try rephrasing?"
            else: # Not initial exploration for the very first step, or no user input for it.
                  # Proceed with step-specific logic for current_ideation_step.

                # 1. Handle dedicated ideation step introductions
                #    The get_intake_to_ideation_transition_message is now handled at phase transition.
                #    We need a way to introduce each ideation step if it's new.
                if not st.session_state.get(f"vp_intro_{self.current_ideation_step}", False):
                    step_intro = self.persona.get_step_intro_message(self.current_ideation_step, self.scratchpad)
                    if step_intro:
                        preliminary_message = step_intro
                        st.session_state[f"vp_intro_{self.current_ideation_step}"] = True # Mark intro as shown
                        if not user_input_stripped: # If only showing intro, add reflection and return
                            final_response_str = preliminary_message + self.persona.get_reflection_prompt()
                            return final_response_str

                if preliminary_message and not user_input_stripped and not final_response_str:
                     final_response_str = preliminary_message + self.persona.get_reflection_prompt()
                     return final_response_str


                # 2. Handle empty user input for current ideation step
                if not user_input_stripped:
                    if not self.scratchpad.get(self.current_ideation_step): # and self.current_ideation_step != "problem":
                        core_response = self.persona.get_prompt_for_empty_input(self.current_ideation_step)
                else: # user_input_stripped is NOT empty
                    stance = self.persona.detect_user_stance(user_input_stripped, self.current_ideation_step)
                    effective_stance = stance

                    if stance == "decided":
                        self.scratchpad[self.current_ideation_step] = user_input_stripped
                    # Simplified logic for auto-filling next steps based on previous ones
                    elif self.current_ideation_step == "differentiator" and self.scratchpad.get("main_benefit") and not self.scratchpad.get("differentiator"):
                        self.scratchpad["differentiator"] = user_input_stripped
                        effective_stance = "decided"
                    elif self.current_ideation_step == "use_case" and self.scratchpad.get("differentiator") and not self.scratchpad.get("use_case"):
                        self.scratchpad["use_case"] = user_input_stripped
                        effective_stance = "decided"
                    
                    self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                    st.session_state["scratchpad"] = self.scratchpad

                    if effective_stance == "decided":
                        core_response = self.persona.coach_on_decision(
                            self.current_ideation_step, user_input_stripped, self.scratchpad, effective_stance
                        )
                        # Suggest next ideation step or check for completion
                        next_ideation_step_candidate = self.suggest_next_step() # Don't pass user_input here to get next logical step
                        if self._are_ideation_fields_filled():
                            # Enforce: ideation MUST transition to recommendation.
                            assert self.PHASES.index("recommendation") == self.PHASES.index(self.current_phase) + 1, \
                                "Ideation phase must transition directly to recommendation."
                            self._transition_phase("recommendation")
                            # The message for transition to recommendation will be handled in the next cycle or by persona
                            preliminary_message += "\n\nGreat! We've filled out the core aspects of your value proposition. Let's move on to recommendations."
                            self.current_ideation_step = "" # Clear ideation step
                        elif next_ideation_step_candidate and next_ideation_step_candidate != "review_ideation":
                             self.current_ideation_step = next_ideation_step_candidate
                             # No explicit message here, next iteration will show step intro
                        # else: stay on current step or review
                    else: # uncertain, open, interest, neutral
                        core_response = self.persona.paraphrase_user_input(
                            user_input_stripped, stance, self.current_ideation_step, self.scratchpad
                        )
            
            # After processing, check if all ideation fields are filled to transition
            if self._are_ideation_fields_filled() and self.current_phase == "ideation": # Check phase again in case it changed
                # Enforce: ideation MUST transition to recommendation.
                assert self.PHASES.index("recommendation") == self.PHASES.index(self.current_phase) + 1, \
                    "Ideation phase must transition directly to recommendation."
                self._transition_phase("recommendation")
                # Add a message indicating transition, if not already handled
                if "Great! We've filled out the core aspects" not in (preliminary_message + core_response) and \
                   "All core value proposition fields are now complete" not in (preliminary_message + core_response):
                    transition_msg = "\n\nAll core value proposition fields are now complete. Moving to the recommendation phase."
                    core_response = (core_response + transition_msg) if core_response else transition_msg


        elif self.current_phase == "recommendation":
            # This phase generates recommendations based on the ideation scratchpad.
            # It's typically entered automatically after ideation or by user navigation.

            # Check if recommendations should be generated/regenerated this turn.
            # Trigger if it's the first time in session OR user explicitly asks.
            should_generate_recommendations = not st.session_state.get("vp_recommendation_fully_generated_once", False) or \
                                             (user_input_stripped and "recommendation" in user_input_stripped.lower())

            if should_generate_recommendations:
                preliminary_message = "Now, let's look at some recommendations based on your value proposition."

                # A. Research Findings (Aggregated from research_requests and stubbed search)
                research_findings_parts = []
                if self.scratchpad.get("research_requests"):
                    research_findings_parts.append("Research Findings (based on your requests and simulated search):\n")
                    for i, req in enumerate(self.scratchpad["research_requests"]):
                        # In a real scenario, this would call an external search API (e.g., Perplexity)
                        # For now, we simulate the search and result.
                        simulated_search_query = f"Searching for: {req['details']} (related to {req['step']})"
                        st.write(f"Simulating search: {simulated_search_query}") # Debugging
                        
                        # Stubbed search result
                        simulated_result = f"  - Stub Result {i+1} for '{req['step']}': Key insights regarding '{req['details']}' would typically include market data analysis, competitor strategies, and potential customer validation approaches. For example, if researching '{req['details']}', one might find data on adoption rates, common pain points identified by early adopters, or existing solutions and their gaps."
                        research_findings_parts.append(f"For '{req['step']}' (request: '{req['details']}'):\n{simulated_result}\n")
                else:
                    research_findings_parts.append("Research Findings: No specific research requests were made during ideation. General market research on your problem and solution space is always recommended.\n")
                research_findings_str = "".join(research_findings_parts)

                # B. Strengths (Derived from filled ideation steps in scratchpad)
                strengths_parts = ["Identified Strengths (from your inputs):\n"]
                has_strengths = False
                for step in self.IDEATION_STEPS:
                    if self.scratchpad.get(step):
                        strengths_parts.append(f"- **{step.replace('_', ' ').title()}**: {self.scratchpad[step]}\n")
                        has_strengths = True
                if not has_strengths:
                    strengths_parts.append("  - Core strengths are still being defined. Completing all ideation steps will help clarify these.\n")
                strengths_str = "".join(strengths_parts)
            
                # C. Tips & Recommendations (General advice, can be enhanced by persona)
                tips_parts = ["General Tips & Recommendations:\n"]
                tips_parts.append("- **Validate Early & Often**: Continuously test your assumptions about the problem, solution, and target customer with real users. Consider creating a Minimum Viable Product (MVP).\n")
                tips_parts.append("- **Focus on Differentiation**: Clearly articulate what makes your solution unique and better than alternatives. This should be a core part of your messaging and branding.\n")
                tips_parts.append("- **Craft Compelling Use Cases**: Develop clear, relatable examples of how customers will use your product/service and the specific benefits they'll gain. Storytelling can be powerful here.\n")
                tips_parts.append("- **Understand Market Context**: Research your market to understand trends, competition, and opportunities for positioning. Identify your Total Addressable Market (TAM).\n")
                if self.scratchpad.get("target_customer"):
                     tips_parts.append(f"- **Engage Your Target Customer ('{self.scratchpad['target_customer']}')**: Seek direct feedback through surveys, interviews, or usability tests. Build relationships with your intended audience to foster loyalty and gather insights.\n")
                if self.scratchpad.get("solution"):
                    tips_parts.append(f"- **Refine Your Solution ('{self.scratchpad['solution']}')**: Based on feedback and further research, be prepared to iterate on your solution to better meet customer needs.\n")

                tips_str = "".join(tips_parts)

                core_response = f"\n\n{research_findings_str}\n{strengths_str}\n{tips_str}"
                core_response += "\n\nWhat would you like to do next? We can iterate on these points, revisit other areas of your value proposition, or move to a summary."
                st.session_state["vp_recommendation_fully_generated_once"] = True # Mark as generated
            
            elif user_input_stripped:
                # Handle follow-up questions or requests to iterate after recommendations have been shown.
                if "iterate" in user_input_stripped.lower() or "refine" in user_input_stripped.lower():
                    # Enforce: recommendation can transition to iteration (cycle).
                    assert self.PHASES.index("iteration") == self.PHASES.index(self.current_phase) + 1 or \
                           self.PHASES.index("iteration") == self.PHASES.index(self.current_phase) - 1, \
                        "Recommendation phase must transition to iteration or summary."
                    self._transition_phase("iteration")
                    preliminary_message = "Okay, let's iterate on your value proposition. What specific aspects would you like to focus on or refine based on the recommendations or your own thoughts?"
                    core_response = "" # Reset core_response as preliminary_message covers the transition.
                elif "summary" in user_input_stripped.lower():
                    # Enforce: recommendation can transition to summary.
                    assert self.PHASES.index("summary") == self.PHASES.index(self.current_phase) + 1, \
                        "Recommendation phase must transition to iteration or summary."
                    self._transition_phase("summary")
                    preliminary_message = "Alright, let's move to the summary of your value proposition."
                    core_response = self.generate_summary() # Generate summary immediately on transition
                    self.completed = True
                else: # General comment or question about recommendations
                    # Persona could provide more nuanced handling here.
                    core_response = f"Regarding your input: '{user_input_stripped}'. We can discuss this further, make adjustments, or if you're ready, move to the summary. What are your thoughts?"
            else:
                # No user input, and recommendations were already shown. Prompt for next action.
                core_response = "The recommendations have been provided. What would you like to do next? We can iterate, revisit previous steps, or proceed to the summary."

        elif self.current_phase == "iteration":
            # This phase allows the user to revise scratchpad fields or re-run recommendations.
            if not user_input_stripped: # First entry or no specific input
                core_response = (
                    "We are now in the iteration phase. Based on the recommendations or any new thoughts, "
                    "would you like to:\n"
                    "1. Revise any part of your value proposition (e.g., problem, solution)?\n"
                    "2. Re-run the recommendations?\n"
                    "3. Proceed to the final summary?\n"
                    "Please let me know what you'd like to do (e.g., 'revise solution', 'rerun recommendations', 'go to summary')."
                )
            else:
                # Process user feedback for iteration
                user_intent_lower = user_input_stripped.lower()

                if "revise" in user_intent_lower:
                    # Attempt to identify which part to revise
                    revised_part_identified = False
                    for step in self.IDEATION_STEPS:
                        if step.replace("_", " ") in user_intent_lower:
                            # Enforce: iteration can transition back to ideation for revision.
                            assert self.PHASES.index("ideation") == self.PHASES.index(self.current_phase) - 2, \
                                "Iteration phase must transition to ideation, recommendation, or summary."
                            self._transition_phase("ideation")
                            self.current_ideation_step = step
                            # Clear intro flag for this step to allow re-introduction by persona
                            st.session_state.pop(f"vp_intro_{step}", None)
                            preliminary_message = f"Okay, let's revise the '{step.replace('_', ' ')}'. What are your new thoughts on this?"
                            revised_part_identified = True
                            break
                    if not revised_part_identified:
                        core_response = "Which part of the value proposition would you like to revise? For example, 'revise problem' or 'change target customer'."
                    else:
                        core_response = "" # Preliminary message will cover it.
                
                elif "rerun recommendation" in user_intent_lower or "re-run recommendation" in user_intent_lower:
                    st.session_state["vp_recommendation_fully_generated_once"] = False # Allow regeneration
                    # Enforce: iteration can transition to recommendation (cycle).
                    assert self.PHASES.index("recommendation") == self.PHASES.index(self.current_phase) - 1, \
                        "Iteration phase must transition to ideation, recommendation, or summary."
                    self._transition_phase("recommendation")
                    preliminary_message = "Alright, I'll prepare a new set of recommendations based on the current state of your value proposition."
                    core_response = "" # Recommendation phase will generate its own content.
                
                elif "summary" in user_intent_lower or "proceed" in user_intent_lower or "done" in user_intent_lower or "finish" in user_intent_lower:
                    # Enforce: iteration can transition to summary.
                    assert self.PHASES.index("summary") == self.PHASES.index(self.current_phase) + 1, \
                        "Iteration phase must transition to ideation, recommendation, or summary."
                    self._transition_phase("summary")
                    preliminary_message = "Great! Let's move to the final summary of your value proposition."
                    # Generate summary immediately upon transitioning
                    core_response = self.generate_summary()
                    self.completed = True
                
                else: # General input, potentially updating scratchpad or asking for clarification
                    self.scratchpad = update_scratchpad(user_input_stripped, self.scratchpad.copy())
                    st.session_state["scratchpad"] = self.scratchpad
                    core_response = (
                        f"I've noted: '{user_input_stripped}'. "
                        "You can revise specific parts, rerun recommendations, or proceed to summary. What's next?"
                    )

        elif self.current_phase == "summary":
            # This phase generates the final summary.
            if not st.session_state.get("vp_summary_generated_once", False) or \
               (user_input_stripped and "summary" in user_input_stripped.lower()): # If user explicitly asks for summary again
                
                summary_parts = [
                    "Final Value Proposition Summary:\n\n",
                    "Throughout our conversation, we've explored and defined key aspects of your value proposition. Here's a consolidated overview:\n\n"
                ]

                # 1. Scratchpad Elements
                summary_parts.append("**Core Value Proposition Elements:**\n")
                for step in self.IDEATION_STEPS:
                    if self.scratchpad.get(step):
                        summary_parts.append(f"- **{step.replace('_', ' ').title()}**: {self.scratchpad[step]}\n")
                    else:
                        summary_parts.append(f"- **{step.replace('_', ' ').title()}**: (Not yet defined)\n")
                summary_parts.append("\n")

                # 2. Main Findings from Recommendations (Simplified for now, could be more elaborate)
                #    This assumes recommendations were generated and stored or can be inferred.
                #    For a more robust summary, recommendation outputs could be stored in scratchpad.
                summary_parts.append("**Key Insights & Recommendations Overview:**\n")
                if st.session_state.get("vp_recommendation_fully_generated_once", False): # Check if recommendations were ever generated
                    summary_parts.append(
                        "Based on our discussion, key recommendations included validating your assumptions, "
                        "focusing on differentiation, crafting compelling use cases, and understanding your market context. "
                        "Specific research requests (if any) were also noted for further investigation.\n"
                    ) # This is a generic recap. Persona could make it more specific.
                else:
                    summary_parts.append("Recommendations were not fully generated in this session.\n")
                summary_parts.append("\n")

                # 3. Spirit of the Conversation (Persona's role)
                #    This part is highly dependent on the persona's capabilities.
                #    For now, a placeholder or a call to a persona method.
                spirit_of_conversation = self.persona.capture_spirit_of_value_prop_conversation(self.scratchpad)
                if spirit_of_conversation:
                     summary_parts.append(f"**Overall Focus & Direction:**\n{spirit_of_conversation}\n\n")
                else: # Fallback
                    summary_parts.append(
                        "**Overall Focus & Direction:**\n"
                        "The process aimed to systematically build out your value proposition, "
                        "encouraging reflection and clarity at each step. The goal is to create a strong foundation "
                        "for your venture.\n\n"
                    )
                
                summary_parts.append("This summary encapsulates our work. You can use this as a basis for further development and communication.")
                core_response = "".join(summary_parts)
                
                self.completed = True # Mark workflow as complete
                st.session_state["vp_summary_generated_once"] = True
            else: # Summary already generated, user might just be chatting
                core_response = "The value proposition development is complete. Here is your summary again:\n\n" + self.generate_summary() # regenerate for display
                self.completed = True # Ensure it stays completed


        # Construct final response
        if not final_response_str: # if not set by early return
            response_parts = []
            if preliminary_message:
                response_parts.append(preliminary_message)
            if core_response:
                response_parts.append(core_response.strip())
            
            final_response_str = " ".join(response_parts).strip()

        if final_response_str:
            # Add reflection prompt unless in summary phase and completed
            if not (self.current_phase == "summary" and self.completed):
                 return final_response_str + self.persona.get_reflection_prompt()
            return final_response_str
        
        # Fallback if no response generated (should be rare)
        return self.persona.get_prompt_for_empty_input(self.current_ideation_step or "current focus") + self.persona.get_reflection_prompt()


    def add_research_request(self, step: str, details: str = ""):
        """Adds a research request to the scratchpad, associated with an ideation step."""
        if "research_requests" not in self.scratchpad:
            self.scratchpad["research_requests"] = []
        self.scratchpad["research_requests"].append({"step": step, "details": details})
        st.write(f"Research request added for {step}: {details}") # For debugging

    def generate_summary(self) -> str:
        """
        Generates a comprehensive, paragraph-style summary of the value proposition workflow.
        This method is called when transitioning to or re-displaying the summary phase.
        Conforms to WorkflowBase.generate_summary.
        """
        summary_parts = [
            f"Value Proposition Summary (Finalized in Phase: {self.current_phase}):\n\n",
            "This captures the core elements, insights, and direction established for your value proposition:\n\n"
        ]

        # 1. Scratchpad Elements
        summary_parts.append("**I. Core Value Proposition Elements:**\n")
        for step in self.IDEATION_STEPS:
            content = self.scratchpad.get(step, "(Not defined)")
            summary_parts.append(f"   - **{step.replace('_', ' ').title()}**: {content}\n")
        summary_parts.append("\n")

        # 2. Main Findings from Recommendations (Simplified recap)
        summary_parts.append("**II. Key Recommendation Themes:**\n")
        if st.session_state.get("vp_recommendation_fully_generated_once", False):
            # This is a generic recap. A more sophisticated approach might store actual recommendation text.
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
        
        # 3. Spirit of the Conversation (Delegated to Persona)
        summary_parts.append("**III. Overall Spirit & Next Steps:**\n")
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
