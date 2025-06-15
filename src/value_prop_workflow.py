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
            "main_benefit": "",
            "differentiator": "",
            "use_case": "",
            "research_requests": []
        }
        self.completed = False
        self.intake_complete = False  # Flag for the initial intake message

    def next_step(self):
        steps = ["problem", "target_user", "solution", "main_benefit", "differentiator", "use_case"]
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
        # Show intro if it's the differentiator step, main_benefit is filled, and differentiator in scratchpad is still empty.
        if self.current_step == "differentiator" and \
           self.scratchpad.get("main_benefit") and \
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
             self.scratchpad.get("main_benefit") and \
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
        for req in self.scratchpad["research_requests"]:
            recs.append(f"Suggested research regarding the {req['step']}: {req.get('details', 'TBD')}")
        if not recs:
            return "No additional research was requested."
        return "\n".join(recs)

    def generate_summary(self):
        # LLM Behavior Guideline:
        # Generate a concise summary of the value proposition.
        # Incorporate the problem, target user, solution, main benefit, differentiator, and use_case
        # using the information gathered from the scratchpad.
        # Paraphrase or summarize these elements in your own words, naturally and conversationally.
        # Do not directly quote the scratchpad values.

        # Constructing a context string for the LLM, not the final summary itself.
        # The LLM will use this context to generate the actual conversational summary.
        problem_desc = self.scratchpad.get('problem', 'not yet defined')
        target_user_desc = self.scratchpad.get('target_user', 'not yet defined')
        solution_desc = self.scratchpad.get('solution', 'not yet defined')
        benefit_desc = self.scratchpad.get('main_benefit', 'not yet defined')
        differentiator_desc = self.scratchpad.get('differentiator', 'not yet defined')
        use_case_desc = self.scratchpad.get('use_case', 'not yet defined')

        # Behavioral instruction for the LLM to generate a summary
        # The LLM should paraphrase the elements, not quote them
        instruction = (
            "Behavioral instruction: Generate a concise, conversational summary of the value proposition. "
            "Paraphrase the following elements in your own words: "
            f"Problem: {problem_desc}, "
            f"Target user: {target_user_desc}, "
            f"Solution: {solution_desc}, "
            f"Main benefit: {benefit_desc}, "
            f"Differentiator: {differentiator_desc}, "
            f"Use Case: {use_case_desc}. "
            "Do not quote these elements directly. "
        )
        return instruction

    def is_complete(self):
        return self.completed

    def get_step(self):
        return self.current_step