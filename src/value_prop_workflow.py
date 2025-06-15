from src.coach_persona import BehaviorEngine

class ValuePropWorkflow:
    def __init__(self, context=None):
        self.context = context or {}
        self.behavior = BehaviorEngine()
        self.current_step = "problem"  # Initial step
        self.scratchpad = {
            "problem": "",
            "target_user": "",
            "solution": "",
            "benefit": "", # Changed from main_benefit
            "differentiator": "",
            "use_case": "", # Will store natural language description of use case(s)
            "research_requests": [] # List of strings or dicts
        }
        self.completed = False
        self.intake_complete = False  # Flag for the initial intake message

    def next_step(self):
        steps = ["problem", "target_user", "solution", "benefit", "differentiator", "use_case"] # Changed main_benefit to benefit
        try:
            current_idx = steps.index(self.current_step)
            if current_idx + 1 < len(steps):
                self.current_step = steps[current_idx + 1]
            else:
                self.completed = True
        except ValueError:
            self.completed = True # Should not happen if current_step is always valid

    def process_user_input(self, user_input: str):
        generated_response_parts = []
        user_input_stripped = user_input.strip()

        # 1. Handle intake-to-ideation transition message (once at the beginning)
        if self.current_step == "problem" and not self.intake_complete:
            generated_response_parts.append(
                "Thanks for sharing! I'll help you develop and vet your ideas now. "
                "I will continue to ask you questions, but you're welcome to ask me for ideas, analysis, or feedback at any point."
            )
            self.intake_complete = True

        # 2. Handle dedicated step introductions
        # Show intro if it's the differentiator step, benefit is filled, and differentiator in scratchpad is still empty.
        if self.current_step == "differentiator" and \
           self.scratchpad.get("benefit") and \
           not self.scratchpad.get("differentiator"):

            differentiator_intro_message = (
                "Let's define what makes your solution unique. "
                "This helps clarify your competitive advantage and will later help to position your idea effectively.\n"
                "What specific aspects set your solution apart from alternatives?"
            )
            if not generated_response_parts or differentiator_intro_message not in generated_response_parts[-1]:
                 generated_response_parts.append(differentiator_intro_message)

            if not user_input_stripped: # If user_input is empty after this intro, we are done for this turn.
                 return "\n\n".join(filter(None, generated_response_parts)).strip()

        # Show intro if it's the use_case step, differentiator is filled, and use_case in scratchpad is still empty.
        elif self.current_step == "use_case" and \
             self.scratchpad.get("differentiator") and \
             not self.scratchpad.get("use_case"):

            use_case_intro_message = (
                "Now let's think about specific use cases. "
                "How do you envision people using your solution in real-world scenarios?"
            )
            if not generated_response_parts or use_case_intro_message not in generated_response_parts[-1]:
                generated_response_parts.append(use_case_intro_message)

            if not user_input_stripped: # If user_input is empty after this intro, we are done for this turn.
                return "\n\n".join(filter(None, generated_response_parts)).strip()

        # 3. General stance handling and coaching
        stance = self.behavior.detect_user_stance(user_input_stripped, self.current_step)

        # Store user input if it's a "decided" stance.
        # Also, if it's a dedicated step (differentiator, use_case) and user provided input for it (and it's not yet in scratchpad).
        if stance == "decided":
            self.scratchpad[self.current_step] = user_input_stripped
        elif self.current_step == "differentiator" and \
             self.scratchpad.get("benefit") and \
             user_input_stripped and \
             not self.scratchpad.get("differentiator"):
            self.scratchpad["differentiator"] = user_input_stripped
            if stance != "decided": # If stance wasn't 'decided' but we captured differentiator, treat as 'decided'.
                stance = "decided"
        elif self.current_step == "use_case" and \
             self.scratchpad.get("differentiator") and \
             user_input_stripped and \
             not self.scratchpad.get("use_case"):
            self.scratchpad["use_case"] = user_input_stripped
            if stance != "decided": # If stance wasn't 'decided' but we captured use_case, treat as 'decided'.
                stance = "decided"

        if stance == "uncertain":
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, stance))
            generated_response_parts.append(self.behavior.offer_example(self.current_step))
            generated_response_parts.append(
                f"Could you try to define the {self.current_step} more clearly, or would you like to brainstorm some ideas together for it?"
            )
        elif stance == "open":
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, stance))
            generated_response_parts.append(self.behavior.offer_strategic_suggestion(self.current_step))
            generated_response_parts.append(
                f"What are your thoughts on that suggestion, or would you like to explore other angles for the {self.current_step}?"
            )
        elif stance == "interest":
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, stance))
            generated_response_parts.append(
                f"It sounds like you're making good progress on the {self.current_step}. "
                "Would you like to refine this further, or shall we consider how this connects to the next part of your value proposition?"
            )
        elif stance == "decided":
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, stance))
            generated_response_parts.append(
                self.behavior.coach_on_decision(self.current_step, user_input_stripped)
            )
        else:  # Fallback for other/unclear stances
            generated_response_parts.append(self.behavior.paraphrase_user_input(user_input_stripped, "neutral"))
            generated_response_parts.append(
                f"That's an interesting perspective on the {self.current_step}. "
                "Could you elaborate a bit more on your reasoning, or would you like to consider some alternative ways to approach this?"
            )

        return "\n\n".join(filter(None, generated_response_parts)).strip()

    def add_research_request(self, step: str, details: str = ""):
        self.scratchpad["research_requests"].append({"step": step, "details": details})

    def actionable_recommendations(self):
        recs = []
        for req in self.scratchpad.get("research_requests", []):
            # Ensuring natural language for recommendations
            if isinstance(req, dict):
                 recs.append(f"It's recommended to research the {req.get('step', 'relevant area')} further, focusing on: {req.get('details', 'specific aspects not yet defined')}.")
            elif isinstance(req, str):
                 recs.append(f"Further research is suggested for: {req}.")
            else:
                 recs.append("Additional research may be beneficial.")
        if not recs:
            return "" # Return empty string if no recommendations, to be handled by generate_summary
        return "\n".join(recs)

    def generate_summary(self):
        # Generates a structured summary string with a main paragraph, use cases, and recommendations.
        # This method now constructs the final user-facing summary directly.

        problem_desc = self.scratchpad.get('problem')
        target_user_desc = self.scratchpad.get('target_user')
        solution_desc = self.scratchpad.get('solution')
        benefit_desc = self.scratchpad.get('benefit') # Changed from main_benefit
        differentiator_desc = self.scratchpad.get('differentiator')
        use_case_desc = self.scratchpad.get('use_case')

        summary_parts = []

        # 1. Main Summary Paragraph
        # Only include elements if they are defined.
        # Using more natural phrasing.
        main_summary_elements = []
        if problem_desc:
            main_summary_elements.append(f"The core problem being addressed is {problem_desc}.")
        if target_user_desc:
            main_summary_elements.append(f"This primarily affects {target_user_desc}.")
        if solution_desc:
            main_summary_elements.append(f"The proposed solution involves {solution_desc}.")
        if benefit_desc:
            main_summary_elements.append(f"The key benefit this offers is {benefit_desc}.")
        if differentiator_desc:
            main_summary_elements.append(f"What sets this apart is {differentiator_desc}.")
        
        if main_summary_elements:
            summary_paragraph = " ".join(main_summary_elements)
            summary_parts.append(summary_paragraph)
        else:
            summary_parts.append("The value proposition is still under development.")

        # 2. Use Case Section
        if use_case_desc:
            # Ensure natural language, not bullets.
            # If use_case_desc might contain multiple points, they should already be in natural language.
            summary_parts.append(f"\n\n**Use Case(s):**\n{use_case_desc}")
        else:
            summary_parts.append("\n\n**Use Case(s):**\nNot yet defined.")


        # 3. Actionable Recommendations Section
        recommendations_text = self.actionable_recommendations()
        if recommendations_text:
            summary_parts.append(f"\n\n**Actionable Recommendations:**\n{recommendations_text}")
        
        return "".join(summary_parts).strip()

    def is_complete(self):
        return self.completed

    def get_step(self):
        return self.current_step